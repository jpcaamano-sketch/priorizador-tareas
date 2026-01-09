import streamlit as st
import json
import google.generativeai as genai
from fpdf import FPDF
import base64

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Priorizador de Tareas", layout="centered")

# --- TRUCO CSS: OCULTAR MENÚS ---
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN DEL CEREBRO ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("⚠️ Falta la API Key en .streamlit/secrets.toml")
    st.stop()

modelo_seleccionado = "models/gemma-3-1b-it"

# --- 3. FUNCIÓN PARA GENERAR PDF ---
def crear_pdf(data_json, rol_usuario):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'Reporte de Priorización Eisenhower', 0, 1, 'C')
            self.ln(5)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Función auxiliar para caracteres en español (tildes/ñ)
    def limpio(texto):
        return texto.encode('latin-1', 'replace').decode('latin-1')

    # Datos del Encabezado
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, limpio(f"Rol Analizado: {rol_usuario}"), 0, 1)
    pdf.ln(5)

    # Cuadrantes
    categorias = [
        ("HACER YA (Urgente e Importante)", "hacer"),
        ("PLANIFICAR (Importante, No Urgente)", "planificar"),
        ("DELEGAR (Urgente, No Importante)", "delegar"),
        ("ELIMINAR (Ni Urgente, Ni Importante)", "eliminar")
    ]

    for titulo, key in categorias:
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(50, 50, 150) # Azul oscuro
        pdf.cell(0, 10, limpio(titulo), 0, 1)
        
        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0) # Negro
        items = data_json.get(key, [])
        
        if not items:
            pdf.cell(0, 8, limpio("- (Ninguna tarea)"), 0, 1)
        else:
            for item in items:
                pdf.cell(0, 8, limpio(f"- {item}"), 0, 1)
        pdf.ln(5)

    # Consejo Final
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 12)
    pdf.multi_cell(0, 10, limpio(f"Consejo del Experto: {data_json.get('recomendacion_top', '')}"))

    # Retornar el PDF como string binario
    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFAZ PRINCIPAL ---
st.title("🛡️ Priorizador de Tareas")
st.caption("Organiza tu día usando la Matriz de Eisenhower e Inteligencia Artificial.")
st.divider()

col_input1, col_input2 = st.columns([1, 3])
with col_input1:
    user_role = st.text_input("1. ¿Cuál es tu rol?", value="Coach Profesional")

tasks_input = st.text_area("2. Pega tu lista de tareas:", height=150, placeholder="Ejemplo:\nLlamar al cliente Juan\nComprar tinta\nEscribir post LinkedIn")

# --- LÓGICA IA ---
def analyze_tasks(tasks, role, model_name):
    try:
        model = genai.GenerativeModel(model_name)
        prompt = f"""
        Actúa como experto en productividad para un "{role}".
        Clasifica estas tareas en la Matriz de Eisenhower.
        TAREAS: {tasks}
        FORMATO JSON REQUERIDO (Solo JSON):
        {{
            "hacer": ["tarea 1"],
            "planificar": ["tarea 2"],
            "delegar": ["tarea 3"],
            "eliminar": ["tarea 4"],
            "recomendacion_top": "Consejo breve"
        }}
        """
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# --- BOTONES Y ACCIÓN ---
if st.button("🚀 Priorizar mis tareas", type="primary", use_container_width=True):
    if not tasks_input:
        st.warning("⚠️ Escribe tareas primero.")
    else:
        with st.spinner("Analizando..."):
            result = analyze_tasks(tasks_input, user_role, modelo_seleccionado)
            
            if result:
                # Mostrar resultados en pantalla
                col1, col2 = st.columns(2)
                with col1:
                    st.success("🔥 HACER YA")
                    for t in result.get("hacer", []): st.write(f"• {t}")
                with col2:
                    st.info("📅 PLANIFICAR")
                    for t in result.get("planificar", []): st.write(f"• {t}")
                
                col3, col4 = st.columns(2)
                with col3:
                    st.warning("🤝 DELEGAR")
                    for t in result.get("delegar", []): st.write(f"• {t}")
                with col4:
                    st.error("🗑️ ELIMINAR")
                    for t in result.get("eliminar", []): st.write(f"• {t}")

                st.divider()
                st.markdown(f"**💡 Consejo:** {result.get('recomendacion_top', '')}")
                
                # --- NUEVO: BOTÓN DE DESCARGA PDF ---
                pdf_bytes = crear_pdf(result, user_role)
                st.download_button(
                    label="📄 Descargar Reporte PDF",
                    data=pdf_bytes,
                    file_name="reporte_eisenhower.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )