from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime, date
import os
import platform
import subprocess
import sys

# -------------------------------------------------------------------
# Utilidades de rutas (soporta ejecución normal y desde .exe PyInstaller)
# -------------------------------------------------------------------
def resource_path(relative_path: str) -> str:
    """Devuelve la ruta absoluta a un recurso, compatible con PyInstaller."""
    try:
        base_path = sys._MEIPASS  # carpeta temporal del .exe
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# -------------------------------------------------------------------
# Registro de fuentes
# - Intenta usar DejaVu desde ./fonts o desde reportlab/fonts si lo empaquetas.
# - Si falla, usa Helvetica / Helvetica-Bold (estándar de ReportLab).
# -------------------------------------------------------------------
def _registrar_fuentes():
    usar_dejavu = False

    # Posibles ubicaciones de los .ttf
    candidatos_regular = [
        "fonts/DejaVuSans.ttf",             # si incluyes ./fonts en tu proyecto
        "reportlab/fonts/DejaVuSans.ttf",   # si incluyes las fuentes de reportlab
    ]
    candidatos_bold = [
        "fonts/DejaVuSans-Bold.ttf",
        "reportlab/fonts/DejaVuSans-Bold.ttf",
    ]

    regular_path = next((p for p in candidatos_regular if os.path.exists(resource_path(p))), None)
    bold_path = next((p for p in candidatos_bold if os.path.exists(resource_path(p))), None)

    if regular_path and bold_path:
        try:
            pdfmetrics.registerFont(TTFont("DejaVu", resource_path(regular_path)))
            pdfmetrics.registerFont(TTFont("DejaVu-Bold", resource_path(bold_path)))
            usar_dejavu = True
        except Exception as e:
            # Si algo falla, se hará fallback
            print("No se pudieron registrar fuentes DejaVu:", e)

    # Nombres de fuentes a usar en el resto del código
    fuente = "DejaVu" if usar_dejavu else "Helvetica"
    fuente_b = "DejaVu-Bold" if usar_dejavu else "Helvetica-Bold"
    return usar_dejavu, fuente, fuente_b

USAR_DEJAVU, FUENTE, FUENTE_B = _registrar_fuentes()

