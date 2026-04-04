import chromadb
from chromadb.utils import embedding_functions

def get_chroma_client(path="./chroma_data"):
    """Inicializa el cliente de ChromaDB persistente."""
    return chromadb.HttpClient(host='localhost', port=8000)

def get_collection(client, collection_name="productos_bancolombia"):
    """Solo obtiene la colección (ideal para buscar). No borra nada."""
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-m3"
    )
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef
    )

def reset_collection(client, collection_name="productos_bancolombia"):
    """Borra la colección y la recrea limpia (ideal para cuando hacemos scraping)."""
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
        
    return get_collection(client, collection_name)