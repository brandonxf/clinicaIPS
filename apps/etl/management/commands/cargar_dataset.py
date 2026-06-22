"""
Comando Django: python manage.py cargar_dataset
Carga un dataset desde una ruta local y ejecuta el pipeline ETL completo.
"""
import os
from django.core.management.base import BaseCommand, CommandError
from apps.etl.services import PipelineETL

class Command(BaseCommand):
    help = 'Carga un dataset desde archivo y ejecuta el proceso ETL'

    def add_arguments(self, parser):
        parser.add_argument('--archivo', type=str, required=True,
                            help='Ruta al archivo Excel/CSV del dataset')

    def handle(self, *args, **options):
        archivo = options['archivo']
        if not os.path.exists(archivo):
            raise CommandError(f'El archivo no existe: {archivo}')

        self.stdout.write(self.style.WARNING('\n=== CARGANDO DATASET ===\n'))

        try:
            pipeline = PipelineETL(file_path=archivo)
            leidos = pipeline.extract()
            self.stdout.write(self.style.SUCCESS(f'Extraidos {leidos} registros.'))
            transformados = pipeline.transform()
            self.stdout.write(self.style.SUCCESS(f'Transformados {transformados} registros.'))
            exito, cargados = pipeline.load()
            self.stdout.write(self.style.SUCCESS(f'Cargados {cargados} registros.\n'))
        except Exception as e:
            raise CommandError(f'Error en ETL: {e}')
