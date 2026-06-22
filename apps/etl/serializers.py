from rest_framework import serializers
from .models import Paciente, HistorialETL, ETLTask, DashboardKPIs


class PacienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = '__all__'


class HistorialETLSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = HistorialETL
        fields = '__all__'


class ETLTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ETLTask
        fields = '__all__'


class DashboardKPIsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardKPIs
        fields = '__all__'
