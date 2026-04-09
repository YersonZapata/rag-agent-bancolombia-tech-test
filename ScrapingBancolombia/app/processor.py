import logging
from datetime import datetime
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
    
    #BAAI/bge-m3
    #multilingual-e5-small
    #intfloat/multilingual-e5-base
    #sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    nombre_modelo_embeddings = "intfloat/multilingual-e5-small"
    
    logger.info("Cargando modelo de embeddings {nombre_modelo_embeddings}...")
    lc_embeddings = HuggingFaceEmbeddings(model_name=nombre_modelo_embeddings)
    
    logger.info("Configurando SemanticChunker...")
    semantic_splitter = SemanticChunker(
        lc_embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=85.0
    )
    
    documents = []
    metadatas = []
    ids = []
    # Capturamos la fecha y hora de la ejecución actual en formato ISO 8601
    fecha_actualizacion = datetime.now().isoformat()
    

    logger.info("Generando chunks semánticos...")
    for prod in productos_extraidos:
        chunks = semantic_splitter.split_text(prod["contenido"])
        for i, chunk in enumerate(chunks):
            #
            chunk_optimizado = f"passage: {chunk}"
            documents.append(chunk_optimizado)
            #
            #documents.append(chunk)
            metadatas.append({
                "id_producto": prod["id"],
                "producto": prod["producto"],     
                "categoria": prod["categoria"],   
                "url": prod["url"],
                "chunk_index": i,
                "fecha_ultima_actualizacion": fecha_actualizacion,
                "modelo_embeddings": nombre_modelo_embeddings
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