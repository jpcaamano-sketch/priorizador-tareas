import streamlit as st
import json
import google.generativeai as genai
from fpdf import FPDF

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Priorizador de Tareas", layout="centered")

# --- 2. ESTÉTICA LIMPIA (Restaurada) ---
# Ocultamos menú, header y footer para apariencia profesional
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Ajuste para subir el contenido ya que no hay barra superior */
    .block-container {
        padding-top: 2rem;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 3. CONFIGURACIÓN DEL CEREBRO ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("⚠️ Falta la API Key en la configuración.")
    st.stop()

modelo_seleccionado = "models/gemma-3-1b-it"

# --- 4. FUNCIÓN PARA GENERAR PDF ---
def crear_pdf(data_json, rol_usuario):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'Reporte de Priorización Eisenhower', 0, 1, 'C')
            self.ln(5)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    def limpio(texto):
        if not texto: return ""
        return texto.encode('latin-1', 'replace').decode('latin-1')

    # Datos Encabezado
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
        pdf.set_text_color(50, 50, 150)
        pdf.cell(0, 10, limpio(titulo), 0, 1)
        
        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0)
        items = data_json.get(key, [])
        
        if not items:
            pdf.cell(0, 8, limpio("- (Ninguna tarea)"), 0, 1)
        else:
            for item in items:
                pdf.cell(0, 8, limpio(f"- {item}"), 0, 1)
        pdf.ln(5)

    # Consejo
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 12)
    pdf.multi_cell(0, 10, limpio(f"Consejo del Experto: {data_json.get('recomendacion_top', '')}"))

    return pdf.output(dest='S').encode('latin-1')

# --- 5. LÓGICA IA ROBUSTA (A prueba de fallos) ---
def analyze_tasks(tasks, role, model_name):
    try:
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        Actúa como un sistema experto de productividad (Coach Ejecutivo).
        Tu tarea es recibir una lista de tareas y clasificarlas en la Matriz de Eisenhower.
        
        Rol del usuario: "{role}"
        Lista de Tareas:
        {tasks}
        
        INSTRUCCIONES:
        1. Responde ÚNICAMENTE con un objeto JSON válido.
        2. NO escribas texto introductorio ni markdown.
        3. Esquema obligatorio:
        {{
            "hacer": ["tarea", "tarea"],
            "planificar": ["tarea"],
            "delegar": ["tarea"],
            "eliminar": ["tarea"],
            "recomendacion_top": "Consejo breve"
        }}
        """
        response = model.generate_content(prompt)
        text = response.text

        # Limpieza quirúrgica del JSON
        text = text.replace("```json", "").replace("```", "")
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start != -1 and end != -1:
            clean_json = text[start:end]
            return json.loads(clean_json)
        else:
            # Intento de respaldo
            return json.loads(text)

    except Exception as e:
        print(f"Error silencioso: {e}") # Log interno
        return None

# --- 6. INTERFAZ VISUAL ---
st.title("🛡️ Priorizador de Tareas")
st.caption("Organiza tu día con Inteligencia Artificial.")
st.divider()

col_input1, col_input2 = st.columns([1, 3])
with col_input1:
    user_role = st.text_input("1. ¿Cuál es tu rol?", value="Coach Profesional")

tasks_input = st.text_area("2. Pega tu lista de tareas:", height=150, placeholder="Ejemplo:\nLlamar al cliente\nRedactar informe\nComprar café")

if st.button("🚀 Priorizar mis tareas", type="primary", use_container_width=True):
    if not tasks_input:
        st.warning("⚠️ Escribe tareas para comenzar.")
    else:
        with st.spinner("Analizando matriz de prioridades..."):
            result = analyze_tasks(tasks_input, user_role, modelo_seleccionado)
            
            if result:
                st.markdown("### 🎯 Resultados")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.success("🔥 HACER YA")
                    for t in result.get("hacer", []): st.write(f"• {t}")
                with c2:
                    st.info("📅 PLANIFICAR")
                    for t in result.get("planificar", []): st.write(f"• {t}")
                
                c3, c4 = st.columns(2)
                with c3:
                    st.warning("🤝 DELEGAR")
                    for t in result.get("delegar", []): st.write(f"• {t}")
                with c4:
                    st.error("🗑️ ELIMINAR")
                    for t in result.get("eliminar", []): st.write(f"• {t}")
                
                st.divider()
                st.info(f"💡 **Consejo:** {result.get('recomendacion_top', '')}")
                
                # Botón PDF
                try:
                    pdf_bytes = crear_pdf(result, user_role)
                    st.download_button(
                        label="📄 Descargar Reporte PDF",
                        data=pdf_bytes,
                        file_name="Prioridades_Eisenhower.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error generando PDF: {e}")
            else:
                st.error("El modelo no pudo procesar las tareas. Por favor intenta de nuevo.")
