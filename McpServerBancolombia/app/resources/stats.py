from app.chroma_client import get_chroma_collection

collection = get_chroma_collection()

def get_stats_data() -> str:
    """
    Obtiene las estadísticas de la base de conocimiento.
    """
    if collection is None:
        return "Error: La base de datos vectorial no está disponible."
    try:
        
        count = collection.count()
        results = collection.get(include=["metadatas"])
        categorias = set()
        modelos = set()
        fecha_actualizacion = set()

        for meta in results.get('metadatas', []):
            if meta and 'categoria' in meta:
                categorias.add(meta['categoria'])
            if 'modelo_embeddings' in meta:
                    modelos.add(meta['modelo_embeddings'])
            if 'fecha_ultima_actualizacion' in meta:
                    fecha_actualizacion.add(meta['fecha_ultima_actualizacion'])

        modelo_usado = list(modelos)[0] if modelos else "Desconocido"
        fecha_actualizacion = list(fecha_actualizacion)[0] if modelos else "Desconocido"
                
        stats = [
            f"Documentos (Chunks) indexados: {count}",
            f"Categorías disponibles: {len(categorias)}",
            f"Modelo de embeddings: {modelo_usado}",
            f"Fecha ultima actualización: {fecha_actualizacion}"
        ]
        return "\n".join(stats)
    except Exception as e:
        return f"Error recuperando estadísticas: {str(e)}"