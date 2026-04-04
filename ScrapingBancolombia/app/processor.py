import logging
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

def procesar_y_guardar_productos(productos_extraidos, collection):
    """
    Recibe la lista de diccionarios en memoria, hace el chunking 
    y guarda en ChromaDB de forma directa.
    """
    if not productos_extraidos:
        logger.warning("No hay productos para procesar.")
        return

    logger.info("Cargando modelo de embeddings BAAI/bge-m3...")
    lc_embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    
    logger.info("Configurando SemanticChunker...")
    semantic_splitter = SemanticChunker(
        lc_embeddings,
        breakpoint_threshold_type="percentile" 
    )
    
    documents = []
    metadatas = []
    ids = []
    
    logger.info("Generando chunks semánticos...")
    for prod in productos_extraidos:
        chunks = semantic_splitter.split_text(prod["contenido"])
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({
                "id_producto": prod["id"],
                "titulo": prod["titulo"],
                "url": prod["url"],
                "chunk_index": i
            })
            ids.append(f"prod_{prod['id']}_chunk_{i}")
            
    logger.info(f"Se generaron {len(documents)} chunks en total.")
    
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info("Datos persistidos exitosamente en ChromaDB.")
    else:
        logger.warning("No se generaron chunks válidos.")