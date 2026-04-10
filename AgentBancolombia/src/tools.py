from langchain.tools import tool
from src.mcp_bridge import PersistentMCPBridge

# Esto inicializa el servidor la PRIMERA vez que se carga el archivo.
# En las siguientes llamadas, reutilizará la conexión abierta.
bridge = PersistentMCPBridge()

@tool
def tool_search_knowledge_base(query: str, n_results: int = 3) -> str:
    """
    Ejecuta una búsqueda semántica en la base de conocimiento de Bancolombia.
    ÚSALA SIEMPRE que necesites detalles profundos sobre un producto ESPECÍFICO.
    """
    return bridge.call_tool_sync("search_knowledge_base", {"query": query, "n_results": n_results})

@tool
def tool_get_article_by_url(url: str) -> str:
    """
    Recupera el texto completo de un artículo específico usando su URL exacta de Bancolombia.
    """
    return bridge.call_tool_sync("get_article_by_url", {"url": url})

@tool
def tool_list_categories() -> str:
    """
    Retorna una lista estructurada con las categorías y productos disponibles.
    """
    return bridge.call_tool_sync("list_categories", {})

# Lista exportable para inyectar en el agente
bancolombia_tools = [tool_search_knowledge_base, tool_get_article_by_url, tool_list_categories]