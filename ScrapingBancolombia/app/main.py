import sys
import asyncio
import logging
import threading  # <-- LA LIBRERÍA SALVADORA
from fastapi import FastAPI
from pydantic import BaseModel

from app.scraper import ejecutar_scraping
from app.chroma_client import get_chroma_client, get_collection, reset_collection
from app.processor import procesar_y_guardar_productos

app = FastAPI(title="Bancolombia Scraper & VectorDB Service")
logger = logging.getLogger(__name__)

class SearchRequest(BaseModel):
    query: str
    limit: int = 3

def tarea_aislada():
    """
    Esta función se ejecutará en un hilo nativo de Windows,
    totalmente invisible y desconectado del motor asíncrono de FastAPI.
    """
    try:
        logger.info("=== INICIANDO PIPELINE EN HILO AISLADO ===")
        
        # 1. Política de Windows
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
        # 2. Creamos y asignamos el ciclo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 3. Ejecutamos el scraping
        productos = loop.run_until_complete(ejecutar_scraping())
        logger.info(f"✅ ¡Se encontraron y extrajeron {len(productos)} productos en total!")
        # 4. Cerramos el ciclo
        loop.close()
        
        # 5. Guardamos en DB
        client = get_chroma_client()
        collection = reset_collection(client)
        
        procesar_y_guardar_productos(productos, collection)
        logger.info("=== PIPELINE FINALIZADO CON ÉXITO ===")
    except Exception as e:
        logger.error(f"Error crítico en el pipeline: {str(e)}")

@app.post("/api/v1/trigger-pipeline")
async def trigger_pipeline():
    # En vez de BackgroundTasks, disparamos un Hilo Nativo
    hilo = threading.Thread(target=tarea_aislada)
    hilo.start()
    
    return {
        "status": "success", 
        "message": "Pipeline iniciado en batch, ve a los logs de la imagen para ver lo que esta sucediendo"
    }

@app.post("/api/v1/search")
async def search_products(request: SearchRequest):
    try:
        logger.info(f"Nueva búsqueda solicitada. Body recibido: {request.model_dump()}")
        
        client = get_chroma_client()
        collection = get_collection(client)
        
        results = collection.query(
            query_texts=[request.query],
            n_results=request.limit
        )
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Error en la búsqueda: {str(e)}")
        return {"status": "error", "message": str(e)}