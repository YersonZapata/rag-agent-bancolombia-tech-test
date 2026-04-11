# 🔌 McpServerBancolombia - Servidor de Conocimiento (MCP)

Este microservicio actúa como la capa de acceso a datos e interoperabilidad del sistema RAG. Utiliza el estándar **Model Context Protocol (MCP)** para exponer de forma estandarizada, segura y descriptiva las herramientas de consulta (Tools) y los metadatos (Resources) de la base de conocimiento vectorial (ChromaDB) hacia el Agente LLM.

---

## 📐 ¿Qué es MCP y por qué se utiliza?

El **Model Context Protocol (MCP)** es un estándar abierto desarrollado por Anthropic que estandariza cómo los modelos de IA acceden a fuentes de datos externas. 

En lugar de que el Agente de LangChain tenga la lógica de la base de datos acoplada en su código, el Agente simplemente "descubre" las herramientas que este servidor MCP le ofrece. 
Para este proyecto, se implementó el **transporte `stdio` (Standard I/O)**. Esto significa que el servidor no expone puertos HTTP al exterior, sino que se ejecuta como un subproceso seguro y encapsulado invocado directamente por el Agente, enviando mensajes JSON-RPC a través de la consola.

---

## 📂 Estructura de Archivos y Responsabilidades

El código está estructurado siguiendo el principio de Responsabilidad Única (SRP):

* **`main.py`**: Es el orquestador y punto de entrada. Utiliza el framework `FastMCP` para registrar las herramientas (Tools) y los recursos (Resources) y levantar el servidor.
* **`chroma_client.py`**: Administra la conexión de bajo nivel con la base de datos vectorial ChromaDB y carga el modelo de embeddings (`intfloat/multilingual-e5-small`).
* **`/tools/`**: Directorio que agrupa las capacidades transaccionales del servidor:
    * `search.py`: Motor de búsqueda semántica.
    * `article.py`: Extractor de documentos exactos por URL.
    * `categories.py`: Agrupador y explorador del catálogo.
* **`/resources/`**: Directorio para datos de solo lectura.
    * `stats.py`: Expone la salud y metadatos del índice vectorial.

---

## 🛠️ Capacidades Expuestas (Tools)

Las siguientes herramientas son expuestas automáticamente al LLM, incluyendo sus descripciones (Docstrings) y validaciones de esquema (JSON Schema derivadas de Pydantic):

### 1. `search_knowledge_base`
* **Propósito:** Realiza búsquedas semánticas (Vector Search) para encontrar los fragmentos de texto más relevantes a la pregunta del usuario.
* **Parámetros:** * `query` (str): La pregunta en lenguaje natural.
    * `n_results` (int, 1-5): Número de resultados a retornar (Default: 3).
    * `categoria` (str): Para mayor presición el modelo puede hacer filtro por categoría y encontrar los chunks referentes a esa categoría
    * `producto` (str): Para mayor presición el modelo puede hacer filtro por producto y encontrar los chunks referentes a esa 
* **Retorno:** JSON con producto, categoría, URL, nivel de relevancia (distancia) y el fragmento del documento.

### 2. `get_article_by_url`
* **Propósito:** Recupera el texto íntegro de un producto mediante filtrado exacto de metadatos (Where clause). Ideal cuando el LLM necesita profundizar en un producto que ya encontró previamente.
* **Validación:** Exige estrictamente que la URL cumpla con el patrón RegEx `^https://www\.bancolombia\.com/personas.*$`.

### 3. `list_categories`
* **Propósito:** Permite al LLM "explorar" el catálogo disponible antes de buscar. Recorre todos los metadatos de la base de datos y utiliza diccionarios de conjuntos (`defaultdict(set)`) para agrupar dinámicamente los productos por categoría, eliminando duplicados.

---

## 📊 Recursos Expuestos (Resources)

A diferencia de las Tools (que ejecutan acciones basadas en parámetros), los Resources son URIs estáticas que el Agente puede leer para obtener contexto del sistema:

* **URI:** `knowledge-base://stats`
* **Descripción:** Retorna una radiografía técnica del clúster vectorial: cantidad de "chunks" indexados, modelo de embeddings activo, categorías totales y la fecha de la última ingesta de datos.

---

## 🧠 Decisiones Clave de Arquitectura

1.  **Patrón Singleton para la Conexión de BD (`chroma_client.py`):** Se implementaron variables globales (`_client`, `_collection`) para garantizar que la conexión HTTP a ChromaDB y, especialmente, **la carga del modelo de embeddings en memoria**, ocurran una única vez en el ciclo de vida del proceso. Esto reduce a cero la latencia de inicialización en cada invocación de una Tool.
2.  **Framework FastMCP:**
    Se seleccionó `FastMCP` sobre la implementación manual de `mcp.server` por su integración nativa con los tipos de Python. FastMCP lee los Type Hints (`Annotated`, `Field` de Pydantic) y los Docstrings de las funciones y genera automáticamente los esquemas de herramientas para el LLM.
3.  **Filtrado Híbrido Estructural:**
    El sistema no solo depende de la búsqueda semántica probabilística (distancia de vectores), sino que expone capacidades de búsqueda determinista (`get_article_by_url` vía metadatos) para evitar alucinaciones cuando se requiere información exacta.
4.  **Manejo de Errores Desacoplado:**
    En lugar de permitir que las excepciones de conexión rompan el subproceso `stdio`, los bloques `try-except` capturan los errores de infraestructura y devuelven cadenas de texto (Ej: *"Error: La base de datos vectorial no está disponible"*). Esto permite que el sistema "falle con gracia" y el Agente superior pueda reaccionar e informar al usuario adecuadamente.


## 🚀 Ejecución

Si solo se desea probar el servidor mcp es necesario se puede ejecutar el siguiente comando

```bash
npx @modelcontextprotocol/inspector python -m app.main
```