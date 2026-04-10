import os
import logging
import chromadb
from chromadb.utils import embedding_functions

# Variables globales para el patrón Singleton
_client = None
_collection = None

def get_chroma_collection():
    """
    Inicializa (si no existe) y retorna la colección de ChromaDB.
    """
    global _client, _collection
    
    # Si la colección ya está en memoria, la devolvemos sin hacer nada más
    if _collection is not None:
        return _collection
        
    logging.info("Inicializando conexión única a ChromaDB...")
    
    try:
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        
        # 1. Creamos el cliente
        _client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        
        # 2. Obtenemos la colección real
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="intfloat/multilingual-e5-small"
        )
        collection_name = os.getenv("CHROMA_COLLECTION", "productos_bancolombia")
        _collection = _client.get_collection(name=collection_name,embedding_function=ef)
        
        logging.info("Colección cargada exitosamente.")
        return _collection
        
    except Exception as e:
        logging.critical(f"Error crítico conectando a ChromaDB: {str(e)}")
        raise e # Falla si no arranca la db