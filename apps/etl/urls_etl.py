from django.urls import path
from .views import (ejecutar_etl_view, subir_dataset, historial_etl,
                    estadisticas_etl, exportar_dataset_csv,
                    estado_etl, reset_data)

urlpatterns = [
    path('run/', ejecutar_etl_view, name='etl_run'),
    path('upload/', subir_dataset, name='etl_upload'),
    path('status/', estado_etl, name='etl_status'),
    path('reset/', reset_data, name='etl_reset'),
    path('stats/', estadisticas_etl, name='etl_stats'),
    path('historial/', historial_etl, name='etl_historial'),
    path('exportar-csv/', exportar_dataset_csv, name='etl_exportar_csv'),

]
