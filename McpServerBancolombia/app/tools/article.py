from app.chroma_client import get_chroma_collection
from typing import Annotated
from pydantic import Field



def get_article_by_url(
    url: Annotated[str, Field(
        description="La URL completa del artículo o producto de Bancolombia. Debe iniciar obligatoriamente con 'https://www.bancolombia.com/personas'.",
        pattern=r"^https://www\.bancolombia\.com/personas.*$"
    )]
) -> str:
    """
    Recupera el texto completo de un producto/categoria específico usando su URL exacta.
    ÚSALA SOLO cuando el usuario te pida más detalles sobre un producto específico cuya URL ya conoces (por ejemplo, tras usar search_knowledge_base) y necesites leer todo su contenido, o cuando el usuario te entregue la url.
    """

    try:

        collection = get_chroma_collection()
        if collection is None:
            return "Error: La base de datos vectorial no está disponible."
   
        results = collection.get(where={"url": url})
        
        if not results.get('documents') or len(results['documents']) == 0:
            return f"No se encontró ningún artículo indexado con la URL: {url}"
            
        return results['documents'][0]
    
    except Exception as e:
        return f"Error al recuperar el artículo por URL: {str(e)}"