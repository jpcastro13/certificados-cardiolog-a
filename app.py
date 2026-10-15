import io
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Certificados - V Congreso de Cardiología", page_icon="🫀"
)

st.title("V Congreso Nacional de Cardiología y Cuidado Crítico Cardiovascular")
st.subheader("Plataforma de Descarga de Certificados de Asistencia")

st.markdown(
    "Por favor, ingresa tu **número de documento de identidad** (sin puntos ni"
    " espacios) para verificar tu registro y descargar tu certificado."
)


# Cargar los datos de los asistentes desde el Excel
@st.cache_data
def cargar_datos():
  # Usamos el nombre corto y sin espacios para evitar errores
  archivo_excel = "asistentes.xlsx"
  df = pd.read_excel(archivo_excel)

  # Limpiar y normalizar los números de documento como texto
  df["Número de documento"] = (
      df["Número de documento"]
      .astype(str)
      .str.strip()
      .str.replace(".0", "", regex=False)
  )
  df["Nombre completo"] = df["Nombre completo"].astype(str).str.strip()

  # Filtrar filas vacías o de prueba
  df = df[df["Número de documento"] != "1"]
  return df


try:
  df_asistentes = cargar_datos()
except Exception as e:
  st.error(f"Error al cargar la base de datos de Excel: {e}")
  df_asistentes = None

# Campo de entrada del documento
documento_input = st.text_input("Número de Documento de Identidad:")

if st.button("Consultar Certificado"):
  if not documento_input:
    st.warning("Por favor, ingresa un número de documento.")
  elif df_asistentes is None:
    st.error("No se pudo cargar la base de datos.")
  else:
    # Buscar el documento en el DataFrame
    doc_buscado = documento_input.strip()
    resultado = df_asistentes[df_asistentes["Número de documento"] == doc_buscado]

    if not resultado.empty:
      nombre_asistente = resultado.iloc[0]["Nombre completo"]
      st.success(
          f"¡Registro encontrado! Bienvenido(a), **{nombre_asistente}**."
      )

      # --- Generación del Certificado Dinámico ---
      try:
        # Cargar la plantilla en imagen PNG
        plantilla_path = "plantilla_certificado.png"
        img = Image.open(plantilla_path)
        draw = ImageDraw.Draw(img)

        try:
          font = ImageFont.truetype("arial.ttf", size=55)
        except:
          font = ImageFont.load_default()

        # Coordenadas (X, Y) para ubicar el nombre centrado
        x_centro = 960
        y_pos = 520

        draw.text(
            (x_centro, y_pos),
            nombre_asistente.title(),
            fill="#1B365D",
            anchor="mm",
            font=font,
        )

        # Guardar en memoria como PDF
        pdf_bytes = io.BytesIO()
        img.save(pdf_bytes, format="PDF")
        pdf_bytes.seek(0)

        # Botón para descargar
        st.download_button(
            label="📥 Descargar Certificado en PDF",
            data=pdf_bytes,
            file_name=f"Certificado_Cardiologia_{doc_buscado}.pdf",
            mime="application/pdf",
        )

      except Exception as ex:
        st.error(
            "Hubo un error al procesar la plantilla gráfica del certificado:"
            f" {ex}"
        )

    else:
      st.error(
          "El número de documento ingresado no se encuentra en la base de"
          " datos de asistentes al congreso. Verifica el número o contacta al"
          " administrador."
      )
