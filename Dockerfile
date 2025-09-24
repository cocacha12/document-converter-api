# Dockerfile para API de conversión de documentos
# Usando Alpine Linux con Python para mayor estabilidad

FROM python:3.9-alpine

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear usuario no-root para seguridad
RUN addgroup -g 1001 -S appuser && adduser -u 1001 -S appuser -G appuser

# Instalar dependencias del sistema requeridas por MarkItDown
RUN apk update && apk add --no-cache \
    # Dependencias básicas
    curl \
    wget \
    # Dependencias para MarkItDown
    file-dev \
    poppler-utils \
    tesseract-ocr \
    qpdf \
    # Dependencias adicionales para procesamiento de documentos
    libreoffice \
    pandoc \
    # Dependencias de compilación
    gcc \
    musl-dev \
    linux-headers

# Crear directorio de trabajo
WORKDIR /app

# Crear directorio para archivos temporales
RUN mkdir -p /app/temp_files && chown -R appuser:appuser /app

# Copiar requirements.txt primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY app/ ./app/
COPY .env.example .env

# Cambiar propietario de archivos
RUN chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8000

# Health check - usar PORT dinámico de Coolify
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Comando por defecto - usar PORT de Coolify si está disponible (formato JSON)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]