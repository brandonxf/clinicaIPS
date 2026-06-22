import os
import time
from datetime import datetime
from django.db import transaction
from .models import Paciente, HistorialETL
from .clasificador_sexo import clasificar_sexo_por_nombre


class PipelineETL:
    def __init__(self, file_path, usuario_id=None):
        self.file_path = file_path
        from apps.authentication.models import Usuario
        self.usuario = Usuario.objects.filter(id=usuario_id).first() if usuario_id else None
        self.start_time = None
        self.df = None
        self.total_extraidos = 0

    def extract(self):
        import pandas as pd
        self.start_time = time.time()
        nombre = self.file_path if isinstance(self.file_path, str) else self.file_path.name
        es_excel = nombre.lower().endswith(('.xlsx', '.xls'))

        if isinstance(self.file_path, str):
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"El archivo en la ruta {self.file_path} no existe.")
            self.df = pd.read_excel(self.file_path) if es_excel else pd.read_csv(self.file_path)
        else:
            self.df = pd.read_excel(self.file_path) if es_excel else pd.read_csv(self.file_path)

        self.total_extraidos = len(self.df)
        return self.total_extraidos

    def transform(self):
        import pandas as pd
        if self.df is None:
            raise ValueError("Primero debes ejecutar el método extract().")

        self.df.drop_duplicates(subset=['id_paciente'], keep='first', inplace=True)

        columnas_numericas = ['peso', 'altura', 'presion_sistolica', 'presion_diastolica',
                              'frecuencia_cardiaca', 'glucosa', 'colesterol',
                              'saturacion_oxigeno', 'temperatura']
        col_rename = {}
        for col_orig in ['presión_sistólica', 'presión_diastólica', 'saturación_oxígeno',
                         'actividad_física', 'diagnóstico_preliminar', 'IMC']:
            if col_orig in self.df.columns:
                col_rename[col_orig] = {
                    'presión_sistólica': 'presion_sistolica',
                    'presión_diastólica': 'presion_diastolica',
                    'saturación_oxígeno': 'saturacion_oxigeno',
                    'actividad_física': 'actividad_fisica',
                    'diagnóstico_preliminar': 'diagnostico_preliminar',
                    'IMC': 'imc',
                }[col_orig]
        self.df = self.df.rename(columns=col_rename)

        for col in columnas_numericas:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                mediana = self.df[col].median()
                if pd.notna(mediana):
                    self.df[col] = self.df[col].fillna(mediana)

        if 'sexo' in self.df.columns:
            self.df['sexo'] = self.df['sexo'].astype(str).str.strip().str.upper()
            mapeo_sexo = {'M': 'Masculino', 'F': 'Femenino', 'MASCULINO': 'Masculino', 'FEMENINO': 'Femenino'}
            self.df['sexo'] = self.df['sexo'].map(mapeo_sexo).fillna('No Definido')

        if 'nombres' in self.df.columns:
            for idx in self.df.index:
                nombre = self.df.at[idx, 'nombres']
                sexo_actual = self.df.at[idx, 'sexo']
                sexo_correcto = clasificar_sexo_por_nombre(nombre)
                if sexo_correcto and sexo_correcto != sexo_actual:
                    self.df.at[idx, 'sexo'] = sexo_correcto

        if 'edad' in self.df.columns:
            mapeo_edades_texto = {'treinta': '30', 'cuarenta': '40', 'cincuenta': '50', 'Treinta': '30'}
            self.df['edad'] = self.df['edad'].astype(str).replace(mapeo_edades_texto)
            self.df['edad'] = pd.to_numeric(self.df['edad'], errors='coerce')
            edad_media = int(self.df['edad'].mean()) if not self.df['edad'].isna().all() else 40
            self.df['edad'] = self.df['edad'].fillna(edad_media).astype(int)

        if 'diagnostico_preliminar' in self.df.columns:
            self.df['diagnostico_preliminar'] = self.df['diagnostico_preliminar'].astype(str).str.strip()
            mapeo_diagnosticos = {
                'hipertencion': 'Hipertension', 'hipertensíon': 'Hipertension',
                'hipertension': 'Hipertension',
                'diabetes tipo 2': 'Diabetes Tipo 2', 'diabetes': 'Diabetes Tipo 2',
                'diabetis': 'Diabetes Tipo 2',
                'obesidad': 'Obesidad', 'cardiopatía': 'Cardiopatia',
                'cardiopatia': 'Cardiopatia',
                'Paciente sano': 'Sano', 'paciente sano': 'Sano',
            }
            self.df['diagnostico_preliminar'] = self.df['diagnostico_preliminar'].replace(mapeo_diagnosticos)
            self.df['diagnostico_preliminar'] = self.df['diagnostico_preliminar'].str.title()

        if 'peso' in self.df.columns and 'altura' in self.df.columns:
            mask = self.df['peso'].notna() & self.df['altura'].notna() & (self.df['altura'] > 0)
            self.df.loc[mask, 'imc'] = (self.df.loc[mask, 'peso'] / (self.df.loc[mask, 'altura'] ** 2)).round(2)
            self.df['clasificacion_imc'] = 'No evaluado'
            self.df.loc[self.df['imc'] < 18.5, 'clasificacion_imc'] = 'Bajo peso'
            self.df.loc[(self.df['imc'] >= 18.5) & (self.df['imc'] < 25), 'clasificacion_imc'] = 'Normal'
            self.df.loc[(self.df['imc'] >= 25) & (self.df['imc'] < 30), 'clasificacion_imc'] = 'Sobrepeso'
            self.df.loc[self.df['imc'] >= 30, 'clasificacion_imc'] = 'Obesidad'

        columnas_bool = ['antecedentes_familiares', 'fumador', 'consumo_alcohol']
        for col in columnas_bool:
            if col in self.df.columns:
                self.df[col] = self.df[col].replace({'True': True, 'False': False, 1: True, 0: False})
                self.df[col] = self.df[col].astype(bool)

        if 'fecha_consulta' in self.df.columns:
            self.df['fecha_consulta'] = pd.to_datetime(self.df['fecha_consulta'], errors='coerce')
            self.df['fecha_consulta'] = self.df['fecha_consulta'].fillna(pd.Timestamp(datetime.now()))

        if 'actividad_fisica' in self.df.columns:
            self.df['actividad_fisica'] = self.df['actividad_fisica'].astype(str).str.strip().str.lower()
            mapa_act = {'sedentario': 'Sedentario', 'sedentaria': 'Sedentario',
                        'baja': 'Baja', 'bajo': 'Baja',
                        'media': 'Media', 'moderada': 'Media',
                        'alta': 'Alta', 'alto': 'Alta'}
            self.df['actividad_fisica'] = self.df['actividad_fisica'].map(mapa_act).fillna('Sedentario')

        self._clasificar_riesgo()

        self.df['es_critico'] = (
            (self.df.get('presion_sistolica', pd.Series(dtype=float)) > 180) |
            (self.df.get('glucosa', pd.Series(dtype=float)) > 300) |
            (self.df.get('saturacion_oxigeno', pd.Series(dtype=float)) < 85)
        ).fillna(False)

        return len(self.df)

    def _clasificar_riesgo(self):
        if 'riesgo_enfermedad' not in self.df.columns:
            self.df['riesgo_enfermedad'] = 'bajo'
        else:
            self.df['riesgo_enfermedad'] = self.df['riesgo_enfermedad'].astype(str).str.strip().str.lower()
            mapa_riesgo = {'bajo': 'bajo', 'medio': 'medio', 'alto': 'alto',
                           'critico': 'critico', 'crítico': 'critico',
                           'bajo ': 'bajo', ' medio': 'medio'}
            self.df['riesgo_enfermedad'] = self.df['riesgo_enfermedad'].map(mapa_riesgo).fillna('bajo')

    def load(self):
        import pandas as pd
        if self.df is None:
            raise ValueError("No hay datos transformados listos para cargar.")

        inicio = self.start_time if self.start_time is not None else time.time()

        Paciente.objects.all().delete()

        registros_a_insertar = []
        for _, row in self.df.iterrows():
            paciente = Paciente(
                id_paciente=int(row['id_paciente']),
                nombres=str(row.get('nombres', '')).strip().title(),
                apellidos=str(row.get('apellidos', '')).strip().title(),
                edad=int(row['edad']),
                sexo=str(row.get('sexo', 'Otro')).strip(),
                peso=float(row['peso']) if pd.notna(row.get('peso')) else None,
                altura=float(row['altura']) if pd.notna(row.get('altura')) else None,
                imc=float(row['imc']) if pd.notna(row.get('imc')) else None,
                clasificacion_imc=row.get('clasificacion_imc'),
                presion_sistolica=float(row['presion_sistolica']) if pd.notna(row.get('presion_sistolica')) else None,
                presion_diastolica=float(row['presion_diastolica']) if pd.notna(row.get('presion_diastolica')) else None,
                frecuencia_cardiaca=float(row['frecuencia_cardiaca']) if pd.notna(row.get('frecuencia_cardiaca')) else None,
                glucosa=float(row['glucosa']) if pd.notna(row.get('glucosa')) else None,
                colesterol=float(row['colesterol']) if pd.notna(row.get('colesterol')) else None,
                saturacion_oxigeno=float(row['saturacion_oxigeno']) if pd.notna(row.get('saturacion_oxigeno')) else None,
                temperatura=float(row['temperatura']) if pd.notna(row.get('temperatura')) else None,
                antecedentes_familiares=bool(row.get('antecedentes_familiares', False)),
                fumador=bool(row.get('fumador', False)),
                consumo_alcohol=bool(row.get('consumo_alcohol', False)),
                actividad_fisica=row.get('actividad_fisica', 'Sedentario'),
                diagnostico_preliminar=row.get('diagnostico_preliminar'),
                riesgo_enfermedad=row.get('riesgo_enfermedad', 'bajo'),
                fecha_consulta=row['fecha_consulta'].date() if pd.notna(row.get('fecha_consulta')) else None,
                es_critico=bool(row.get('es_critico', False)),
            )
            registros_a_insertar.append(paciente)

        try:
            with transaction.atomic():
                Paciente.objects.bulk_create(registros_a_insertar, ignore_conflicts=True)

            tiempo_final = time.time() - inicio

            HistorialETL.objects.create(
                usuario=self.usuario,
                archivo_origen=str(self.file_path) if isinstance(self.file_path, str) else self.file_path.name,
                registros_entrada=self.total_extraidos,
                registros_limpios=len(registros_a_insertar),
                duplicados_eliminados=self.total_extraidos - len(registros_a_insertar),
                tiempo_ejecucion_seg=round(tiempo_final, 3),
                estado='completado',
            )
            return True, len(registros_a_insertar)

        except Exception as e:
            tiempo_final = time.time() - inicio
            HistorialETL.objects.create(
                usuario=self.usuario,
                registros_entrada=self.total_extraidos,
                registros_limpios=0,
                tiempo_ejecucion_seg=round(tiempo_final, 3),
                estado='error',
                errores=str(e),
            )
            raise e
