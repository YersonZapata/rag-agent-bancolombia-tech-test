# Dockerfile para el Agente RAG + Servidor MCP (Ubicado en la raíz)
FROM python:3.10-slim

# Evitar escritura de bytecode y forzar log de salida estándar
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copiar requerimientos de ambos microservicios para aprovechar caché
COPY McpServerBancolombia/requirements.txt ./req_server.txt
COPY AgentBancolombia/requirements.txt ./req_agent.txt

# Instalar dependencias conjuntas
RUN pip install --no-cache-dir -r req_server.txt -r req_agent.txt

# Copiar el código fuente de ambos proyectos
COPY McpServerBancolombia/ ./McpServerBancolombia/
COPY AgentBancolombia/ ./AgentBancolombia/

# Inyectar la ruta en PYTHONPATH para que el puente MCP encuentre el servidor
ENV PYTHONPATH="/app/McpServerBancolombia:/app:${PYTHONPATH}"

# Exponer el puerto de Streamlit
EXPOSE 8501

# Comando para levantar la interfaz gráfica (que a su vez ejecutará el MCP por debajo)
CMD ["python", "-m", "streamlit", "run", "AgentBancolombia/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.fileWatcherType=none"]