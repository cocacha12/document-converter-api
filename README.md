# Document Converter API

API simple para convertir documentos DOCX y PDF a Markdown usando MarkItDown de Microsoft.

## Características

- Conversión de documentos DOCX y PDF a Markdown
- Procesamiento asíncrono para archivos grandes
- Sistema de jobs con seguimiento de estado
- Limpieza automática de archivos temporales
- Monitoreo de memoria y recursos
- Webhooks para notificaciones
- Health checks
- Logging estructurado para producción
- Middleware de CORS configurable
- Manejo global de excepciones

## Deployment en Coolify

### Requisitos del Sistema

La aplicación requiere las siguientes dependencias del sistema que están incluidas en el Dockerfile:

- `libmagic-dev` - Detección de tipos de archivo
- `poppler-utils` - Procesamiento de PDFs
- `tesseract-ocr` - OCR para documentos escaneados
- `tesseract-ocr-spa` - Paquete de idioma español
- `tesseract-ocr-eng` - Paquete de idioma inglés
- `libreoffice` - Procesamiento de documentos Office
- `pandoc` - Conversión de documentos
- `qpdf` - Manipulación de PDFs

### Configuración en Coolify

1. **Crear nuevo proyecto en Coolify**
   - Selecciona "Docker Compose" como tipo de deployment
   - Conecta tu repositorio Git

2. **Variables de entorno requeridas:**
   ```env
   # Configuración básica
   PORT=8000
   HOST=0.0.0.0
   
   # Configuración de archivos
   MAX_FILE_SIZE=52428800
   LARGE_FILE_THRESHOLD=5242880
   CONVERSION_TIMEOUT=300
   CHUNK_SIZE=1000
   
   # Configuración de archivos temporales
   TEMP_FILES_DIR=./temp_files
   TEMP_FILES_RETENTION_HOURS=24
   MAX_TEMP_FILES=100
   
   # Configuración de logging para producción
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   
   # Configuración de CORS para producción
   ALLOWED_ORIGINS=*
   
   # Webhook opcional para notificaciones
   WEBHOOK_URL=https://tu-webhook-url.com/webhook
   ```

3. **Configuración de recursos recomendada:**
   - **CPU**: 1-2 cores
   - **RAM**: 1-2 GB (mínimo 512MB)
   - **Almacenamiento**: 5-10 GB
   - **Timeout**: 300 segundos (para archivos grandes)

4. **Health Check:**
   - **Path**: `/health`
   - **Port**: 8000
   - **Interval**: 30s
   - **Timeout**: 10s
   - **Retries**: 3

### Archivos de Configuración

El proyecto incluye:

- `Dockerfile` - Imagen optimizada para producción con todas las dependencias
- `docker-compose.yml` - Configuración para desarrollo y testing
- `.env.example` - Plantilla de variables de entorno
- `requirements.txt` - Dependencias de Python

### Monitoreo y Logs

La aplicación incluye:

- **Logging estructurado**: JSON en producción, formato legible en desarrollo
- **Middleware de logging**: Registra todas las requests y responses
- **Manejo global de excepciones**: Captura y registra todos los errores
- **Métricas del sistema**: Endpoint `/system/stats` para monitoreo
- **Health checks**: Endpoint `/health` con verificaciones extendidas

### Endpoints de Monitoreo

- `GET /health` - Health check básico
- `GET /health?extended=true` - Health check extendido con limpieza
- `GET /system/stats` - Estadísticas del sistema y jobs
- `GET /jobs` - Lista de jobs activos

## Instalación Local

1. Clona el repositorio
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Configura las variables de entorno:
   ```bash
   cp .env.example .env
   ```
4. Ejecuta la aplicación:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Uso

### Endpoints principales

- `POST /convert` - Convierte un documento
- `POST /convert-and-save` - Convierte y guarda para descarga posterior
- `GET /status/{job_id}` - Consulta el estado de un job
- `GET /result/{job_id}` - Obtiene el resultado de la conversión
- `GET /download/{job_id}` - Descarga el archivo convertido
- `DELETE /jobs/{job_id}` - Elimina un job
- `GET /jobs` - Lista todos los jobs
- `GET /health` - Health check
- `GET /system/stats` - Estadísticas del sistema

### Ejemplo de uso

```bash
# Conversión directa
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@documento.pdf"

# Conversión con guardado
curl -X POST "http://localhost:8000/convert-and-save" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@documento.pdf" \
  -F "format=markdown"
```

## Docker

Puedes ejecutar la aplicación usando Docker:

```bash
docker build -t document-converter .
docker run -p 8000:8000 document-converter
```

O usando docker-compose:

```bash
docker-compose up
```

## Troubleshooting

### Problemas Comunes

1. **Error de memoria**: Ajusta `MAX_MEMORY_USAGE` y `LARGE_FILE_THRESHOLD`
2. **Timeouts**: Incrementa `CONVERSION_TIMEOUT`
3. **Archivos temporales**: Verifica permisos en `TEMP_FILES_DIR`
4. **Dependencias del sistema**: Asegúrate de que el Dockerfile incluye todas las dependencias

### Logs de Debug

Para habilitar logs de debug:
```env
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

## Formatos soportados

- **PDF**: Archivos PDF estándar
- **DOCX**: Documentos de Microsoft Word

## Limitaciones

- Tamaño máximo de archivo: 10MB
- Solo archivos DOCX y PDF
- Sin autenticación (API pública)
- Sin persistencia de datos

## Estructura del proyecto

```
.
├── app/
│   ├── __init__.py
│   └── main.py          # Lógica principal de la API
├── venv/                # Entorno virtual
├── main.py              # Punto de entrada
├── requirements.txt     # Dependencias
└── README.md           # Este archivo
```

## Dependencias principales

- **FastAPI**: Framework web moderno y rápido
- **MarkItDown**: Librería de Microsoft para conversión a Markdown
- **Uvicorn**: Servidor ASGI para FastAPI
- **python-multipart**: Para manejo de archivos multipart

## Desarrollo

Para desarrollo, la API se ejecuta con recarga automática:

```bash
python main.py
```

O usando uvicorn directamente:

```bash
uvicorn app.main:app --reload
```

## Ejemplos de uso

### Con Python requests

```python
import requests

url = "http://localhost:8000/convert"
files = {'file': open('documento.pdf', 'rb')}

response = requests.post(url, files=files)
result = response.json()

print(result['markdown_content'])
```

### Con JavaScript/Fetch

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/convert', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log(data.markdown_content);
});
```

## Manejo de errores

La API devuelve códigos de estado HTTP apropiados:

- **200**: Conversión exitosa
- **400**: Error en la validación del archivo
- **413**: Archivo demasiado grande
- **500**: Error interno del servidor

## Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.