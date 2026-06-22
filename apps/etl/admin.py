from django.contrib import admin
from .models import Paciente, HistorialETL, ETLTask, DashboardKPIs

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['id_paciente', 'nombres', 'apellidos', 'edad', 'sexo', 
                    'riesgo_enfermedad', 'es_critico', 'fecha_consulta']
    list_filter = ['riesgo_enfermedad', 'es_critico', 'sexo', 'clasificacion_imc']
    search_fields = ['nombres', 'apellidos', 'diagnostico_preliminar']

@admin.register(HistorialETL)
class HistorialETLAdmin(admin.ModelAdmin):
    list_display = ['fecha_ejecucion', 'usuario', 'registros_entrada', 
                    'registros_limpios', 'estado', 'tiempo_ejecucion_seg']
    list_filter = ['estado']
    readonly_fields = ['log_detalle', 'errores']

@admin.register(ETLTask)
class ETLTaskAdmin(admin.ModelAdmin):
    list_display = ['task_id', 'activo', 'fase', 'created_at']
    list_filter = ['activo', 'fase']

@admin.register(DashboardKPIs)
class DashboardKPIsAdmin(admin.ModelAdmin):
    list_display = ['fecha_calculo', 'total_registros', 'pacientes_criticos', 'riesgo_promedio']
