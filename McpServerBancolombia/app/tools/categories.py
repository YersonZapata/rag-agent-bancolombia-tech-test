from app.chroma_client import get_chroma_collection
from collections import defaultdict

def list_categories() -> str:
    """
    Retorna una lista estructurada con las categorías y los productos específicos disponibles para cada categoría disponible en Bancolombia.
    ÚSALA cuando el usuario haga preguntas exploratorias como '¿Qué tipo de productos ofrecen?', '¿Cuáles son las categorías?' o cuando necesites entender el portafolio de servicios del banco antes de hacer una búsqueda más profunda.
    """
    try:
        collection = get_chroma_collection()
        if collection is None:
            return "Error: La base de datos vectorial no está disponible."
    
        results = collection.get(include=["metadatas"])
        
        # Usamos un diccionario donde cada llave es una categoría y su valor es un set de productos (para evitar duplicados)
        catalogo = defaultdict(set)
        
        for meta in results.get('metadatas', []):
            if meta and 'categoria' in meta:
                categoria = meta['categoria']
                # Si el documento tiene la llave 'producto', la usamos; si no, ponemos un valor por defecto
                producto = meta.get('producto', 'Producto general/Sin especificar')
                catalogo[categoria].add(producto)
                
        if not catalogo:
            return "No hay categorías registradas en los metadatos de los documentos actuales."
            
        # Formateamos la salida para que sea muy legible para el LLM
        respuesta = [f"Se encontraron {len(catalogo)} categorías disponibles en el portafolio:"]
        
        # Ordenamos alfabéticamente para mayor limpieza
        for categoria, productos in sorted(catalogo.items()):
            respuesta.append(f"\nCategoría: {categoria}")
            for producto in sorted(productos):
                respuesta.append(f"   - {producto}")
                
        return "\n".join(respuesta)
        
    except Exception as e:
        return f"Error recuperando las categorías y productos: {str(e)}"