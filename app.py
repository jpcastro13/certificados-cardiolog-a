import io
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# --- OCULTAR LA BARRA SUPERIOR Y EL ICONO DE GITHUB ---
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ----------------------------- Configuración -----------------------------
st.set_page_config(
    page_title="Certificados - Congreso de Cardiología", page_icon="🫀"
)

ARCHIVO_EXCEL = "asistentes.xlsx"
PLANTILLA = "plantilla_certificado.png"
LOGO = "icono-zentria.png"  # Nombre exacto del archivo del logo que subiste
FUENTE = "OpenSans-Italic.ttf"
COLOR_TEXTO = "#7B1F6A"

# Posiciones en proporción al tamaño de la plantilla
X_CENTRO = 0.408  # centro horizontal de la línea del nombre
Y_NOMBRE = 0.355  # justo encima de la línea de degradado
Y_DOC = 0.420  # posición de "C.C."
ANCHO_MAX = 0.60  # ancho máximo del nombre (proporción del ancho)

st.title("Congreso Nacional de Cardiología y Cuidado Crítico Cardiovascular")
st.subheader("Plataforma de Descarga de Certificados de Asistencia")

st.markdown(
    "Por favor, ingresa tu **número de documento de identidad** (sin puntos ni"
    " espacios) para verificar tu registro y descargar tu certificado."
)


# ----------------------------- Funciones -----------------------------
@st.cache_data
def cargar_datos():
  df = pd.read_excel(ARCHIVO_EXCEL)

  df["Número de documento"] = (
      df["Número de documento"]
      .astype(str)
      .str.strip()
      .str.replace(r"\.0$", "", regex=True)
  )
  df["Nombre completo"] = df["Nombre completo"].astype(str).str.strip()

  # Filtrar filas de prueba
  df = df[df["Número de documento"] != "1"]
  return df


def cargar_fuente(size):
  """Intenta la fuente del proyecto, luego una del sistema, luego la por defecto."""
  for ruta in (
      FUENTE,
      "DejaVuSans-Oblique.ttf",
      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
      "arial.ttf",
  ):
    try:
      return ImageFont.truetype(ruta, size)
    except OSError:
      continue
  return ImageFont.load_default(size=size)


def generar_certificado_pdf(nombre, documento):
  img = Image.open(PLANTILLA).convert("RGB")
  W, H = img.size

  # --- INCLUIR EL LOGO DE ZENTRIA EN LA ESQUINA SUPERIOR DERECHA ---
  try:
    logo = Image.open(LOGO).convert("RGBA")
    # Definir un ancho proporcional para el logo (ej. 12% del ancho total)
    logo_ancho_deseado = int(W * 0.12)
    aspect_ratio = logo.height / logo.width
    logo_alto_deseado = int(logo_ancho_deseado * aspect_ratio)

    logo = logo.resize((logo_ancho_deseado, logo_alto_deseado), Image.Resampling.LANCZOS)

    # Márgenes desde la esquina superior derecha
    margen_derecho = int(W * 0.04)
    margen_superior = int(H * 0.04)
    pos_x = W - logo_ancho_deseado - margen_derecho
    pos_y = margen_superior

    # Pegar el logo respetando sus transparencias
    img.paste(logo, (pos_x, pos_y), logo)
  except Exception as e:
    pass  # Si ocurre algún inconveniente con el logo, el certificado se genera igual

  draw = ImageDraw.Draw(img)

  x_centro = int(W * X_CENTRO)
  y_nombre = int(H * Y_NOMBRE)
  y_doc = int(H * Y_DOC)
  ancho_max = int(W * ANCHO_MAX)

  # Nombre: reduce el tamaño si es muy largo
  nombre = nombre.title()
  size = int(H * 0.058)
  font_nombre = cargar_fuente(size)
  while draw.textlength(nombre, font=font_nombre) > ancho_max and size > 20:
    size -= 2
    font_nombre = cargar_fuente(size)

  font_doc = cargar_fuente(int(H * 0.034))

  draw.text(
      (x_centro, y_nombre),
      nombre,
      fill=COLOR_TEXTO,
      anchor="mm",
      font=font_nombre,
  )
  draw.text(
      (x_centro, y_doc),
      f"C.C. {documento}",
      fill=COLOR_TEXTO,
      anchor="mm",
      font=font_doc,
  )

  pdf_bytes = io.BytesIO()
  img.save(pdf_bytes, format="PDF", resolution=150)
  pdf_bytes.seek(0)
  return pdf_bytes


# ----------------------------- Carga de datos -----------------------------
try:
  df_asistentes = cargar_datos()
except Exception as e:
  st.error(f"Error al cargar la base de datos de Excel: {e}")
  df_asistentes = None

# ----------------------------- Interfaz -----------------------------
documento_input = st.text_input("Número de Documento de Identidad:")

if st.button("Consultar Certificado"):
  if not documento_input:
    st.warning("Por favor, ingresa un número de documento.")
  elif df_asistentes is None:
    st.error("No se pudo cargar la base de datos.")
  else:
    doc_buscado = documento_input.strip()
    resultado = df_asistentes[
        df_asistentes["Número de documento"] == doc_buscado
    ]

    if not resultado.empty:
      nombre_asistente = resultado.iloc[0]["Nombre completo"]
      st.success(
          f"¡Registro encontrado! Bienvenido(a), **{nombre_asistente}**."
      )

      try:
        pdf_bytes = generar_certificado_pdf(nombre_asistente, doc_buscado)
        st.download_button(
            label="📥 Descargar Certificado en PDF",
            data=pdf_bytes,
            file_name=f"Certificado_Cardiologia_{doc_buscado}.pdf",
            mime="application/pdf",
        )
      except Exception as ex:
        st.error(
            f"Hubo un error al procesar la plantilla del certificado: {ex}"
        )
    else:
      st.error(
          "El número de documento ingresado no se encuentra en la base de"
          " datos de asistentes al congreso. Verifica el número o contacta al"
          " administrador."
      )
