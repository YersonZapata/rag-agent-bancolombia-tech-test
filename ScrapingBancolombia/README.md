# 🕸️ ScrapingBancolombia - Microservicio RAG

Este microservicio es el motor de ingesta y búsqueda para el sistema RAG (Retrieval-Augmented Generation) de productos de Bancolombia. 

Se encarga de navegar dinámicamente por la página web del banco, extraer la información de los productos, limpiarla (convirtiéndola a Markdown), segmentarla y guardarla como vectores en una base de datos ChromaDB para su posterior recuperación semántica.

## 🚀 Tecnologías Principales

* **Framework API:** FastAPI (Python)
* **Scraping:** Playwright (Asíncrono con emulación de navegador Chromium)
* **Procesamiento de Texto:** Markdownify y LangChain (SemanticChunker para segmentación basada en contexto)
* **Embeddings:** Modelo `BAAI/bge-m3` (SentenceTransformers), usado por ... ["COMPLETAR"]
* **Base de Datos Vectorial:** ChromaDB, por defecto la colección se llama "productos_bancolombia"
* **Contenerización:** Podman / Docker

---

## ⚙️ Variables de Entorno

El servicio está diseñado para ser configurado a través de variables de entorno. En el entorno de producción o al usar `docker-compose`, se pueden inyectar las siguientes variables:

| Variable | Descripción | Valor por Defecto |
| :--- | :--- | :--- |
| `MAX_PRODUCTOS_A_GUARDAR` | Límite máximo de productos a extraer por ejecución. Usa `-1` para extracción ilimitada, el scraping solo navega el menu de productos y servicios de la pagina de Bancolombia, el scraping dura aproximadamente 10 min, pero el embedding puede durar mas de 30 min dependiendo de la maquina| `-1` |
| `CHROMA_HOST` | Nombre del host o contenedor donde vive el servidor de ChromaDB. | `chromadb-server` |
| `CHROMA_PORT` | Puerto de conexión para el servidor de ChromaDB. | `8000` |

CHROMA_HOST y CHROMA_PORT no son obligatorios si se usa la db que se levanta de manera local
---

## 🏗️ Cómo ejecutar el proyecto (Vía Contenedores)
Este microservicio está diseñado para vivir dentro de un ecosistema orquestado. El archivo `docker-compose.yml` principal se encuentra en la **raíz del proyecto** (un nivel arriba de esta carpeta).

Para levantar toda la infraestructura (Base de datos + API de Scraping):

1. Abre tu terminal y ubícate en la raíz del repositorio (`rag-agent-bancolombia-tech-test`).
2. Ejecuta el orquestador usando Podman (o Docker):

```bash
podman compose up -d --build
```
3. Para levantar solo el proyecto del scraping es necesario tener la chromadb arriba en el puerto 8000 ejecutar el siguiente comando para levantar el servicio en el puerto 8001 

```bash
uvicorn app.main:app --port 8001 --reload
```


## 🔌 Endpoints Disponibles

El microservicio expone los siguientes endpoints para interactuar con el motor de ingesta y búsqueda:

### 1. Iniciar Ingesta
`POST localhost:8001/api/v1/trigger-pipeline`

Dispara el proceso de scraping y guardado en la base de datos vectorial de forma asíncrona.
*   **Funcionamiento:** Ejecuta el pipeline de scraping en segundo plano.
*   **Logs:** Para monitorear el progreso detallado, es necesario entrar a la consola del pod/contenedor y visualizarlos en tiempo real.
*   **Cuerpo (Body):** No requiere parámetros.

### 2. Búsqueda Rápida (Pruebas)
`POST localhost:8001/api/v1/search`

Permite realizar consultas semánticas directas sobre **ChromaDB** para validar que la información se haya indexado correctamente.

*   **Cuerpo (JSON):**
```json
{
  "query": "cuales son las caracteristicas del seguro de vida mas",
  "limit": 3
}

para navegar dentro de los datos de la chromadb en local usar 

```bash
chroma browse productos_bancolombia --local
```

## 💾 Precarga de Datos (Backup de Embeddings)

Dado que el proceso de scraping y embedding puede ser lento o fallar por cambios estructurales en la web de Bancolombia, se ha incluido una copia de seguridad de los datos procesados que puede cargarse directamente en ChromaDB.

Sigue estos pasos para restaurar el backup:

**1. Copiar el contenido del backup al contenedor:**
```bash
podman cp "tu_ruta_local\chroma_backup\data\." chromadb-server:/data
```
**2. Asignar permisos sobre la ruta:**
```bash
podman exec -it chromadb-server chmod -R 777 /data
```
**3. Reiniciar el contenedor:**
```bash
podman restart chromadb-server
```

Si tienes instalado Chroma en tu sistema, puedes verificar los datos cargados ejecutando:

```bash
chroma browse productos_bancolombia --local
```