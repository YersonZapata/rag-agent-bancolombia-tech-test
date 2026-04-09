import os
import chromadb
from chromadb.utils import embedding_functions

def get_chroma_client(path="./chroma_data"):
    """Inicializa el cliente de ChromaDB persistente."""

    # Si no encuentra la variable, usará 'localhost' por defecto
    chroma_host = os.getenv("CHROMA_HOST", "localhost")

    # Leemos el puerto y lo convertimos a entero (por defecto 8000)
    chroma_port = int(os.getenv("CHROMA_PORT", "8000"))

    return chromadb.HttpClient(host=chroma_host, port=chroma_port)

def get_collection(client, collection_name="productos_bancolombia"):
    """Solo obtiene la colección (ideal para buscar)."""
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="intfloat/multilingual-e5-small"
    )
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef
    )

def reset_collection(client, collection_name="productos_bancolombia"):
    """Borra la colección y la recrea limpia"""
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
        
    return get_collection(client, collection_name)