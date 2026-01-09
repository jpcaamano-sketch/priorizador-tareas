import streamlit as st
import json
import google.generativeai as genai
from fpdf import FPDF
import base64

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Priorizador de Tareas", layout="centered")

# --- 2. CONFIGURACIÓN DEL CEREBRO ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("⚠️ Falta la API Key en la configuración.")
    st.stop()

# Modelo fijo (Gemma 2 es rápido y eficiente)
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

    # Función auxiliar para caracteres en español
    def limpio(texto):
        if not texto: return ""
        return texto.encode('latin-1', 'replace').decode('latin-1')

    # Encabezado
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

    # Consejo Final
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 12)
    pdf.multi_cell(0, 10, limpio(f"Consejo del Experto: {data_json.get('recomendacion_top', '')}"))

    return pdf.output(dest='S').encode('latin-1')

# --- 4. LÓGICA DE INTELIGENCIA ARTIFICIAL (ROBUSTA) ---
def analyze_tasks(tasks, role, model_name):
    try:
        model = genai.GenerativeModel(model_name)
        
        # Prompt diseñado para forzar formato JSON estricto
        prompt = f"""
        Actúa como un sistema experto de productividad (Coach Ejecutivo).
        Tu tarea es recibir una lista de tareas y clasificarlas en la Matriz de Eisenhower.
        
        Rol del usuario: "{role}"
        Lista de Tareas:
        {tasks}
        
        INSTRUCCIONES CRÍTICAS:
        1. Responde ÚNICAMENTE con un objeto JSON válido.
        2. NO escribas introducciones, ni conclusiones, ni texto fuera del JSON.
        3. Usa este esquema exacto:
        {{
            "hacer": ["lista de tareas urgentes e importantes"],
            "planificar": ["lista de tareas importantes no urgentes"],
            "delegar": ["lista de tareas urgentes no importantes"],
            "eliminar": ["lista de tareas ni urgentes ni importantes"],
            "recomendacion_top": "Un consejo estratégico breve de 2 líneas"
        }}
        """
        
        response = model.generate_content(prompt)
        text = response.text

        # --- FILTRO DE LIMPIEZA ---
        # 1. Eliminar marcadores de código si existen
        text = text.replace("```json", "").replace("```", "")
        
        # 2. Buscar quirúrgicamente dónde empieza '{' y termina '}'
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start != -1 and end != -1:
            clean_json_text = text[start:end]
            return json.loads(clean_json_text)
        else:
            # Intento desesperado si no encuentra llaves
            st.warning("El modelo no devolvió un formato estándar, intentando procesar...")
            return json.loads(text)

    except Exception as e:
        st.error(f"Error interpretando la respuesta del modelo: {e}")
        # Retorno de seguridad para que la app no explote
        return None

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🛡️ Priorizador de Tareas")
st.caption("Organiza tu día con Inteligencia Artificial.")
st.divider()

col_input1, col_input2 = st.columns([1, 3])
with col_input1:
    user_role = st.text_input("1. ¿Cuál es tu rol?", value="Coach Profesional")

tasks_input = st.text_area("2. Pega tu lista de tareas:", height=150, placeholder="Ejemplo:\nLlamar al cliente\nPagar cuentas\nEscribir informe")

if st.button("🚀 Priorizar mis tareas", type="primary", use_container_width=True):
    if not tasks_input:
        st.warning("⚠️ Por favor escribe algunas tareas.")
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
                
                col3, col4 = st.columns(2)
                with col3:
                    st.warning("🤝 DELEGAR")
                    for t in result.get("delegar", []): st.write(f"• {t}")
                with col4:
                    st.error("🗑️ ELIMINAR")
                    for t in result.get("eliminar", []): st.write(f"• {t}")
                
                st.divider()
                st.info(f"💡 **Consejo:** {result.get('recomendacion_top', '')}")
                
                # Botón de descarga
                try:
                    pdf_bytes = crear_pdf(result, user_role)
                    st.download_button(
                        label="📄 Descargar Reporte PDF",
                        data=pdf_bytes,
                        file_name="prioridades.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.warning(f"No se pudo generar el PDF: {e}")
