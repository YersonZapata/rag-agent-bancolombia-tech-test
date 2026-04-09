import sys
import os
import logging
from fastmcp import FastMCP
os.environ["ANONYMIZED_TELEMETRY"] = "False"
# Evita que HuggingFace imprima barras de progreso en stdout
os.environ["TQDM_DISABLE"] = "1"
# Evita advertencias de paralelismo de tokenizers
os.environ["TOKENIZERS_PARALLELISM"] = "false" 

# Forzar el logging estrictamente a STDERR para no corromper el JSON de MCP
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # <- ESTO ES VITAL
)

# Importar las tools separadas
from app.tools.search import search_knowledge_base
from app.tools.article import get_article_by_url
from app.tools.categories import list_categories

# Importar la lógica del resource
from app.resources.stats import get_stats_data

from app.chroma_client import get_chroma_collection

mcp = FastMCP("BancolombiaRAGServer")

mcp.add_tool(search_knowledge_base)
mcp.add_tool(get_article_by_url)
mcp.add_tool(list_categories)

# Configura el logging básico de Python
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 1. Inicialización del servidor MCP
mcp = FastMCP("BancolombiaRAGServer")

# 2. Registro de Tools Obligatorias
# FastMCP leerá el nombre, los parámetros y los docstrings directamente de las funciones importadas
mcp.add_tool(search_knowledge_base)
mcp.add_tool(get_article_by_url)
mcp.add_tool(list_categories)

# 3. Registro del Resource 
@mcp.resource("knowledge-base://stats")
def stats_resource() -> str:
    """
    Expone estadísticas de la base de conocimiento: número de documentos indexados, categorías disponibles, fecha de última actualización, modelo de embeddings utilizado.
    """
    return get_stats_data()

# 4. Ejecución del servidor
if __name__ == "__main__":
    logging.info("Pre-calentando cliente de ChromaDB y modelo de embeddings...")
    get_chroma_collection()
    logging.info("Servidor MCP listo. Iniciando transporte stdio...")
    # Inicia el servidor usando stdio, tal como lo exige el requerimiento de transporte
    mcp.run()
    #mcp.run(transport="http", host="0.0.0.0", port=8005)