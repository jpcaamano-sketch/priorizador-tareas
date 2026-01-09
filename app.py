import streamlit as st
import json
import google.generativeai as genai
from fpdf import FPDF
import pandas as pd
import io

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Priorizador de Tareas", layout="centered")

# --- 2. ESTÉTICA LIMPIA ---
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 2rem;}
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

# --- 4. FUNCIONES DE EXPORTACIÓN ---

# A) Generar PDF
def crear_pdf(data_json, rol_usuario):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'Reporte de Priorización Eisenhower', 0, 1, 'C')
            self.ln(5)

    pdf = PDF()
    pdf.add_page()
    
    def limpio(texto):
        if not texto: return ""
        return texto.encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, limpio(f"Rol Analizado: {rol_usuario}"), 0, 1)
    pdf.ln(5)

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

    pdf.ln(5)
    pdf.set_font("Arial", 'I', 12)
    pdf.multi_cell(0, 10, limpio(f"Consejo: {data_json.get('recomendacion_top', '')}"))

    return pdf.output(dest='S').encode('latin-1')

# B) Generar Excel
def crear_excel(data_json):
    # Crear una lista plana para la tabla
    filas = []
    
    # Mapeo de categorías a nombres bonitos
    mapa_cat = {
        "hacer": "1. HACER (Urgente/Importante)",
        "planificar": "2. PLANIFICAR (No Urgente/Importante)",
        "delegar": "3. DELEGAR (Urgente/No Importante)",
        "eliminar": "4. ELIMINAR (Ni Urgente/Ni Importante)"
    }
    
    for key, titulo in mapa_cat.items():
        tareas = data_json.get(key, [])
        for t in tareas:
            filas.append({"Prioridad": titulo, "Tarea": t})
            
    df = pd.DataFrame(filas)
    
    # Buffer de memoria para guardar el Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Matriz Eisenhower')
    
    return output.getvalue()

# --- 5. LÓGICA IA ---
def analyze_tasks(tasks, role, model_name):
    try:
        model = genai.GenerativeModel(model_name)
        prompt = f"""
        Actúa como experto de productividad. Clasifica las tareas para un "{role}".
        INSTRUCCIONES:
        1. Responde SOLO JSON válido.
        2. Esquema:
        {{
            "hacer": ["tarea", "tarea"],
            "planificar": ["tarea"],
            "delegar": ["tarea"],
            "eliminar": ["tarea"],
            "recomendacion_top": "Consejo breve"
        }}
        LISTA DE TAREAS: {tasks}
        """
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "")
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            return json.loads(text[start:end])
        return json.loads(text)
    except Exception:
        return None

# --- 6. INTERFAZ ---
st.title("🛡️ Priorizador de Tareas")
st.caption("Organiza tu día con Inteligencia Artificial.")
st.divider()

col_input1, col_input2 = st.columns([1, 3])
with col_input1:
    user_role = st.text_input("1. ¿Cuál es tu rol?", value="Coach Profesional")
tasks_input = st.text_area("2. Pega tu lista de tareas:", height=150)

# Variables de estado para guardar el resultado entre recargas
if 'resultado_ia' not in st.session_state:
    st.session_state.resultado_ia = None

if st.button("🚀 Priorizar mis tareas", type="primary", use_container_width=True):
    if not tasks_input:
        st.warning("⚠️ Escribe tareas para comenzar.")
    else:
        with st.spinner("Analizando..."):
            st.session_state.resultado_ia = analyze_tasks(tasks_input, user_role, modelo_seleccionado)

# Mostrar resultados si existen
if st.session_state.resultado_ia:
    result = st.session_state.resultado_ia
    
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
    
    # --- ZONA DE DESCARGAS ---
    st.subheader("📥 Exportar Resultados")
    
    col_d1, col_d2, col_d3 = st.columns([2, 1, 1])
    
    with col_d1:
        nombre_archivo = st.text_input("Nombre del archivo:", value="Mis_Prioridades")
    
    with col_d2:
        formato = st.radio("Formato:", ["PDF", "Excel"], horizontal=True)
    
    with col_d3:
        st.write("") # Espacio para alinear el botón abajo
        st.write("")
        
        if formato == "PDF":
            data_file = crear_pdf(result, user_role)
            mime_type = "application/pdf"
            ext = "pdf"
        else:
            data_file = crear_excel(result)
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ext = "xlsx"
            
        st.download_button(
            label=f"Bajar {formato}",
            data=data_file,
            file_name=f"{nombre_archivo}.{ext}",
            mime=mime_type,
            use_container_width=True
        )
