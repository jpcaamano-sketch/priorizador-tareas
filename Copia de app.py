import streamlit as st
import json
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Priorizador de Tareas", layout="centered")

# --- TRUCO CSS: OCULTAR MENÚS Y PIE DE PÁGINA ---
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    /* Opcional: Ajustar el padding superior para que el título suba más */
    .block-container {
        padding-top: 2rem;
    }
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

# --- 3. MODELO FIJO ---
modelo_seleccionado = "models/gemma-3-1b-it"

# --- INTERFAZ PRINCIPAL ---
st.title("🛡️ Priorizador de Tareas")
st.caption("Organiza tu día usando la Matriz de Eisenhower e Inteligencia Artificial.")

st.divider()

# Inputs
col_input1, col_input2 = st.columns([1, 3])
with col_input1:
    user_role = st.text_input("1. ¿Cuál es tu rol?", value="Coach Profesional")

tasks_input = st.text_area("2. Pega tu lista de tareas:", height=150, placeholder="Ejemplo:\nLlamar al cliente Juan\nComprar tinta impresora\nEscribir post de LinkedIn\nRevisar facturas del mes")

# --- LÓGICA DE INTELIGENCIA ARTIFICIAL ---
def analyze_tasks(tasks, role, model_name):
    try:
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        Actúa como experto en productividad para un "{role}".
        Clasifica estas tareas en la Matriz de Eisenhower.
        
        TAREAS:
        {tasks}
        
        FORMATO JSON REQUERIDO (Solo JSON, sin markdown):
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
        st.error(f"Error procesando con el modelo: {e}")
        return None

# --- BOTÓN Y RESULTADOS ---
if st.button("🚀 Priorizar mis tareas", type="primary", use_container_width=True):
    if not tasks_input:
        st.warning("⚠️ Por favor, escribe algunas tareas antes de procesar.")
    else:
        with st.spinner("Analizando prioridades..."):
            result = analyze_tasks(tasks_input, user_role, modelo_seleccionado)
            
            if result:
                st.markdown("### 🎯 Resultados")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.success("🔥 HACER YA")
                    for t in result.get("hacer", []): st.write(f"• {t}")
                
                with col2:
                    st.info("📅 PLANIFICAR")
                    for t in result.get("planificar", []): st.write(f"• {t}")
                
                st.write("") # Espacio
                
                col3, col4 = st.columns(2)
                with col3:
                    st.warning("🤝 DELEGAR")
                    for t in result.get("delegar", []): st.write(f"• {t}")
                
                with col4:
                    st.error("🗑️ ELIMINAR")
                    for t in result.get("eliminar", []): st.write(f"• {t}")
                
                st.divider()
                st.markdown(f"**💡 Consejo:** {result.get('recomendacion_top', '')}")