# -------------------------------------------------------------------
# Utilidades de fecha
# -------------------------------------------------------------------
def _parse_fecha(fecha_str_or_date):
    """
    Acepta str (YYYY-MM-DD o DD/MM/YYYY o DD-MM-YYYY/YY) o date/datetime.
    Devuelve datetime.date o None.
    """
    if not fecha_str_or_date:
        return None
    if isinstance(fecha_str_or_date, (datetime, date)):
        return fecha_str_or_date if isinstance(fecha_str_or_date, date) else fecha_str_or_date.date()
    if isinstance(fecha_str_or_date, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d-%m-%y"):
            try:
                return datetime.strptime(fecha_str_or_date, fmt).date()
            except Exception:
                continue
    return None

def _fmt_ddmmyyyy(fecha_str_or_date) -> str:
    """Devuelve la fecha en 'DD/MM/YYYY' o '' si no se puede parsear."""
    d = _parse_fecha(fecha_str_or_date)
    return d.strftime("%d/%m/%Y") if d else ""

# -------------------------------------------------------------------
# Abrir PDF según sistema operativo (silencioso si falla)
# -------------------------------------------------------------------
def _abrir_automaticamente(ruta_pdf: str):
    try:
        so = platform.system().lower()
        if "windows" in so:
            os.startfile(ruta_pdf)  # type: ignore[attr-defined]
        elif "darwin" in so:  # macOS
            subprocess.Popen(["open", ruta_pdf], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:  # Linux y otros
            subprocess.Popen(["xdg-open", ruta_pdf], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

# -------------------------------------------------------------------
# Generador de recibo (PDF)
# -------------------------------------------------------------------
def generar_recibo(usuario, membresia=None, fecha_registro=None, fecha_vencimiento=None, monto=None):
    """
    Genera un PDF de recibo.
    Parámetros:
      - usuario: tupla (id, nombre, apellido, telefono, membresia_db, fecha_registro_db, fecha_vencimiento_db)
      - membresia / fecha_registro / fecha_vencimiento: opcionales para override (p.ej. renovación)
      - monto: opcional; si no se pasa, se intenta inferir por tipo de membresía (20/50/200)

    Crea el archivo en 'recibos/recibo_<id>_<timestamp>.pdf' y lo abre automáticamente si puede.
    Devuelve la ruta del PDF creado.
    """
    # Desempaquetar
    id_u, nombre, apellido, telefono, mem_db, f_reg_db, f_ven_db = usuario

    # Determinar valores finales
    mem = membresia or mem_db
    f_reg = fecha_registro or f_reg_db
    f_ven = fecha_vencimiento or f_ven_db

    # Fallback para monto si no viene
    if monto is None:
        precios_locales = {"Mensual": 20, "Trimestral": 50, "Anual": 200}
        monto = precios_locales.get(str(mem), None)

    # Carpeta de salida
    carpeta = "recibos"
    os.makedirs(carpeta, exist_ok=True)
    nombre_pdf = os.path.join(carpeta, f"recibo_{id_u}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

    # Canvas
    c = canvas.Canvas(nombre_pdf, pagesize=LETTER)
    c.setTitle("Recibo de Inscripción / Renovación")
    ancho, alto = LETTER

    # Márgenes y coordenadas iniciales
    left = 55
    right = ancho - 55
    y = alto - 50
    esp = 22

    # Encabezado
    c.setFont(FUENTE_B, 18)
    c.drawCentredString(ancho / 2, y, "OPPTYMUS GYM")
    y -= 18
    c.setFont(FUENTE, 12)
    c.drawCentredString(ancho / 2, y, "Recibo de Inscripción / Renovación")
    y -= 14
    c.line(left, y, right, y)
    y -= 20

    # Info del recibo
    c.setFont(FUENTE, 10)
    c.drawRightString(right, y, f"Fecha de emisión: {_fmt_ddmmyyyy(datetime.now())}")
    c.drawString(left, y, f"N° Recibo: {id_u}-{datetime.now().strftime('%H%M%S')}")
    y -= 20

    # Datos del cliente
    c.setFont(FUENTE_B, 12)
    c.drawString(left, y, "Datos del cliente")
    y -= 6
    c.line(left, y, left + 140, y)
    y -= 14
    c.setFont(FUENTE, 12)
    c.drawString(left + 10, y, f"Nombre: {nombre} {apellido}"); y -= esp
    c.drawString(left + 10, y, f"Teléfono: {telefono}"); y -= esp

    # Detalle de la membresía
    c.setFont(FUENTE_B, 12)
    c.drawString(left, y, "Detalle de la membresía")
    y -= 6
    c.line(left, y, left + 200, y)
    y -= 14
    c.setFont(FUENTE, 12)
    c.drawString(left + 10, y, f"Tipo: {mem}"); y -= esp
    c.drawString(left + 10, y, f"Fecha de registro: {_fmt_ddmmyyyy(f_reg)}"); y -= esp
    c.drawString(left + 10, y, f"Válido hasta: {_fmt_ddmmyyyy(f_ven)}"); y -= esp

    # Total
    if monto is not None:
        c.setFont(FUENTE_B, 13)
        c.drawString(left + 10, y, f"Total cancelado: ${monto}")
        y -= esp

    # Mensaje final
    c.setFont(FUENTE, 11)
    mensaje = "¡Gracias por ser parte de nuestra familia de entrenamiento!"
    if not USAR_DEJAVU:
        mensaje = "¡Gracias por ser parte de nuestra familia de entrenamiento!"
    c.drawString(left + 10, y - 8, mensaje)

    # Cerrar PDF
    c.save()

    # Intentar abrir
    _abrir_automaticamente(nombre_pdf)

    return nombre_pdf
