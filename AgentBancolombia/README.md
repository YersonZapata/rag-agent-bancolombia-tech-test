# 🏦 AgentBancolombia - Asistente Conversacional RAG

Este módulo representa la capa de interacción y orquestación de Inteligencia Artificial del sistema RAG (Retrieval-Augmented Generation) para el Grupo Bancolombia. 

Actúa como el cerebro del sistema, interactuando con el usuario final a través de una interfaz gráfica, manteniendo el contexto de la conversación, y decidiendo de forma autónoma cuándo y cómo consultar la base de conocimiento utilizando el protocolo MCP (Model Context Protocol).

---

## ⚙️ Arquitectura del Sistema

El Agente está diseñado bajo el patrón **ReAct (Reason + Act)** y utiliza una arquitectura orientada a grafos (LangGraph) para el manejo del estado conversacional. Está estrictamente desacoplado de la base de datos vectorial; su única forma de acceder a los datos de los productos bancarios es a través de un puente MCP.

### Componentes Principales:
1. **Frontend (UI):** Interfaz construida en Streamlit que maneja la memoria a corto plazo (Session State) y renderiza la conversación.
2. **Query Rewriter:** Un pipeline previo al agente que toma el historial de la conversación y reformula consultas ambiguas en consultas independientes (Standalone Queries) para maximizar la precisión semántica.
3. **Agente Enrutador:** Motor impulsado por Gemini que evalúa la intención del usuario y orquesta la invocación de herramientas.
4. **MCP Bridge (`mcp_bridge.py`):** Un adaptador de infraestructura que gestiona el ciclo de vida de la comunicación con el `McpServerBancolombia` utilizando el transporte `stdio`.

---

## 🛠️ Tecnologías Utilizadas

* **Orquestación IA:** LangChain / LangGraph
* **LLM Core:** Google Gemini (`gemini-3.1-flash-lite-preview`) vía `langchain-google-genai`
* **Protocolo de Integración:** Model Context Protocol (MCP SDK oficial de Anthropic)
* **Frontend:** Streamlit
* **Gestión de Entorno:** Python 3.11, dependencias asíncronas (`asyncio`)

---

## 🧠 Flujo de Ejecución (Cómo Funciona)

1. **Ingreso del Usuario:** El usuario envía un mensaje (ej. *"¿Cuáles son sus seguros?"*).
2. **Reescritura Contextual:** Si hay historial previo (ej. el usuario preguntaba antes por tarjetas de crédito), el `Query Rewriter` transforma la pregunta a *"¿Cuáles son los seguros asociados a las tarjetas de crédito de Bancolombia?"*.
3. **Razonamiento (ReAct):** El Agente LLM analiza el System Prompt y la pregunta reformulada, decidiendo que necesita información externa. Formula un JSON con la llamada a la herramienta `search_knowledge_base`.
4. **Ejecución MCP:** El `MCPBridge` intercepta la solicitud, levanta un subproceso aislado del servidor MCP mediante la salida estándar (`stdio`), ejecuta la consulta en la base de datos vectorial (ChromaDB) y recupera los fragmentos de texto.
5. **Síntesis y Respuesta:** El Agente recibe el contexto crudo, redacta una respuesta amigable, natural y veraz, adjunta las fuentes consultadas y actualiza el historial en la interfaz de Streamlit.

---

## 📐 Decisiones Clave de Arquitectura

Para esta prueba técnica, se tomaron decisiones orientadas a la resiliencia, escalabilidad y buenas prácticas de la industria:

* **Desacoplamiento Estricto (MCP):** El agente LangChain no importa ni conoce la existencia de ChromaDB. Esto permite que el día de mañana el `McpServerBancolombia` pueda conectarse a otra base de datos vectorial sin modificar una sola línea de código en este agente.
* **Conversational Query Rewriting:** Se implementó una capa de reformulación de consultas para evitar la degradación del vector de búsqueda (Vector Search Drift). Esto soluciona el problema clásico de los sistemas RAG donde el contexto se pierde en preguntas de seguimiento como por ejemplo pregutar `Cuales son los seguros de esta tarjeta?`.
* **Manejo de Errores y Rate Limiting:** Se implementó un control de excepciones avanzado en la UI que intercepta y traduce fallos técnicos (como la caída de la base de datos `Connection Refused` o el límite de cuota del LLM `429 RESOURCE_EXHAUSTED`) en mensajes amigables para el usuario.


---

## 🚀 Ejecución

Dado el acoplamiento en tiempo de ejecución del transporte `stdio`, este módulo está diseñado para ser levantado desde la **raíz del monorepo**. 

* **Para desarrollo local:** Levante la chromadb en loca y ejecute el siguiente comando.

```bash
python -u -m streamlit run AgentBancolombia/app.py --server.fileWatcherType none
```

* **Para producción:** El agente se encuentra empacado junto a su servidor MCP en el contenedor unificado configurado en el `Dockerfile` principal, orquestado a través de `docker-compose`.

entrar a http://localhost:8501/ para interactuar con el chat