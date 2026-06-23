"""
Genera el Manual de Usuario de HealthAnalytics IPS en PDF
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, KeepTogether
)
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, Frame
from reportlab.platypus.frames import Frame as RLFrame

OUTPUT = "/home/siriloooo/Desktop/clinica/clinicaIPS/MANUAL_USUARIO.pdf"

# ─── Color palette ──────────────────────────────────────────────────────────
TEAL        = HexColor("#14b8a6")
TEAL_DARK   = HexColor("#0d9488")
TEAL_BRIGHT = HexColor("#10e5cc")
PURPLE      = HexColor("#8b5cf6")
ORANGE      = HexColor("#f97316")
DARK        = HexColor("#1f2937")
TEXT        = HexColor("#111827")
TEXT_MUTED  = HexColor("#6b7280")
LIGHT_BG    = HexColor("#f9fafb")
SIDEBAR_BG  = HexColor("#080e1c")
SUCCESS     = HexColor("#10b981")
DANGER      = HexColor("#ef4444")
BORDER      = HexColor("#e5e7eb")
WHITE       = white

# ─── Styles ─────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    'CoverTitle', fontName='Helvetica-Bold', fontSize=28,
    textColor=WHITE, alignment=TA_CENTER, leading=34,
    spaceAfter=6))
styles.add(ParagraphStyle(
    'CoverSubtitle', fontName='Helvetica', fontSize=14,
    textColor=HexColor("#cbd5e1"), alignment=TA_CENTER, leading=20,
    spaceAfter=4))
styles.add(ParagraphStyle(
    'CoverFooter', fontName='Helvetica', fontSize=10,
    textColor=HexColor("#94a3b8"), alignment=TA_CENTER, leading=14))
styles.add(ParagraphStyle(
    'SectionTitle', fontName='Helvetica-Bold', fontSize=18,
    textColor=TEAL_DARK, leading=22, spaceBefore=20, spaceAfter=12))
styles.add(ParagraphStyle(
    'SubSection', fontName='Helvetica-Bold', fontSize=13,
    textColor=DARK, leading=16, spaceBefore=14, spaceAfter=6))
styles.add(ParagraphStyle(
    'BodyText2', fontName='Helvetica', fontSize=10,
    textColor=TEXT, leading=14, alignment=TA_JUSTIFY, spaceAfter=6))
styles.add(ParagraphStyle(
    'BulletCustom', fontName='Helvetica', fontSize=10,
    textColor=TEXT, leading=14, leftIndent=20, spaceAfter=3,
    bulletIndent=8, bulletFontSize=10))
styles.add(ParagraphStyle(
    'NoteTitle', fontName='Helvetica-Bold', fontSize=10,
    textColor=TEAL_DARK, leading=14, spaceBefore=6, spaceAfter=2))
styles.add(ParagraphStyle(
    'TableCell', fontName='Helvetica', fontSize=9,
    textColor=TEXT, leading=12))
styles.add(ParagraphStyle(
    'TableHeader', fontName='Helvetica-Bold', fontSize=9,
    textColor=WHITE, leading=12, alignment=TA_CENTER))
styles.add(ParagraphStyle(
    'Caption', fontName='Helvetica-Oblique', fontSize=8,
    textColor=TEXT_MUTED, alignment=TA_CENTER, spaceAfter=10, leading=10))
styles.add(ParagraphStyle(
    'TOCEntry', fontName='Helvetica', fontSize=11,
    textColor=TEXT, leading=18, leftIndent=10))
styles.add(ParagraphStyle(
    'TOCSection', fontName='Helvetica-Bold', fontSize=11,
    textColor=TEAL_DARK, leading=20, leftIndent=0))

# ─── Page number callback ───────────────────────────────────────────────────
def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawCentredString(letter[0]/2, 0.5*inch,
        f"HealthAnalytics IPS — Manual de Usuario — Pág. {doc.page}")
    # Header line
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(0.75*inch, letter[1]-0.6*inch, letter[0]-0.75*inch, letter[1]-0.6*inch)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(0.75*inch, letter[1]-0.55*inch, "HealthAnalytics IPS v1.0")
    canvas.drawRightString(letter[0]-0.75*inch, letter[1]-0.55*inch, "Confidencial")
    canvas.restoreState()

def cover_page(canvas, doc):
    canvas.saveState()
    # Full page gradient background (simulated with rectangles)
    bg = canvas
    bg.setFillColor(SIDEBAR_BG)
    bg.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
    # Teal accent line
    bg.setFillColor(TEAL_BRIGHT)
    bg.rect(0, letter[1]*0.45, letter[0], 3, fill=1, stroke=0)
    bg.restoreState()

def cover_page_after(canvas, doc):
    pass

# ─── Helper functions ───────────────────────────────────────────────────────
def section(title):
    return Paragraph(title, styles['SectionTitle'])

def sub(title):
    return Paragraph(title, styles['SubSection'])

def body(text):
    return Paragraph(text, styles['BodyText2'])

def bullet(text):
    return Paragraph(f"• {text}", styles['Bullet'])

def spacer(h=6):
    return Spacer(1, h)

def caption(text):
    return Paragraph(text, styles['Caption'])

def note_box(title, text):
    data = [[
        Paragraph(f"<b>{title}</b><br/>{text}",
                  ParagraphStyle('NoteBody', fontName='Helvetica', fontSize=9,
                                 textColor=TEXT, leading=13))
    ]]
    t = Table(data, colWidths=[6.2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor("#f0fdfa")),
        ('BOX', (0,0), (-1,-1), 1, TEAL),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    return t

def make_table(headers, rows, col_widths=None):
    data = [[Paragraph(h, styles['TableHeader']) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), styles['TableCell']) for c in row])
    if not col_widths:
        col_widths = [6.5*inch / len(headers)] * len(headers)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0,0), (-1,0), TEAL),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,1), (-1,-1), 5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
    ]
    # Alternate row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0,i), (-1,i), HexColor("#f8fafc")))
        else:
            style_cmds.append(('BACKGROUND', (0,i), (-1,i), WHITE))
    t.setStyle(TableStyle(style_cmds))
    return t

def screenshot(path, width=5.5*inch):
    if os.path.exists(path):
        img = Image(path, width=width, height=width*0.62)
        return img
    return None

# ─── Build document ─────────────────────────────────────────────────────────
doc = BaseDocTemplate(
    OUTPUT, pagesize=letter,
    leftMargin=0.75*inch, rightMargin=0.75*inch,
    topMargin=0.8*inch, bottomMargin=0.8*inch,
)

# Frame for normal pages
frame_normal = RLFrame(
    0.75*inch, 0.8*inch, letter[0]-1.5*inch, letter[1]-1.6*inch,
    id='normal')
frame_cover = RLFrame(
    0, 0, letter[0], letter[1],
    id='cover')

doc.addPageTemplates([
    PageTemplate(id='Cover', frames=[frame_cover],
                 onPage=cover_page, onPageEnd=cover_page_after),
    PageTemplate(id='Normal', frames=[frame_normal],
                 onPage=add_page_number),
])

from reportlab.platypus.doctemplate import NextPageTemplate

story = []

# ═══════════════════════════════════════════════════════════════════════════
# PORTADA (uses Cover template)
# ═══════════════════════════════════════════════════════════════════════════
story.append(NextPageTemplate('Cover'))
story.append(Spacer(1, 2.5*inch))
story.append(Paragraph("HealthAnalytics IPS", styles['CoverTitle']))
story.append(Paragraph("MANUAL DE USUARIO", styles['CoverTitle']))
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph("Plataforma Inteligente de Analítica Clínica", styles['CoverSubtitle']))
story.append(Paragraph(f"Versión 1.0 — {datetime.now().strftime('%B %Y')}", styles['CoverSubtitle']))
story.append(Spacer(1, 1.5*inch))
story.append(Paragraph("Documento Confidencial", styles['CoverFooter']))
story.append(Paragraph("HealthAnalytics IPS © Todos los derechos reservados", styles['CoverFooter']))

story.append(NextPageTemplate('Normal'))
story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════
# TABLA DE CONTENIDO
# ═══════════════════════════════════════════════════════════════════════════
story.append(section("Tabla de Contenido"))
story.append(spacer(10))

toc_items = [
    ("1.", "Introducción"),
    ("2.", "Acceso al Sistema"),
    ("3.", "Dashboard — Panel Principal"),
    ("4.", "Gestión de Pacientes"),
    ("5.", "Módulo ETL — Carga de Datos"),
    ("6.", "Machine Learning"),
    ("7.", "Exportación de Reportes"),
    ("8.", "Gestión de Usuarios"),
    ("9.", "Roles y Permisos"),
]

for num, title in toc_items:
    story.append(Paragraph(f"<b>{num}</b>&nbsp;&nbsp;{title}", styles['TOCEntry']))
    story.append(Spacer(1, 2))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════
# 1. INTRODUCCIÓN
# ═══════════════════════════════════════════════════════════════════════════
story.append(section("1. Introducción"))
story.append(body(
    "HealthAnalytics IPS es una plataforma web integral diseñada para la gestión, análisis y "
    "predicción de datos clínicos. Permite a profesionales de la salud, analistas y administradores "
    "cargar datasets de pacientes, visualizar indicadores clave, entrenar modelos de Machine Learning "
    "para predicción de riesgos y exportar reportes en formato PDF."))
story.append(body(
    "Este manual describe todas las funcionalidades del sistema, los roles de usuario disponibles "
    "y los pasos necesarios para realizar cada operación."))

story.append(sub("Roles de Usuario"))
story.append(make_table(
    ["Rol", "Descripción", "Acceso Principal"],
    [
        ["Administrador", "Control total del sistema", "Todas las secciones + gestión de usuarios"],
        ["Médico", "Visualización clínica", "Dashboard, Pacientes, Reportes PDF"],
        ["Analista", "Análisis de datos", "Dashboard, Pacientes, ETL, ML, Reportes PDF"],
    ],
    [1.5*inch, 2.5*inch, 2.5*inch]
))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════
# 2. ACCESO AL SISTEMA
# ═══════════════════════════════════════════════════════════════════════════
story.append(section("2. Acceso al Sistema"))

story.append(sub("2.1. Página de Inicio de Sesión"))
story.append(body(
    "Para acceder a la plataforma, abra su navegador web y diríjase a la URL proporcionada por su "
    "administrador. Se mostrará la pantalla de inicio de sesión con un formulario para ingresar "
    "sus credenciales."))

img_login = screenshot("/tmp/manual_login.png")
if img_login:
    story.append(img_login)
    story.append(caption("Figura 1: Pantalla de inicio de sesión"))
story.append(spacer())

story.append(sub("2.2. Credenciales de Acceso"))
story.append(body("Ingrese su nombre de usuario y contraseña, luego haga clic en el botón <b>Ingresar</b>. "
    "El sistema cuenta con los siguientes usuarios predefinidos:"))

story.append(spacer(6))
story.append(make_table(
    ["Rol", "Usuario", "Contraseña"],
    [
        ["Administrador", "admin", "admin123"],
        ["Médico", "medico", "medico123"],
        ["Analista", "analista", "analista123"],
    ],
    [2.0*inch, 2.25*inch, 2.25*inch]
))
story.append(spacer(4))
story.append(body("Si olvida su contraseña, contacte al administrador del sistema."))

story.append(note_box("Nota",
    "Por seguridad, la sesión expira después de un período de inactividad. "
    "Deberá iniciar sesión nuevamente."))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════
# 3. DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
story.append(section("3. Dashboard — Panel Principal"))
story.append(body(
    "El Dashboard es la pantalla principal después de iniciar sesión. Muestra un resumen visual "
    "de los indicadores clave de la clínica (KPIs) y permite monitorear el estado general de los pacientes."))

img_dash = screenshot("/tmp/manual_dashboard.png")
if img_dash:
    story.append(img_dash)
    story.append(caption("Figura 2: Dashboard principal con KPIs"))
story.append(spacer())

story.append(sub("Indicadores disponibles"))
story.append(bullet("Total de pacientes registrados"))
story.append(bullet("Distribución por sexo (Masculino / Femenino)"))
story.append(bullet("Pacientes por nivel de riesgo (Bajo, Medio, Alto)"))
story.append(bullet("Promedio de edad"))
story.append(bullet("Pacientes críticos"))
story.append(bullet("Gráficos de distribución de IMC, glucosa y presión arterial"))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════
# 4. GESTIÓN DE PACIENTES
# ═══════════════════════════════════════════════════════════════════════════
story.append(section("4. Gestión de Pacientes"))
story.append(body(
    "La sección de Pacientes permite visualizar, buscar, filtrar y gestionar los registros de "
    "pacientes procesados por el sistema."))

img_pac = screenshot("/tmp/manual_pacientes.png")
if img_pac:
    story.append(img_pac)
    story.append(caption("Figura 3: Listado de pacientes con filtros"))
story.append(spacer())

story.append(sub("4.1. Buscar y Filtrar"))
story.append(body(
    "Utilice la barra de búsqueda para encontrar pacientes por nombre, documento o diagnóstico. "
    "Puede aplicar filtros combinados:"))
story.append(bullet("Riesgo: Bajo, Medio o Alto"))
story.append(bullet("Sexo: Masculino o Femenino"))
story.append(bullet("Crítico: Solo pacientes marcados como críticos"))

story.append(sub("4.2. Predecir Riesgo"))
story.append(body(
    "Los usuarios con rol <b>Analista</b> y <b>Administrador</b> pueden hacer clic en el botón "
    "<b>Predecir Riesgo</b> junto a cada paciente. El sistema analizará las variables clínicas "
    "del paciente usando el modelo de Machine Learning activo y mostrará:"))
story.append(bullet("El nivel de riesgo predicho (Bajo, Medio, Alto)"))
story.append(bullet("La probabilidad asociada"))
story.append(bullet("Una gráfica de distribución de probabilidades por clase"))

story.append(sub("4.3. Editar Paciente"))
story.append(body(
    "Los usuarios con rol <b>Administrador</b> pueden editar los datos de un paciente haciendo "
    "clic en el botón <b>Editar</b>. Se abrirá un formulario modal donde podrá modificar campos "
    "como peso, altura, presión arterial, glucosa, entre otros."))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════
# 5. ETL
# ═══════════════════════════════════════════════════════════════════════════
story.append(section("5. Módulo ETL — Carga de Datos"))
story.append(body(
    "El módulo ETL (Extract, Transform, Load) permite cargar archivos de datos clínicos al sistema. "
    "Los datos son procesados, limpiados y almacenados en la base de datos para su posterior análisis."))

img_etl = screenshot("/tmp/manual_etl.png")
if img_etl:
    story.append(img_etl)
    story.append(caption("Figura 4: Módulo ETL para carga de datos"))
story.append(spacer())

story.append(sub("5.1. Cargar Dataset"))
story.append(bullet("Seleccione un archivo en formato Excel (.xlsx) con los datos de pacientes"))
story.append(bullet("Haga clic en <b>Cargar</b> para iniciar el proceso de importación"))
story.append(bullet("El sistema mostrará el progreso y resultado de la operación"))
story.append(bullet("Los datos cargados estarán disponibles en la sección de Pacientes y Dashboard"))

story.append(sub("5.2. Historial de ETL"))
story.append(body(
    "Puede consultar el historial de todas las cargas realizadas, incluyendo fecha, "
    "número de registros procesados y estado de cada ejecución."))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════
# 6. ML
# ═══════════════════════════════════════════════════════════════════════════
story.append(section("6. Machine Learning"))
story.append(body(
    "El módulo de Machine Learning permite entrenar modelos predictivos utilizando los datos "
    "clínicos cargados en el sistema. Los modelos aprenden patrones a partir de las variables "
    "de los pacientes para predecir el nivel de riesgo de enfermedades cardiovasculares."))

img_ml = screenshot("/tmp/manual_ml.png")
if img_ml:
    story.append(img_ml)
    story.append(caption("Figura 5: Módulo de Machine Learning"))
story.append(spacer())

story.append(sub("6.1. Entrenar Modelo"))
story.append(body(
    "Seleccione uno de los algoritmos disponibles y haga clic en <b>Entrenar</b>:"))
story.append(bullet("Regresión Logística — modelo lineal interpretable"))
story.append(bullet("Árbol de Decisión — modelo basado en reglas"))
story.append(bullet("Random Forest — modelo de ensamble de alta precisión"))

story.append(sub("6.2. Evaluación de Modelos"))
story.append(body(
    "Después del entrenamiento, el sistema muestra métricas de rendimiento:"))
story.append(bullet("Precisión (Accuracy)"))
story.append(bullet("Precisión por clase (Precision)"))
story.append(bullet("Sensibilidad (Recall)"))
story.append(bullet("Puntuación F1"))
story.append(bullet("Matriz de confusión"))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════
# 7. REPORTES
# ═══════════════════════════════════════════════════════════════════════════
story.append(section("7. Exportación de Reportes"))
story.append(body(
    "El sistema permite exportar los datos de pacientes en formato PDF. "
    "La exportación respeta los filtros activos en la sección de Pacientes."))

story.append(sub("7.1. Exportar PDF"))
story.append(body(
    "Desde el menú lateral izquierdo, en la sección <b>Exportar</b>, haga clic en <b>PDF</b>. "
    "También puede exportar desde la sección de Pacientes usando el botón de exportación."))
story.append(bullet("El reporte incluye todos los pacientes filtrados actualmente"))
story.append(bullet("Se genera un documento PDF con formato profesional"))
story.append(bullet("El sistema muestra una notificación de éxito o error"))

story.append(note_box("Consejo",
    "Use los filtros de la sección Pacientes antes de exportar para obtener un reporte "
    "con solo los datos que necesita."))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════
# 8. USUARIOS
# ═══════════════════════════════════════════════════════════════════════════
story.append(section("8. Gestión de Usuarios"))
story.append(body(
    "Solo los usuarios con rol <b>Administrador</b> pueden acceder a la gestión de usuarios. "
    "Esta sección permite administrar las cuentas de todos los usuarios del sistema."))

img_usr = screenshot("/tmp/manual_usuarios.png")
if img_usr:
    story.append(img_usr)
    story.append(caption("Figura 6: Gestión de usuarios (solo administrador)"))
story.append(spacer())

story.append(sub("8.1. Crear Usuario"))
story.append(body(
    "Haga clic en <b>Nuevo Usuario</b> y complete el formulario con:"))
story.append(bullet("Username — nombre de usuario único"))
story.append(bullet("Email — correo electrónico"))
story.append(bullet("Nombres y Apellidos"))
story.append(bullet("Rol — Administrador, Médico o Analista"))
story.append(bullet("Contraseña — mínimo 8 caracteres"))

story.append(sub("8.2. Editar y Eliminar"))
story.append(body(
    "Puede editar los datos de cualquier usuario haciendo clic en el ícono de lápiz. "
    "Para eliminar un usuario, haga clic en el ícono de papelera. El sistema solicitará "
    "confirmación antes de eliminar."))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════
# 9. ROLES Y PERMISOS
# ═══════════════════════════════════════════════════════════════════════════
story.append(section("9. Roles y Permisos"))
story.append(body(
    "El sistema cuenta con tres roles de usuario con diferentes niveles de acceso. "
    "La siguiente matriz resume los permisos de cada rol:"))

story.append(spacer(8))
story.append(make_table(
    ["Módulo / Función", "Admin", "Médico", "Analista"],
    [
        ["Dashboard — KPIs y gráficos", "✅", "✅", "✅"],
        ["Pacientes — Visualizar listado", "✅", "✅", "✅"],
        ["Pacientes — Editar datos", "✅", "❌", "❌"],
        ["Pacientes — Predecir Riesgo", "✅", "❌", "✅"],
        ["ETL — Cargar datasets", "✅", "❌", "✅"],
        ["ML — Entrenar modelos", "✅", "❌", "✅"],
        ["ML — Predecir pacientes", "✅", "❌", "✅"],
        ["Reportes — Exportar PDF", "✅", "✅", "✅"],
        ["Usuarios — CRUD completo", "✅", "❌", "❌"],
    ],
    [3.0*inch, 1.2*inch, 1.15*inch, 1.15*inch]
))

story.append(spacer(12))
story.append(note_box("Importante",
    "Los cambios en roles y permisos solo pueden ser realizados por un usuario con rol Administrador "
    "desde la sección de Gestión de Usuarios."))

story.append(Spacer(1, 0.5*inch))
story.append(Paragraph(
    "— Fin del Manual —", 
    ParagraphStyle('EndMark', fontName='Helvetica-Bold', fontSize=12,
                   textColor=TEAL, alignment=TA_CENTER, spaceBefore=20)))

# ─── Build ─────────────────────────────────────────────────────────────────
doc.build(story)
print(f"✅ Manual generado: {OUTPUT}")
print(f"   Tamaño: {os.path.getsize(OUTPUT)/1024:.0f} KB")
