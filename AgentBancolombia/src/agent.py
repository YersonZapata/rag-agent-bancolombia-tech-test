from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from src.tools import bancolombia_tools

def get_query_rewriter():
    """
    Crea una cadena (chain) que reformula la pregunta del usuario basándose en el historial.
    """
    llm_rewriter = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", temperature=0)
    
    system_prompt = """Dada la historia de la conversación y la nueva pregunta del usuario, 
    reformula la pregunta para que sea una consulta independiente (standalone query) que incluya 
    absolutamente todo el contexto necesario para buscar en una base de datos.
    
    EJEMPLO:
    Usuario: ¿Qué tarjetas de crédito tienen?
    Asistente: Tenemos la tarjeta clásica, oro y platinum.
    Usuario: ¿Cuáles son sus seguros?
    Tu respuesta: ¿Cuáles son los seguros que ofrecen las tarjetas de crédito clásica, oro y platinum de Bancolombia?
    
    REGLA: Si la pregunta actual ya es clara por sí sola o es un saludo, devuélvela exactamente igual.
    NO respondas a la pregunta, SOLO devuelve la pregunta reformulada."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ])
    
    # LCEL: Conectamos el prompt -> LLM -> Convertimos la salida a texto plano
    return prompt | llm_rewriter | StrOutputParser()

def build_bancolombia_agent():
    """
    Construye y retorna el agente de LangChain v1.2.15 utilizando Gemini y LangGraph.
    """
    # 1. Definir el LLM 
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite-preview", 
        temperature=0.2,
        max_retries=2 
    )
    
    # 2. Diseñar el Prompt del Sistema
    system_prompt = """
    Eres un asistente virtual amable, profesional y altamente capacitado del Grupo Bancolombia.
    Tu objetivo es ayudar a los usuarios con información precisa sobre productos y servicios del banco.
    
   REGLAS ESTRICTAS DE USO DE HERRAMIENTAS:
1. PREGUNTAS GENERALES/CATÁLOGO: Si el usuario pregunta "qué tipos de...", "qué clases de..." o pide listar opciones (ej. "¿Qué tarjetas tienen?"), DEBES llamar primero a la herramienta `list_categories`.
2. PREGUNTAS ESPECÍFICAS: Si el usuario menciona un producto concreto (ej. "requisitos de la tarjeta Mastercard Clásica" o "tasa del crédito hipotecario"), DEBES usar `search_knowledge_base`.
3. CITACIÓN DE FUENTES: ... (tu regla actual)
4. Si conoces la url de un producto, puedes usar 'get_article_by_url' para traer todo el articulo correspondiente
    """
    
    # 3. Crear el Agente
    # create_agent por defecto maneja el ciclo de pensamiento (ReAct) y la invocación de herramientas
    agent = create_agent(
        model=llm,
        tools=bancolombia_tools,
        system_prompt=system_prompt
    )
    
    return agent