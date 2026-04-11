import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from src.agent import build_bancolombia_agent, get_query_rewriter

from langchain_core.globals import set_debug
set_debug(True)

st.set_page_config(page_title="Asistente Bancolombia RAG", page_icon="🏦", layout="centered")
st.title("🏦 Asistente Virtual Bancolombia")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
@st.cache_resource
def get_agent_and_rewriter():
    return build_bancolombia_agent(), get_query_rewriter()

agent_app, rewriter = get_agent_and_rewriter()

for msg in st.session_state.chat_history:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.write(msg.content)

user_input = st.chat_input("¿En qué te puedo ayudar hoy?")

if user_input:
    # 1. Mostramos el mensaje original del usuario en la pantalla
    with st.chat_message("user"):
        st.write(user_input)
        
    with st.chat_message("assistant"):
        # --- FASE 1: QUERY REWRITING ---
        with st.spinner("Analizando contexto..."):
            if len(st.session_state.chat_history) > 0:
                # Si hay historia, reescribimos la pregunta
                standalone_query = rewriter.invoke({
                    "chat_history": st.session_state.chat_history,
                    "question": user_input
                })
                # Opcional: Mostrar que el sistema es inteligente
                st.caption(f"*(Búsqueda contextualizada: {standalone_query})*")
            else:
                standalone_query = user_input

        # Creamos una lista temporal de mensajes para el agente
        # usando la pregunta REESCRITA como el último mensaje humano
        messages_for_agent = st.session_state.chat_history.copy()
        messages_for_agent.append(HumanMessage(content=standalone_query))

        # --- FASE 2: EJECUCIÓN DEL AGENTE ---
        with st.spinner("Consultando la base de conocimiento..."):
            try:
                response = agent_app.invoke({"messages": messages_for_agent})
                
                # Extraemos y limpiamos el texto de Gemini
                raw_content = response["messages"][-1].content
                if isinstance(raw_content, list):
                    output_text = "".join(
                        block["text"] for block in raw_content 
                        if isinstance(block, dict) and "text" in block
                    )
                else:
                    output_text = str(raw_content)

                st.write(output_text)
                
                # --- ACTUALIZACIÓN DE MEMORIA ---
                # Guardamos la pregunta ORIGINAL del usuario (para que el chat se vea natural)
                # y la respuesta del bot en la memoria de la sesión
                st.session_state.chat_history.append(HumanMessage(content=user_input))
                st.session_state.chat_history.append(AIMessage(content=output_text))
                
            except Exception as e:
                error_msg = str(e)
                
                # 1. Manejo del error 429 (Límite de cuota / Rate Limit)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    st.warning("⏳ **Límite de consultas alcanzado.** La API gratuita se encuentra saturada en este momento. Por favor, espera aproximadamente **1 minuto** e intenta de nuevo.")
                
                # 2. Manejo de error de conexión con el Servidor MCP (ChromaDB apagado, etc.)
                elif "Connection refused" in error_msg or "stdio" in error_msg:
                    st.error("🔌 **Error de conexión con la Base de Conocimiento.** Asegúrate de que el servidor vectorial (ChromaDB) esté en ejecución.")
                
                # 3. Cualquier otro error inesperado
                else:
                    st.error(f"Ocurrió un error inesperado, intenta nuevamente: {error_msg}")