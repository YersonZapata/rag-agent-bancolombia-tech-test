from app.chroma_client import get_chroma_collection
import json
from typing import Annotated
from pydantic import Field



def search_knowledge_base(
    query: Annotated[str, Field(
        description="La pregunta o consulta del usuario en lenguaje natural. Debe ser específica sobre productos, servicios o beneficios de Bancolombia.",
        min_length=5
    )],
    n_results: Annotated[int, Field(
        description="Cantidad de documentos relevantes a recuperar. Útil para limitar o expandir el contexto.",
        ge=1, 
        le=5
    )] = 3
) -> str:
    """
    Ejecuta una búsqueda semántica en la base de conocimiento de Bancolombia.
    ÚSALA SIEMPRE que el usuario pregunte por características, tasas, requisitos, seguros, créditos o cualquier información de productos del banco. 
    Si no tienes mas información obten el articulo completo con la url y verifica la información solicitada por el usuario.
    """
    
    
    try:
        
        collection = get_chroma_collection()
        if collection is None:
            return "Error: La base de datos vectorial no está disponible."
        
        results = collection.query(query_texts=[query], n_results=n_results)
        
        if not results.get('documents') or not results['documents'][0]:
            return "No se encontraron resultados en la base de conocimiento para esta consulta."
            
        formatted_results = []
        for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
            url = meta.get('url', 'URL no disponible')
            
            
            producto = meta.get('producto','nombre no disponible')
            categoria = meta.get('categoria','categoria')
            item = {
                "producto": producto,
                "categoria":categoria,
                "url": url,
                "relevancia": round(dist, 4), # Redondeamos 
                "contenido": doc
            }
            formatted_results.append(item)
            
        return json.dumps({"result": formatted_results}, ensure_ascii=False)
    except Exception as e:
        return f"Error consultando la base vectorial: {str(e)}"