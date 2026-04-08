import asyncio
from langchain.tools import tool
from src.mcp_bridge import MCPBridge

# Instancia global del puente
mcp_bridge = MCPBridge()

# Función auxiliar para ejecutar código async en un entorno sincrónico (Streamlit)
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@tool
def tool_search_knowledge_base(query: str, n_results: int = 3) -> str:
    """
    Ejecuta una búsqueda semántica en la base de conocimiento de Bancolombia.
    ÚSALA SIEMPRE que el usuario pregunte por características, tasas, requisitos, seguros o créditos.
    """
    return run_async(mcp_bridge.call_tool("search_knowledge_base", {"query": query, "n_results": n_results}))

@tool
def tool_get_article_by_url(url: str) -> str:
    """
    Recupera el texto completo de un artículo específico usando su URL exacta de Bancolombia.
    """
    return run_async(mcp_bridge.call_tool("get_article_by_url", {"url": url}))

@tool
def tool_list_categories() -> str:
    """
    Retorna una lista estructurada con las categorías y productos disponibles.
    """
    return run_async(mcp_bridge.call_tool("list_categories", {}))

# Lista exportable para inyectar en el agente
bancolombia_tools = [tool_search_knowledge_base, tool_get_article_by_url, tool_list_categories]