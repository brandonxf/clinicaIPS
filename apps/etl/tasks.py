import os
import uuid
from django.conf import settings
from .services import PipelineETL
from .analytics import calcular_analitica_dataset, recalcular_kpis_desde_db
from .models import ETLTask

TASK_ID_KEY = 'etl_task_id'


def _save_task(task_id, activo=True, fase='', mensaje='', detalle='', logs=None):
    ETLTask.objects.update_or_create(
        task_id=task_id,
        defaults={
            'activo': activo,
            'fase': fase,
            'mensaje': mensaje,
            'detalle': detalle,
            'logs': logs or [],
        }
    )


def ejecutar_pipeline(ruta_archivo, usuario_id=None):
    task_id = uuid.uuid4().hex

    def actualizar_log(fase, mensaje, detalle=''):
        log_history = []
        try:
            existing = ETLTask.objects.filter(task_id=task_id).first()
            if existing:
                log_history = list(existing.logs)
        except Exception:
            pass
        log_history.append({'fase': fase, 'mensaje': mensaje, 'detalle': detalle})
        _save_task(task_id, activo=True, fase=fase, mensaje=mensaje, detalle=detalle, logs=log_history)

    _save_task(task_id, activo=True, fase='INIT', mensaje='Iniciando pipeline...', detalle='')

    try:
        ext = os.path.splitext(ruta_archivo)[1].lower() or '.xlsx'
        saved_path = str(settings.BASE_DIR / 'datasets' / f'dataset_clinico{ext}')
        os.makedirs(os.path.dirname(saved_path), exist_ok=True)
        import shutil
        shutil.copy2(ruta_archivo, saved_path)
    except Exception:
        pass

    actualizar_log('EXTRACT', 'Extrayendo datos del archivo...', 'Leyendo CSV/Excel con Pandas')
    pipeline = PipelineETL(file_path=ruta_archivo, usuario_id=usuario_id)
    filas_extraidas = pipeline.extract()
    actualizar_log('EXTRACT', 'Extraccion completada', f'{filas_extraidas} registros leidos')

    actualizar_log('TRANSFORM', 'Transformando datos...', 'Limpieza, normalizacion y calculo de IMC')
    pipeline.transform()
    actualizar_log('TRANSFORM', 'Transformacion completada', 'Datos limpios y estructurados')

    actualizar_log('LOAD', 'Cargando datos a la base de datos...', 'Insercion masiva con transaccion atomica')
    exito, filas_cargadas = pipeline.load()
    actualizar_log('LOAD', 'Carga completada', f'{filas_cargadas} registros insertados')

    actualizar_log('ANALYTICS', 'Calculando KPIs del dashboard...', 'Estadisticas descriptivas y pacientes criticos')
    try:
        kpi = calcular_analitica_dataset(pipeline.df, reemplazar=True)
        if not kpi:
            raise ValueError('El dataset no produjo KPIs')
        actualizar_log('ANALYTICS', 'KPIs calculados correctamente', f'{kpi.total_registros} registros')
    except Exception as e:
        actualizar_log('ANALYTICS', 'Reintentando KPIs desde la base de datos...', str(e))
        try:
            kpi = recalcular_kpis_desde_db()
            if kpi:
                actualizar_log('ANALYTICS', 'KPIs recalculados desde BD', f'{kpi.total_registros} registros')
            else:
                actualizar_log('ANALYTICS', 'No se pudieron calcular KPIs', 'Sin pacientes en la base de datos')
        except Exception as e2:
            actualizar_log('ANALYTICS', 'Error definitivo calculando KPIs', str(e2))

    try:
        os.remove(ruta_archivo)
    except Exception:
        pass

    actualizar_log('ML', 'Entrenando modelo Random Forest con datos limpios...', 'Scikit-Learn pipeline en progreso')
    try:
        from apps.ml.services import entrenar_modelo
        modelo_obj, metricas = entrenar_modelo('random_forest')
        actualizar_log('ML', 'Modelo entrenado exitosamente',
                       f'Accuracy: {metricas["accuracy"]:.4f}, F1: {metricas["f1_score"]:.4f}')
    except Exception as e:
        actualizar_log('ML', 'Error en entrenamiento ML', str(e))

    actualizar_log('DONE', 'Pipeline ETL+ML finalizado', 'Proceso completo')
    _save_task(task_id, activo=False, fase='DONE', mensaje='Pipeline ETL+ML finalizado', detalle='Proceso completo')

    return {
        "status": "success",
        "registros_leidos": filas_extraidas,
        "registros_procesados": filas_cargadas,
    }
