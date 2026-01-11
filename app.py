import streamlit as st

# --- LÓGICA DE PRIORIZACIÓN (Eisenhower) ---
# NOTA: No incluimos 'st.set_page_config' ni estilos CSS aquí, 
# porque el archivo 'Inicio.py' ya se encarga de todo eso.

st.header("⚖️ Priorizador de Tareas (Matriz de Eisenhower)")
st.markdown("**Herramienta para decidir qué tareas hacer ahora y cuáles planificar o eliminar.**")
st.divider()

# --- 1. INGRESAR TAREA ---
col1, col2 = st.columns([2, 1])

with col1:
    tarea = st.text_input("📝 Describe la tarea:", placeholder="Ej: Responder correo urgente del cliente...")

with col2:
    st.write("**Evaluación:**")
    c_imp, c_urg = st.columns(2)
    es_importante = c_imp.checkbox("¿Es Importante?", help="¿Te acerca a tus objetivos a largo plazo?")
    es_urgente = c_urg.checkbox("¿Es Urgente?", help="¿Requiere atención inmediata o tiene fecha límite ya?")

# --- 2. LOGICA DE DECISIÓN ---
st.divider()

if not tarea:
    st.info("👆 Ingresa una tarea arriba para ver qué debes hacer con ella.")

else:
    st.subheader("💡 Acción Recomendada")
    
    # Cuadrante 1: Importante + Urgente
    if es_importante and es_urgente:
        st.error("🔥 ¡HAZLO YA! (Cuadrante 1)")
        st.markdown(f"La tarea **'{tarea}'** es una crisis o problema inminente.")
        st.write("👉 **Consejo:** No lo pienses, ejecútalo ahora mismo para apagar el fuego.")

    # Cuadrante 2: Importante + NO Urgente
    elif es_importante and not es_urgente:
        st.info("📅 PLANIFÍCALO (Cuadrante 2)")
        st.markdown(f"La tarea **'{tarea}'** es estratégica para tu crecimiento.")
        st.write("👉 **Consejo:** Ponle fecha y hora en tu calendario. Aquí es donde debes pasar la mayor parte de tu tiempo.")

    # Cuadrante 3: NO Importante + Urgente
    elif not es_importante and es_urgente:
        st.warning("👥 DELÉGALO (Cuadrante 3)")
        st.markdown(f"La tarea **'{tarea}'** es una interrupción disfrazada de trabajo.")
        st.write("👉 **Consejo:** ¿Puede hacerlo alguien más? Si no tienes equipo, hazlo rápido para quitártelo de encima, pero no le dediques mucha energía.")

    # Cuadrante 4: NO Importante + NO Urgente
    else:
        st.success("🗑️ ELIMÍNALO (Cuadrante 4)")
        st.markdown(f"La tarea **'{tarea}'** es probablemente una distracción.")
        st.write("👉 **Consejo:** ¿Qué pasa si no lo haces? Si la respuesta es 'nada', bórralo de tu lista.")

# --- 3. EXPLICACIÓN EDUCATIVA ---
with st.expander("📚 Ver explicación detallada de los 4 Cuadrantes"):
    st.markdown("""
    * **Cuadrante 1 (Hacer):** Crisis, problemas acuciantes, proyectos con fecha límite hoy.
    * **Cuadrante 2 (Planificar):** Prevención, construcción de relaciones, búsqueda de nuevas oportunidades, planificación. **(Es el cuadrante del Liderazgo).**
    * **Cuadrante 3 (Delegar):** Interrupciones, algunas llamadas, correos, reuniones irrelevantes para ti pero urgentes para otros.
    * **Cuadrante 4 (Eliminar):** Trivialidades, ajetreo inútil, ladrones de tiempo (redes sociales, correos spam).
    """)
