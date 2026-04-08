from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from src.tools import bancolombia_tools

def get_query_rewriter():
    """
    Crea una cadena (chain) que reformula la pregunta del usuario basándose en el historial.
    """
    llm_rewriter = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
    
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
    Construye y retorna el agente de LangChain v1.x utilizando Gemini y LangGraph.
    """
    # 1. Definir el LLM 
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest", 
        temperature=0.2,
        max_retries=2 
    )
    
    # 2. Diseñar el Prompt del Sistema
    system_prompt = """
    Eres un asistente virtual amable, profesional y altamente capacitado del Grupo Bancolombia.
    Tu objetivo es ayudar a los usuarios con información precisa sobre productos y servicios del banco.
    
    REGLAS ESTRICTAS:
    1. DEBES basar tus respuestas en la información obtenida a través de tus herramientas (base de conocimiento).
    2. NUNCA inventes información, tasas, ni requisitos. Si la base de conocimiento no tiene la respuesta, indica cortésmente que no dispones de esa información en este momento.
    3. CITACIÓN DE FUENTES: Al final de cada respuesta que use información de la base de conocimiento, DEBES incluir una sección llamada "Fuentes consultadas:" listando las URLs utilizadas.
    4. FUERA DE ALCANCE: Si el usuario pregunta por temas no relacionados con Bancolombia, servicios financieros o soporte general, responde educadamente que tu alcance se limita a productos y servicios del Grupo Bancolombia y no puedes responder esa pregunta.
    """
    
    # 3. Crear el Agente (Nuevo estándar)
    # create_agent por defecto maneja el ciclo de pensamiento (ReAct) y la invocación de herramientas
    agent = create_agent(
        model=llm,
        tools=bancolombia_tools,
        system_prompt=system_prompt
    )
    
    return agent