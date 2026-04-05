# 🕸️ ScrapingBancolombia - Microservicio RAG

Este microservicio es el motor de ingesta y búsqueda para el sistema RAG (Retrieval-Augmented Generation) de productos de Bancolombia. 

Se encarga de navegar dinámicamente por la página web del banco, extraer la información de los productos, limpiarla (convirtiéndola a Markdown), segmentarla y guardarla como vectores en una base de datos ChromaDB para su posterior recuperación semántica.

## 🚀 Tecnologías Principales

* **Framework API:** FastAPI (Python)
* **Scraping:** Playwright (Asíncrono con emulación de navegador Chromium)
* **Procesamiento de Texto:** Markdownify y LangChain (RecursiveCharacterTextSplitter)
* **Embeddings:** Modelo `BAAI/bge-m3` (SentenceTransformers)
* **Base de Datos Vectorial:** ChromaDB
* **Contenerización:** Podman / Docker

---

## ⚙️ Variables de Entorno

El servicio está diseñado para ser configurado a través de variables de entorno. En el entorno de producción o al usar `docker-compose`, se pueden inyectar las siguientes variables:

| Variable | Descripción | Valor por Defecto |
| :--- | :--- | :--- |
| `MAX_PRODUCTOS_A_GUARDAR` | Límite máximo de páginas/productos a extraer por ejecución. Usa `-1` para extracción ilimitada. | `2` |
| `CHROMA_HOST` | Nombre del host o contenedor donde vive el servidor de ChromaDB. | `chromadb-server` |
| `CHROMA_PORT` | Puerto de conexión para el servidor de ChromaDB. | `8000` |

---

## 🏗️ Cómo ejecutar el proyecto (Vía Contenedores)

Este microservicio está diseñado para vivir dentro de un ecosistema orquestado. El archivo `docker-compose.yml` principal se encuentra en la **raíz del proyecto** (un nivel arriba de esta carpeta).

Para levantar toda la infraestructura (Base de datos + API de Scraping):

1. Abre tu terminal y ubícate en la raíz del repositorio (`rag-agent-bancolombia-tech-test`).
2. Ejecuta el orquestador usando Podman (o Docker):

```bash
podman compose up -d --build