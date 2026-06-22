import os, csv, uuid, threading
from django.conf import settings
from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.authentication.permissions import EsAnalistaOAdministrador, EsMedicoOAdministrador
from rest_framework.filters import SearchFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Paciente, HistorialETL, ETLTask, DashboardKPIs
from .serializers import PacienteSerializer, HistorialETLSerializer
from .services import PipelineETL
from .analytics import recalcular_kpis_desde_db
from .tasks import ejecutar_pipeline as tarea_ejecutar_pipeline


class PacienteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            from apps.authentication.permissions import EsMedicoOAdministrador
            return [IsAuthenticated(), EsMedicoOAdministrador()]
        return [IsAuthenticated(), EsAnalistaOAdministrador()]
    search_fields = ['nombres', 'apellidos', 'id_paciente']

    @extend_schema(
        tags=['pacientes'],
        parameters=[
            OpenApiParameter('search', OpenApiTypes.STR,
                             description='Buscar por nombres, apellidos o ID de paciente'),
            OpenApiParameter('riesgo', OpenApiTypes.STR,
                             description='Filtrar por nivel de riesgo: bajo, medio, alto, critico'),
            OpenApiParameter('sexo', OpenApiTypes.STR,
                             description='Filtrar por sexo: Masculino, Femenino'),
            OpenApiParameter('critico', OpenApiTypes.STR,
                             description='Solo pacientes criticos: true'),
        ],
        summary='Listar pacientes',
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        riesgo  = self.request.query_params.get('riesgo')
        critico = self.request.query_params.get('critico')
        sexo    = self.request.query_params.get('sexo')
        if riesgo:           qs = qs.filter(riesgo_enfermedad=riesgo)
        if critico == 'true': qs = qs.filter(es_critico=True)
        if sexo:             qs = qs.filter(sexo=sexo)
        return qs


@extend_schema(
    tags=['etl'],
    summary='Ejecutar proceso ETL',
    description='Ejecuta Extract -> Transform -> Load sobre el dataset clinico almacenado en el servidor.',
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, EsAnalistaOAdministrador])
def ejecutar_etl_view(request):
    dataset_dir = settings.BASE_DIR / 'datasets'
    filepath = str(dataset_dir / 'dataset_clinico.xlsx')
    if not os.path.exists(filepath):
        filepath = str(dataset_dir / 'dataset_clinico.csv')
    if not os.path.exists(filepath):
        upload_dir = dataset_dir / 'temp_uploads'
        if os.path.isdir(upload_dir):
            archivos = sorted(os.listdir(upload_dir), reverse=True)
            for f in archivos:
                candidate = str(upload_dir / f)
                if candidate.endswith(('.xlsx', '.xls', '.csv')):
                    filepath = candidate
                    break
    if not os.path.exists(filepath):
        return Response(
            {'error': 'No hay dataset disponible. Sube un archivo usando el panel ETL.'},
            status=status.HTTP_404_NOT_FOUND
        )
    folder = os.path.dirname(filepath)
    historial = PipelineETL(filepath, usuario_id=request.user.id)
    historial.extract()
    historial.transform()
    historial.load()
    last = HistorialETL.objects.order_by('-id').first()
    return Response(HistorialETLSerializer(last).data)


