FROM python:3.10-slim

# Evitar que Python escriba archivos .pyc y forzar el log de salida estándar (sin buffer)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MAX_PRODUCTOS_A_GUARDAR=-1

WORKDIR /app

# Instalar dependencias del sistema necesarias para Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Instalar los navegadores de Playwright y sus dependencias de SO
RUN playwright install chromium
RUN playwright install-deps chromium

# Copiar el código fuente
COPY ./app /app/app

# Exponer el puerto de FastAPI
EXPOSE 8001

# Comando para iniciar el servidor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]