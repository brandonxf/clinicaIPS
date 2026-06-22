import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.etl.services import PipelineETL


class Command(BaseCommand):
    help = 'Ejecuta de forma secuencial el pipeline ETL para procesar el archivo Excel clinico'

    def add_arguments(self, parser):
        parser.add_argument('--archivo', type=str, default=None,
                            help='Ruta al archivo Excel/CSV del dataset')

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n=== INICIANDO PIPELINE ETL ===\n'))

        archivo = options.get('archivo')
        if archivo and os.path.exists(archivo):
            file_path = archivo
        else:
            base_dir = settings.BASE_DIR
            file_path = os.path.join(base_dir, 'datasets', 'dataset_clinico.xlsx')
            if not os.path.exists(file_path):
                file_path_csv = os.path.join(base_dir, 'datasets', 'dataset_clinico.csv')
                if os.path.exists(file_path_csv):
                    file_path = file_path_csv

        self.stdout.write(f"Buscando archivo en: {file_path}")

        if not os.path.exists(file_path):
            raise CommandError(
                f'\n[ERROR] No se pudo iniciar el proceso. El archivo NO existe en la ruta:\n{file_path}\n'
                f'Usa --archivo /ruta/al/dataset.xlsx o coloca el archivo en datasets/'
            )

        try:
            pipeline = PipelineETL(file_path=file_path)

            self.stdout.write(self.style.MIGRATE_LABEL('1. Ejecutando capa de Extraccion (Extract)...'))
            leidos = pipeline.extract()
            self.stdout.write(self.style.SUCCESS(f'   Exito: Se leyeron {leidos} filas originales.'))

            self.stdout.write(self.style.MIGRATE_LABEL('2. Ejecutando capa de Transformacion (Transform)...'))
            transformados = pipeline.transform()
            self.stdout.write(self.style.SUCCESS(f'   Exito: Quedaron {transformados} registros tras limpieza.'))

            self.stdout.write(self.style.MIGRATE_LABEL('3. Ejecutando capa de Carga (Load)...'))
            exito, cargados = pipeline.load()

            self.stdout.write(self.style.SUCCESS('\nPROCESO FINALIZADO CON EXITO!'))
            self.stdout.write(self.style.SUCCESS(f'Se insertaron {cargados} registros limpios.\n'))

        except Exception as e:
            raise CommandError(f'\n[ERROR] El pipeline fallo debido a: {str(e)}')