@extend_schema(
    tags=['etl'],
    summary='Subir dataset y ejecutar ETL (asincrono)',
    description='Sube un archivo CSV o Excel. El proceso ETL se ejecuta en segundo plano.',
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, EsAnalistaOAdministrador])
@parser_classes([MultiPartParser])
def subir_dataset(request):
    try:
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({'error': 'No se envio archivo'}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in ['.csv', '.xlsx', '.xls']:
            return Response(
                {'error': 'Formato no soportado. Use CSV o Excel (.csv, .xlsx, .xls)'},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            )

        upload_dir = os.path.join(settings.DATASETS_DIR, 'temp_uploads')
        os.makedirs(upload_dir, exist_ok=True)
        nombre_unico = f"{uuid.uuid4().hex}{ext}"
        ruta_guardado = os.path.join(upload_dir, nombre_unico)

        with open(ruta_guardado, 'wb+') as destino:
            for chunk in archivo.chunks():
                destino.write(chunk)

        usuario_id = request.user.id if request.user.is_authenticated else None

        thread = threading.Thread(
            target=tarea_ejecutar_pipeline,
            args=(ruta_guardado,),
            kwargs={'usuario_id': usuario_id},
            daemon=True
        )
        thread.start()

        return Response({
            "status": "accepted",
            "message": "El archivo se ha recibido correctamente y se esta procesando en segundo plano."
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        return Response({
            "status": "error",
            "message": f"Ocurrio un error al recibir el archivo: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['etl'], summary='Estado de ejecucion ETL en tiempo real')
@api_view(['GET'])
@permission_classes([IsAuthenticated, EsAnalistaOAdministrador])
def estado_etl(request):
    task = ETLTask.objects.filter(activo=True).order_by('-created_at').first()
    if not task:
        task = ETLTask.objects.order_by('-created_at').first()
    if not task:
        return Response({"activo": False, "logs": []}, status=status.HTTP_200_OK)

    return Response({
        "activo": task.activo,
        "fase": task.fase,
        "mensaje": task.mensaje,
        "detalle": task.detalle,
        "logs": task.logs,
    }, status=status.HTTP_200_OK)


@extend_schema(tags=['etl'], summary='Restablecer datos (eliminar pacientes, historial ETL y KPIs)')
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, EsAnalistaOAdministrador])
def reset_data(request):
    try:
        pacientes_borrados = Paciente.objects.count()
        Paciente.objects.all().delete()
        HistorialETL.objects.all().delete()
        DashboardKPIs.objects.all().delete()
        return Response({
            "status": "success",
            "message": f"Datos restablecidos. {pacientes_borrados} registros eliminados."
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "status": "error",
            "message": f"Error al restablecer datos: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['etl'], summary='Estadisticas agregadas del ETL')
@api_view(['GET'])
@permission_classes([IsAuthenticated, EsAnalistaOAdministrador])
def estadisticas_etl(request):
    from django.db.models import Sum, Avg, Count
    stats = HistorialETL.objects.aggregate(
        total_ejecuciones=Count('id'),
        total_entrada=Sum('registros_entrada'),
        total_limpios=Sum('registros_limpios'),
        total_duplicados=Sum('duplicados_eliminados'),
        total_nulos=Sum('nulos_tratados'),
        promedio_tiempo=Avg('tiempo_ejecucion_seg'),
    )
    for k, v in stats.items():
        if v is None:
            stats[k] = 0
        elif isinstance(v, float):
            stats[k] = round(v, 2)
    return Response(stats)


@extend_schema(
    tags=['etl'],
    summary='Historial de ejecuciones ETL',
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, EsAnalistaOAdministrador])
def historial_etl(request):
    registros = HistorialETL.objects.all()[:20]
    return Response(HistorialETLSerializer(registros, many=True).data)


@extend_schema(
    tags=['etl'],
    summary='Exportar dataset limpio como CSV',
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, EsAnalistaOAdministrador])
def exportar_dataset_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="dataset_limpio.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    campos = ['id_paciente', 'nombres', 'apellidos', 'edad', 'sexo', 'peso', 'altura',
              'imc', 'clasificacion_imc', 'presion_sistolica', 'presion_diastolica',
              'frecuencia_cardiaca', 'glucosa', 'colesterol', 'saturacion_oxigeno',
              'temperatura', 'antecedentes_familiares', 'fumador', 'consumo_alcohol',
              'actividad_fisica', 'diagnostico_preliminar', 'riesgo_enfermedad',
              'es_critico', 'fecha_consulta']
    writer.writerow(campos)
    for p in Paciente.objects.all().iterator():
        writer.writerow([getattr(p, c, '') for c in campos])
    return response



