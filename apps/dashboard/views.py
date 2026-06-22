from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from apps.analytics.services import (
    obtener_kpis, obtener_estadisticas_descriptivas,
    segmentacion_por_edad, distribucion_imc,
    segmentacion_por_diagnostico, tendencia_consultas_mensual,
    matriz_calor_edad_riesgo,
)
from apps.etl.models import HistorialETL, Paciente, DashboardKPIs
from apps.ml.models import ModeloML


@extend_schema(
    tags=['dashboard'],
    summary='KPIs del dashboard principal',
    description='Retorna KPIs agregados, ultimo ETL, modelo activo y datos para todas las graficas del dashboard.',
    responses={200: {'type': 'object'}},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_kpis(request):
    kpis = obtener_kpis()
    stats = obtener_estadisticas_descriptivas()
    snapshot = DashboardKPIs.objects.last()
    ultimo_etl = HistorialETL.objects.first()
    modelo_activo = ModeloML.objects.filter(activo=True).first()

    ultimas_consultas = list(
        Paciente.objects.order_by('-fecha_consulta', '-id')[:10].values(
            'id', 'nombres', 'apellidos', 'edad', 'sexo',
            'diagnostico_preliminar', 'fecha_consulta', 'riesgo_enfermedad',
            'es_critico',
        )
    )

    return Response({
        'kpis': kpis,
        'snapshot': {
            'fecha': snapshot.fecha_calculo.isoformat() if snapshot and snapshot.fecha_calculo else None,
            'total_pacientes': snapshot.total_registros if snapshot else kpis.get('total_pacientes'),
            'pacientes_criticos': snapshot.pacientes_criticos if snapshot else kpis.get('pacientes_criticos'),
            'promedio_edad': float(snapshot.edad_media) if snapshot and snapshot.edad_media is not None else None,
        } if snapshot else None,
        'ultimo_etl': {
            'fecha': ultimo_etl.fecha_ejecucion if ultimo_etl else None,
            'estado': ultimo_etl.estado if ultimo_etl else None,
            'registros': ultimo_etl.registros_limpios if ultimo_etl else 0,
        },
        'modelo_activo': {
            'nombre': modelo_activo.nombre if modelo_activo else None,
            'accuracy': modelo_activo.accuracy if modelo_activo else None,
        },
        'graficas': {
            'distribucion_riesgo': kpis.get('distribucion_riesgo', {}),
            'segmentacion_edad': segmentacion_por_edad(),
            'distribucion_imc': distribucion_imc(),
            'top_diagnosticos': segmentacion_por_diagnostico(),
            'tendencia_consultas': tendencia_consultas_mensual(),
            'heatmap_edad_riesgo': matriz_calor_edad_riesgo(),
        },
        'estadisticas_descriptivas': stats,
        'ultimas_consultas': ultimas_consultas,
    })
