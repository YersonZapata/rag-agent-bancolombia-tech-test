from app.chroma_client import get_chroma_collection
import json
from typing import Annotated, Optional
from pydantic import Field



def search_knowledge_base(
    query: Annotated[str, Field(
        description="La pregunta o consulta del usuario en lenguaje natural. Debe ser específica caracteristicas o beneficios de un producto un servicio o una Categoría",
        min_length=5
    )],
    n_results: Annotated[int, Field(
        description="Cantidad de documentos relevantes a recuperar. Útil para limitar o expandir el contexto.",
        ge=1, 
        le=5
    )] = 3,
    categoria: Annotated[Optional[str], Field(
        description="Opcional. Categoría exacta para filtrar la búsqueda. Usa list_categories primero para saber cuáles existen y usa el texto EXACTO de la Categoría."
    )] = None,
    producto: Annotated[Optional[str], Field(
        description="Opcional. Nombre exacto del producto para filtrar (ej: 'Tarjeta de Crédito Black'). Extrae este valor usando list_categories primero."
    )] = None
) -> str:
    """
    Ejecuta una búsqueda semántica en la base de conocimiento de Bancolombia.
    ÚSALA SIEMPRE que necesites detalles profundos sobre un producto ESPECÍFICO (características, tasas, requisitos, beneficios).
    REGLA DE EXCLUSIÓN: NO uses esta herramienta si el usuario hace una pregunta general como "¿Qué tipos de tarjetas tienen?" o "¿Cuáles son sus créditos?". Para esos casos de exploración, usa SIEMPRE la herramienta 'list_categories' primero.
    """
    
    
    try:
        
        collection = get_chroma_collection()
        if collection is None:
            return "Error: La base de datos vectorial no está disponible."
        #
        query_optimizada = f"query: {query}"
        search_kwargs = {
        "query_texts": [query_optimizada],
        "n_results": n_results
        }
        filtros = []
        if categoria:
            filtros.append({"categoria": categoria})
        if producto:
            filtros.append({"producto": producto})
        if len(filtros) == 1:
            search_kwargs["where"] = filtros[0]
        elif len(filtros) > 1:
            search_kwargs["where"] = {"$and": filtros}
        
        results = collection.query(**search_kwargs)
        #results = collection.query(query_texts=[query_optimizada], n_results=n_results)
        #
        #results = collection.query(query_texts=[query], n_results=n_results)
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