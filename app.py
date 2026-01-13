import streamlit as st
import json
import google.generativeai as genai
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Priorizador Eisenhower", page_icon="🛡️", layout="wide")

# CSS para ocultar elementos innecesarios y limpiar la interfaz
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN SEGURA (CLOUD & LOCAL) ---
try:
    # Intenta leer la clave desde los secretos de Streamlit (secrets.toml o Cloud)
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("⚠️ Error de Seguridad: No se encontró la API KEY.")
    st.info("Nota: Si estás en local, asegura que exista .streamlit/secrets.toml. Si estás en la nube, configúrala en los 'Secrets' del dashboard.")
    st.stop()

# --- 3. INTERFAZ DE USUARIO ---
st.title("🛡️ Priorizador de Eisenhower")
st.caption("Organización inteligente de tareas basada en tu rol profesional.")

st.divider()

# Input del ROL (Movido arriba de la lista como pediste)
user_role = st.text_input(
    "👤 ¿Cuál es tu rol o cargo?", 
    value="Profesional ocupado",
    placeholder="Ej: Gerente de Ventas, Abogado, Dueña de casa..."
)

# Input de TAREAS
st.subheader("📝 Tu lista de pendientes")
tasks_input = st.text_area(
    "Escribe tus tareas aquí (una por línea):",
    height=150,
    placeholder="Revisar contrato del cliente X\nComprar cartulina para el hijo\nLlamar al contador..."
)

# --- 4. LÓGICA DE INTELIGENCIA ARTIFICIAL ---
def analyze_tasks(tasks, role):
    try:
        # Usamos un modelo fijo y rápido (Flash) para que el usuario no tenga que elegir
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = f"""
        Actúa como un experto en productividad para un "{role}".
        Clasifica estas tareas en la Matriz de Eisenhower.
        
        TAREAS:
        {tasks}
        
        FORMATO JSON REQUERIDO (Estrictamente solo JSON):
        {{
            "hacer": ["tarea 1", "tarea 2"],
            "planificar": ["tarea 3"],
            "delegar": ["tarea 4"],
            "eliminar": ["tarea 5"],
            "recomendacion_top": "Un consejo breve de una frase sobre el foco de hoy"
        }}
        """
        response = model.generate_content(prompt)
        # Limpieza de la respuesta para asegurar JSON puro
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)

    except Exception as e:
        st.error(f"Error al procesar: {e}")
        return None

# --- 5. EJECUCIÓN ---
if st.button("🚀 Priorizar Ahora", type="primary", use_container_width=True):
    if not tasks_input:
        st.warning("⚠️ La lista está vacía. Escribe algo para comenzar.")
    else:
        with st.spinner("Analizando urgencia e importancia..."):
            result = analyze_tasks(tasks_input, user_role)
            
            if result:
                st.divider()
                
                # Fila superior
                col1, col2 = st.columns(2)
                with col1:
                    st.success("🔥 1. HACER YA (Urgente e Importante)")
                    for t in result.get("hacer", []): st.write(f"• {t}")
                    if not result.get("hacer"): st.write("*Nada por aquí*")
                
                with col2:
                    st.info("📅 2. PLANIFICAR (No Urgente pero Importante)")
                    for t in result.get("planificar", []): st.write(f"• {t}")
                    if not result.get("planificar"): st.write("*Nada por aquí*")

                st.divider()

                # Fila inferior
                col3, col4 = st.columns(2)
                with col3:
                    st.warning("🤝 3. DELEGAR (Urgente pero No Importante)")
                    for t in result.get("delegar", []): st.write(f"• {t}")
                    if not result.get("delegar"): st.write("*Nada por aquí*")
                
                with col4:
                    st.error("🗑️ 4. ELIMINAR (Ni Urgente ni Importante)")
                    for t in result.get("eliminar", []): st.write(f"• {t}")
                    if not result.get("eliminar"): st.write("*Nada por aquí*")
                
                # Consejo final
                st.markdown(f"""
                <div style="background-color:#f0f2f6;padding:15px;border-radius:10px;margin-top:20px;text-align:center;">
                    <b>💡 Consejo del Coach:</b> {result.get('recomendacion_top', '')}
                </div>
                """, unsafe_allow_html=True)