from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import http_exception_handler
import time
from markitdown import MarkItDown
import tempfile
import os
from typing import Dict, Any, Optional, List
import uuid
import asyncio
from datetime import datetime, timedelta
import psutil
from enum import Enum
import shutil
from pathlib import Path
import re
import structlog
import sys
import zipfile
import json
from io import BytesIO
try:
    import magic
except ImportError:
    magic = None

# Configurar structlog para producción
def configure_logging():
    """Configurar logging estructurado para producción"""
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Mapear niveles de log
    level_mapping = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    }
    
    log_level_num = level_mapping.get(log_level, 20)  # Default INFO
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if is_production:
        # Producción: JSON estructurado
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Desarrollo: formato legible
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level_num),
        logger_factory=structlog.WriteLoggerFactory(sys.stdout),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

# Configurar logging al inicio
configure_logging()

logger = structlog.get_logger(__name__)

# Enums y clases para manejo de jobs
class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class OutputFormat(str, Enum):
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    GOOGLE_DOCS = "google_docs"

class ConversionJob:
    def __init__(self, job_id: str, filename: str, file_size: int, output_format: OutputFormat = OutputFormat.MARKDOWN):
        self.job_id = job_id
        self.filename = filename
        self.file_size = file_size
        self.output_format = output_format
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress = 0
        self.result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.memory_usage: Optional[float] = None
        self.temp_file_path: Optional[str] = None
        self.download_url: Optional[str] = None

# Almacén en memoria para jobs (en producción usar Redis o base de datos)
jobs_store: Dict[str, ConversionJob] = {}

# Crear instancia de FastAPI
app = FastAPI(
    title="Document Converter API",
    description="API simple para convertir documentos DOCX y PDF a Markdown usando MarkItDown",
    version="2.0.0"
)

# Configurar CORS para producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Middleware de logging para requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requests y responses"""
    start_time = time.time()
    
    # Log de request entrante
    logger.info(
        "Request iniciado",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log de response exitoso
        logger.info(
            "Request completado",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
            client_ip=request.client.host if request.client else "unknown"
        )
        
        # Agregar header de tiempo de procesamiento
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        
        # Log de error
        logger.error(
            "Request falló",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time_ms=round(process_time * 1000, 2),
            client_ip=request.client.host if request.client else "unknown",
            exc_info=True
        )
        raise

# Manejador global de excepciones HTTP
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Manejador personalizado para excepciones HTTP con logging"""
    logger.warning(
        "HTTP Exception",
        method=request.method,
        url=str(request.url),
        status_code=exc.status_code,
        detail=exc.detail,
        client_ip=request.client.host if request.client else "unknown"
    )
    return await http_exception_handler(request, exc)

# Manejador global de excepciones no controladas
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejador global para excepciones no controladas"""
    logger.error(
        "Excepción no controlada",
        method=request.method,
        url=str(request.url),
        error=str(exc),
        error_type=type(exc).__name__,
        client_ip=request.client.host if request.client else "unknown",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "error_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat()
        }
    )

# Inicializar MarkItDown
md_converter = MarkItDown()

# Configuraciones
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB por defecto
LARGE_FILE_THRESHOLD = int(os.getenv("LARGE_FILE_THRESHOLD", 5 * 1024 * 1024))  # 5MB
MAX_MEMORY_USAGE = int(os.getenv("MAX_MEMORY_USAGE", 500 * 1024 * 1024))  # 500MB
CONVERSION_TIMEOUT = int(os.getenv("CONVERSION_TIMEOUT", 300))  # 5 minutos
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))  # Líneas por chunk

# Configuraciones para archivos temporales
TEMP_FILES_DIR = os.getenv("TEMP_FILES_DIR", "./temp_files")
TEMP_FILES_RETENTION_HOURS = int(os.getenv("TEMP_FILES_RETENTION_HOURS", 24))  # 24 horas
MAX_TEMP_FILES = int(os.getenv("MAX_TEMP_FILES", 100))  # Máximo 100 archivos temporales
WEBHOOK_URL = os.getenv("WEBHOOK_URL", None)  # URL para webhooks n8n

# Crear directorio de archivos temporales si no existe
Path(TEMP_FILES_DIR).mkdir(parents=True, exist_ok=True)

# Nuevas clases para manejo de títulos y archivos
class TitleInfo:
    def __init__(self, extracted_title: str, custom_title: Optional[str] = None, 
                 confidence: float = 0.0, fallback_used: bool = False, 
                 extraction_method: str = "content"):
        self.extracted_title = extracted_title
        self.custom_title = custom_title
        self.confidence = confidence
        self.fallback_used = fallback_used
        self.extraction_method = extraction_method

class FileInfo:
    def __init__(self, filename: str, file_size: int, file_type: str, 
                 order_index: int = 0, is_from_zip: bool = False):
        self.id = str(uuid.uuid4())
        self.filename = filename
        self.file_size = file_size
        self.file_type = file_type
        self.order_index = order_index
        self.is_from_zip = is_from_zip
        self.title_info: Optional[TitleInfo] = None

# Almacén para conexiones WebSocket
websocket_connections: Dict[str, WebSocket] = {}

# Funciones para extracción de títulos
def extract_title_from_content(content: str, filename: str) -> TitleInfo:
    """Extrae el título de un documento basado en su contenido"""
    lines = content.strip().split('\n')
    
    # Buscar primer encabezado H1
    for line in lines[:20]:  # Revisar solo las primeras 20 líneas
        line = line.strip()
        if line.startswith('# '):
            title = line[2:].strip()
            if title:
                return TitleInfo(
                    extracted_title=title,
                    confidence=0.9,
                    fallback_used=False,
                    extraction_method="header"
                )
    
    # Buscar primer párrafo no vacío que parezca un título
    for line in lines[:10]:
        line = line.strip()
        if line and len(line) < 100 and not line.startswith(('*', '-', '>', '|')):
            # Verificar si parece un título (no muy largo, sin caracteres especiales)
            if not re.search(r'[.!?]$', line) and len(line.split()) <= 10:
                return TitleInfo(
                    extracted_title=line,
                    confidence=0.7,
                    fallback_used=False,
                    extraction_method="content"
                )
    
    # Fallback: usar nombre del archivo
    title = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
    return TitleInfo(
        extracted_title=title,
        confidence=0.5,
        fallback_used=True,
        extraction_method="filename"
    )

def validate_zip_file(file_content: bytes) -> bool:
    """Valida si el contenido es un archivo ZIP válido"""
    try:
        with zipfile.ZipFile(BytesIO(file_content), 'r') as zip_file:
            # Verificar que el ZIP no esté corrupto
            zip_file.testzip()
            return True
    except (zipfile.BadZipFile, zipfile.LargeZipFile):
        return False

def extract_files_from_zip(file_content: bytes) -> List[Dict[str, Any]]:
    """Extrae archivos DOCX y PDF de un archivo ZIP"""
    extracted_files = []
    
    try:
        with zipfile.ZipFile(BytesIO(file_content), 'r') as zip_file:
            for file_info in zip_file.filelist:
                # Saltar directorios
                if file_info.is_dir():
                    continue
                
                filename = file_info.filename
                file_extension = os.path.splitext(filename)[1].lower()
                
                # Solo procesar archivos DOCX y PDF
                if file_extension in ALLOWED_EXTENSIONS:
                    try:
                        file_data = zip_file.read(file_info)
                        extracted_files.append({
                            "filename": os.path.basename(filename),
                            "content": file_data,
                            "size": len(file_data),
                            "type": file_extension[1:],  # Remover el punto
                            "original_path": filename
                        })
                    except Exception as e:
                        logger.warning(f"Error extrayendo {filename}: {str(e)}")
                        continue
    
    except Exception as e:
        logger.error(f"Error procesando archivo ZIP: {str(e)}")
        raise HTTPException(status_code=400, detail="Error procesando archivo ZIP")
    
    return extracted_files

async def send_websocket_update(job_id: str, message: Dict[str, Any]) -> None:
    """Envía actualización por WebSocket si hay conexión activa"""
    if job_id in websocket_connections:
        try:
            json_message = json.dumps(message)
            logger.info(f"📡 Sending WebSocket message: {json_message[:500]}...", job_id=job_id)
            await websocket_connections[job_id].send_text(json_message)
        except Exception as e:
            logger.warning(f"Error enviando WebSocket update para job {job_id}: {str(e)}")
            # Remover conexión si hay error
            websocket_connections.pop(job_id, None)
    else:
        logger.warning(f"No WebSocket connection found for job {job_id}")


def validate_file(file: UploadFile) -> None:
    """Validar el archivo subido"""
    # Verificar extensión
    file_extension = os.path.splitext(file.filename or "")[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado. Solo se permiten: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Verificar que el archivo tenga contenido
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No se proporcionó un archivo válido"
        )

def get_memory_usage() -> float:
    """Obtener uso actual de memoria en bytes"""
    process = psutil.Process()
    return process.memory_info().rss

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Dividir texto en chunks por líneas"""
    lines = text.split('\n')
    chunks = []
    for i in range(0, len(lines), chunk_size):
        chunk = '\n'.join(lines[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def sanitize_filename(filename: str) -> str:
    """Sanitizar nombre de archivo para uso seguro"""
    # Remover extensión y caracteres no seguros
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name)
    return name.strip('-')

def format_content_for_output(content: str, output_format: OutputFormat) -> str:
    """Formatear contenido según el formato de salida especificado"""
    if output_format == OutputFormat.PLAIN_TEXT:
        # Remover markdown y mantener solo texto plano
        text = re.sub(r'#{1,6}\s+', '', content)  # Remover headers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remover bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # Remover italic
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Remover links
        text = re.sub(r'`([^`]+)`', r'\1', text)  # Remover code
        return text
    elif output_format == OutputFormat.GOOGLE_DOCS:
        # Formato optimizado para Google Docs
        content = content.replace('# ', '')
        content = content.replace('## ', '')
        content = content.replace('### ', '')
        content = content.replace('**', '')
        content = content.replace('*', '')
        return content
    else:
        # Mantener markdown original
        return content

def save_temp_file(content: str, job_id: str, original_filename: str, output_format: OutputFormat) -> str:
    """Guardar contenido en archivo temporal y retornar la ruta"""
    # Determinar extensión según formato
    extension = ".md" if output_format == OutputFormat.MARKDOWN else ".txt"
    
    # Crear nombre de archivo seguro
    safe_name = sanitize_filename(original_filename)
    temp_filename = f"{job_id}_{safe_name}{extension}"
    temp_file_path = os.path.join(TEMP_FILES_DIR, temp_filename)
    
    # Formatear contenido
    formatted_content = format_content_for_output(content, output_format)
    
    # Guardar archivo
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        f.write(formatted_content)
    
    return temp_file_path

def cleanup_old_temp_files() -> int:
    """Limpiar archivos temporales antiguos y retornar cantidad eliminada"""
    if not os.path.exists(TEMP_FILES_DIR):
        try:
            os.makedirs(TEMP_FILES_DIR, exist_ok=True)
            logger.info(f"Directorio temporal creado: {TEMP_FILES_DIR}")
        except OSError as e:
            logger.error(f"Error creando directorio temporal: {e}")
            return 0
        return 0
    
    cutoff_time = datetime.now() - timedelta(hours=TEMP_FILES_RETENTION_HOURS)
    deleted_count = 0
    failed_count = 0
    
    try:
        files = os.listdir(TEMP_FILES_DIR)
        logger.debug(f"Revisando {len(files)} archivos en directorio temporal")
        
        for filename in files:
            file_path = os.path.join(TEMP_FILES_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_mtime < cutoff_time:
                        os.unlink(file_path)
                        deleted_count += 1
                        logger.debug(f"Archivo temporal eliminado: {filename}")
            except (OSError, IOError) as e:
                failed_count += 1
                logger.warning(f"Error eliminando archivo temporal {filename}: {e}")
            except Exception as e:
                failed_count += 1
                logger.error(f"Error inesperado eliminando {filename}: {e}")
    
    except OSError as e:
        logger.error(f"Error accediendo al directorio temporal: {e}")
        return 0
    
    if deleted_count > 0 or failed_count > 0:
        logger.info(f"Limpieza temporal completada: {deleted_count} eliminados, {failed_count} fallos")
    
    return deleted_count

def get_file_extension_for_format(output_format: OutputFormat) -> str:
    """Obtener extensión de archivo según formato de salida"""
    return ".md" if output_format == OutputFormat.MARKDOWN else ".txt"

async def send_webhook(webhook_url: str, data: Dict[str, Any]) -> None:
    """Enviar webhook con los datos de conversión"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=data, timeout=30)
            logger.info(f"Webhook enviado a {webhook_url}, status: {response.status_code}")
    except Exception as e:
        logger.error(f"Error enviando webhook a {webhook_url}: {str(e)}")

async def process_conversion_async(job: ConversionJob, file_content: bytes, temp_file_path: str) -> None:
    """Procesar conversión de forma asíncrona"""
    try:
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now()
        job.progress = 10
        
        # Enviar actualización inicial
        await send_websocket_update(job.job_id, {
            "type": "progress",
            "status": "processing",
            "progress": 10,
            "message": "Iniciando conversión de documento"
        })
        
        # Monitorear memoria antes de la conversión
        initial_memory = get_memory_usage()
        job.memory_usage = initial_memory
        
        # Verificar límites de memoria
        if initial_memory > MAX_MEMORY_USAGE:
            raise Exception(f"Uso de memoria excesivo: {initial_memory / (1024*1024):.2f}MB")
        
        job.progress = 30
        await send_websocket_update(job.job_id, {
            "type": "progress",
            "status": "processing",
            "progress": 30,
            "message": "Verificando memoria y preparando conversión"
        })
        
        # Realizar conversión con timeout
        logger.info(f"Iniciando conversión asíncrona para job {job.job_id}")
        
        # Simular progreso durante la conversión
        await asyncio.sleep(0.1)  # Permitir que otros procesos corran
        job.progress = 50
        await send_websocket_update(job.job_id, {
            "type": "progress",
            "status": "processing",
            "progress": 50,
            "message": "Convirtiendo documento a markdown"
        })
        
        result = md_converter.convert(temp_file_path)
        job.progress = 80
        await send_websocket_update(job.job_id, {
            "type": "progress",
            "status": "processing",
            "progress": 80,
            "message": "Procesando contenido convertido"
        })
        
        # Verificar memoria después de la conversión
        final_memory = get_memory_usage()
        job.memory_usage = final_memory
        
        # Preparar resultado
        markdown_content = result.text_content
        
        # Si el contenido es muy grande, dividirlo en chunks
        chunks = chunk_text(markdown_content) if len(markdown_content) > 10000 else [markdown_content]
        
        # Guardar archivo temporal
        temp_file_path_saved = save_temp_file(markdown_content, job.job_id, job.filename, job.output_format)
        job.temp_file_path = temp_file_path_saved
        job.download_url = f"/download/{job.job_id}"
        
        job.result = {
            "success": True,
            "filename": job.filename,
            "file_size": job.file_size,
            "markdown_content": markdown_content,
            "chunks": chunks,
            "total_chunks": len(chunks),
            "temp_file_saved": True,
            "download_url": job.download_url,
            "output_format": job.output_format,
            "metadata": {
                "original_filename": job.filename,
                "content_length": len(markdown_content),
                "memory_used_mb": final_memory / (1024*1024),
                "processing_time_seconds": (datetime.now() - job.started_at).total_seconds(),
                "temp_file_extension": get_file_extension_for_format(job.output_format)
            }
        }
        
        job.progress = 100
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now()
        
        logger.info(f"🎯 Job {job.job_id} marked as COMPLETED, sending WebSocket update")
        
        # Enviar actualización final por WebSocket con resultado
        await send_websocket_update(job.job_id, {
            "type": "status_update",
            "status": "completed",
            "progress": 100,
            "message": "Conversión completada exitosamente",
            "result": {
                "success": True,
                "job_id": job.job_id,
                "filename": job.filename,
                "download_url": f"/download/{job.job_id}",
                "format": job.output_format.value,
                "processing_time": (datetime.now() - job.started_at).total_seconds(),
                "content_preview": markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content
            }
        })
        
        logger.info(f"📡 WebSocket completion message sent for job {job.job_id}")
        
        # Enviar webhook si está configurado
        if WEBHOOK_URL:
            webhook_data = {
                "job_id": job.job_id,
                "status": "completed",
                "download_url": f"/download/{job.job_id}",
                "output_format": job.output_format.value,
                "filename": job.filename,
                "completed_at": job.completed_at.isoformat()
            }
            await send_webhook(WEBHOOK_URL, webhook_data)
        
        logger.info(f"Conversión completada para job {job.job_id}")
        
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.now()
        
        # Enviar actualización de error por WebSocket
        await send_websocket_update(job.job_id, {
            "type": "error",
            "status": "failed",
            "progress": 0,
            "message": f"Error en conversión: {str(e)}",
            "error": str(e)
        })
        
        # Enviar webhook de error si está configurado
        if WEBHOOK_URL:
            webhook_data = {
                "job_id": job.job_id,
                "status": "failed",
                "error": str(e),
                "filename": job.filename,
                "completed_at": job.completed_at.isoformat()
            }
            await send_webhook(WEBHOOK_URL, webhook_data)
        
        logger.error(f"Error en conversión asíncrona para job {job.job_id}: {str(e)}")
    
    finally:
        # Limpiar archivo temporal de forma robusta
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.debug(f"Archivo temporal de procesamiento eliminado: {temp_file_path}")
        except (OSError, IOError) as e:
            logger.warning(f"Error eliminando archivo temporal {temp_file_path}: {e}")
        except Exception as e:
            logger.error(f"Error inesperado eliminando archivo temporal {temp_file_path}: {e}")


@app.post("/convert-and-save")
async def convert_and_save_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    output_format: OutputFormat = OutputFormat.MARKDOWN,
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """Convertir documento y guardar automáticamente como archivo temporal"""
    try:
        # Validar archivo
        validate_file(file)
        
        # Leer contenido del archivo
        file_content = await file.read()
        
        # Verificar tamaño del archivo
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"El archivo es demasiado grande. Tamaño máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Limpiar archivos antiguos antes de procesar
        cleanup_old_temp_files()
        
        # Crear job ID único
        job_id = str(uuid.uuid4())
        
        # Crear archivo temporal para procesamiento
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or "")[1]) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # Crear job
        job = ConversionJob(job_id, file.filename or "unknown", len(file_content), output_format)
        jobs_store[job_id] = job
        
        # Determinar si usar procesamiento asíncrono
        if len(file_content) > LARGE_FILE_THRESHOLD:
            # Archivo grande - procesamiento asíncrono
            background_tasks.add_task(process_conversion_async, job, file_content, temp_file_path)
            
            return {
                "job_id": job_id,
                "status": "processing",
                "message": "Archivo grande detectado. Procesamiento en segundo plano iniciado.",
                "filename": file.filename,
                "file_size": len(file_content),
                "output_format": output_format,
                "estimated_time_minutes": max(1, len(file_content) // (1024 * 1024)),
                "check_status_url": f"/status/{job_id}",
                "download_url_when_ready": f"/download/{job_id}",
                "webhook_url": webhook_url
            }
        else:
            # Archivo pequeño - procesamiento inmediato
            try:
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.now()
                
                # Convertir usando MarkItDown
                logger.info(f"Convirtiendo y guardando archivo: {file.filename}")
                result = md_converter.convert(temp_file_path)
                content = result.text_content
                
                # Guardar archivo temporal (siempre en este endpoint)
                temp_file_path_saved = save_temp_file(content, job_id, file.filename or "unknown", output_format)
                job.temp_file_path = temp_file_path_saved
                job.download_url = f"/download/{job_id}"
                
                # Preparar respuesta
                response_data = {
                    "success": True,
                    "job_id": job_id,
                    "filename": file.filename,
                    "file_size": len(file_content),
                    "output_format": output_format,
                    "download_url": job.download_url,
                    "temp_file_saved": True,
                    "content_preview": content[:500] + "..." if len(content) > 500 else content,
                    "metadata": {
                        "original_filename": file.filename,
                        "file_type": os.path.splitext(file.filename or "")[1].lower(),
                        "content_length": len(content),
                        "processing_type": "immediate",
                        "temp_file_extension": get_file_extension_for_format(output_format),
                        "temp_file_path": os.path.basename(temp_file_path_saved)
                    }
                }
                
                # Actualizar job como completado
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                job.result = response_data
                
                # Enviar webhook si se proporciona
                if webhook_url:
                    background_tasks.add_task(send_webhook, webhook_url, response_data)
                
                logger.info(f"Conversión y guardado exitoso para: {file.filename}")
                return response_data
                
            finally:
                # Limpiar archivo temporal de procesamiento de forma robusta
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                        logger.debug(f"Archivo temporal de procesamiento eliminado: {temp_file_path}")
                except (OSError, IOError) as e:
                    logger.warning(f"Error eliminando archivo temporal {temp_file_path}: {e}")
                except Exception as e:
                    logger.error(f"Error inesperado eliminando archivo temporal {temp_file_path}: {e}")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al convertir y guardar archivo {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor al procesar el archivo: {str(e)}"
        )

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Endpoint de verificación de salud"""
    return {
        "status": "healthy",
        "message": "Document Converter API está funcionando correctamente"
    }

@app.get("/download/{job_id}")
async def download_file(job_id: str):
    """Descargar archivo convertido por job_id"""
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    job = jobs_store[job_id]
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job no completado")
    
    if not job.temp_file_path or not Path(job.temp_file_path).exists():
        raise HTTPException(status_code=404, detail="Archivo temporal no encontrado")
    
    # Determinar tipo de contenido
    content_type = "text/markdown" if job.output_format == OutputFormat.MARKDOWN else "text/plain"
    
    # Obtener nombre del archivo original y crear nombre de descarga
    original_name = job.filename
    base_name = Path(original_name).stem
    extension = get_file_extension_for_format(job.output_format)
    download_filename = f"{base_name}_converted{extension}"
    
    return FileResponse(
        path=job.temp_file_path,
        media_type=content_type,
        filename=download_filename
    )


@app.post("/convert")
async def convert_document(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    format: str = "text",
    save_temp: bool = False
) -> Dict[str, Any]:
    """Convertir documento DOCX o PDF a Markdown"""
    try:
        # Validar archivo
        validate_file(file)
        
        # Leer contenido del archivo
        file_content = await file.read()
        
        # Verificar tamaño del archivo
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"El archivo es demasiado grande. Tamaño máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Crear job ID único
        job_id = str(uuid.uuid4())
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or "")[1]) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # Determinar formato de salida
        output_format = OutputFormat.PLAIN_TEXT if format.lower() == "text" else OutputFormat.MARKDOWN
        
        # Crear job
        job = ConversionJob(job_id, file.filename or "unknown", len(file_content), output_format)
        jobs_store[job_id] = job
        
        # Determinar si usar procesamiento asíncrono
        if len(file_content) > LARGE_FILE_THRESHOLD:
            # Archivo grande - procesamiento asíncrono
            background_tasks.add_task(process_conversion_async, job, file_content, temp_file_path)
            
            return {
                "job_id": job_id,
                "status": "processing",
                "message": "Archivo grande detectado. Procesamiento en segundo plano iniciado.",
                "filename": file.filename,
                "file_size": len(file_content),
                "estimated_time_minutes": max(1, len(file_content) // (1024 * 1024)),  # Estimación básica
                "check_status_url": f"/status/{job_id}"
            }
        else:
            # Archivo pequeño - procesamiento inmediato
            try:
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.now()
                
                # Convertir usando MarkItDown
                logger.info(f"Convirtiendo archivo pequeño: {file.filename}")
                result = md_converter.convert(temp_file_path)
                
                # Preparar respuesta inmediata
                content = result.text_content
                
                # Guardar archivo temporal si se solicita o si el formato es texto
                temp_file_saved = False
                download_url = None
                if save_temp or format.lower() == "text":
                    temp_file_path_saved = save_temp_file(content, job_id, file.filename or "unknown", output_format)
                    job.temp_file_path = temp_file_path_saved
                    job.download_url = f"/download/{job_id}"
                    temp_file_saved = True
                    download_url = job.download_url
                
                response_data = {
                    "success": True,
                    "job_id": job_id,
                    "filename": file.filename,
                    "file_size": len(file_content),
                    "content": format_content_for_output(content, output_format),
                    "format": format,
                    "output_format": output_format,
                    "temp_file_saved": temp_file_saved,
                    "download_url": download_url,
                    "metadata": {
                        "original_filename": file.filename,
                        "file_type": os.path.splitext(file.filename or "")[1].lower(),
                        "content_length": len(content),
                        "processing_type": "immediate",
                        "temp_file_extension": get_file_extension_for_format(output_format) if temp_file_saved else None
                    }
                }
                
                # Actualizar job como completado
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                job.result = response_data
                
                logger.info(f"Conversión inmediata exitosa para: {file.filename}")
                return response_data
                
            finally:
                # Limpiar archivo temporal para archivos pequeños de forma robusta
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                        logger.debug(f"Archivo temporal eliminado: {temp_file_path}")
                except (OSError, IOError) as e:
                    logger.warning(f"Error eliminando archivo temporal {temp_file_path}: {e}")
                except Exception as e:
                    logger.error(f"Error inesperado eliminando archivo temporal {temp_file_path}: {e}")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al convertir archivo {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor al procesar el archivo: {str(e)}"
        )


@app.get("/status/{job_id}")
async def get_job_status(job_id: str) -> Dict[str, Any]:
    """Obtener el estado de un job de conversión"""
    if job_id not in jobs_store:
        raise HTTPException(
            status_code=404,
            detail="Job no encontrado"
        )
    
    job = jobs_store[job_id]
    
    response = {
        "job_id": job.job_id,
        "status": job.status,
        "filename": job.filename,
        "file_size": job.file_size,
        "progress": job.progress,
        "created_at": job.created_at.isoformat(),
        "memory_usage_mb": job.memory_usage / (1024*1024) if job.memory_usage else None
    }
    
    if job.started_at:
        response["started_at"] = job.started_at.isoformat()
    
    if job.completed_at:
        response["completed_at"] = job.completed_at.isoformat()
        response["processing_time_seconds"] = (job.completed_at - job.started_at).total_seconds() if job.started_at else None
    
    if job.status == JobStatus.FAILED and job.error_message:
        response["error_message"] = job.error_message
    
    if job.status == JobStatus.COMPLETED and job.result:
        response["result"] = job.result
    
    return response

@app.get("/result/{job_id}")
async def get_job_result(job_id: str, chunk: Optional[int] = None) -> Dict[str, Any]:
    """Obtener el resultado de un job completado, opcionalmente por chunks"""
    logger.info(f"🔍 GET /result/{job_id} - Fetching job result")
    
    if job_id not in jobs_store:
        logger.error(f"❌ Job {job_id} not found in jobs_store. Available jobs: {list(jobs_store.keys())}")
        raise HTTPException(
            status_code=404,
            detail="Job no encontrado"
        )
    
    job = jobs_store[job_id]
    logger.info(f"📊 Job {job_id} status: {job.status}, has_result: {job.result is not None}")
    
    if job.status != JobStatus.COMPLETED:
        logger.error(f"❌ Job {job_id} not completed. Current status: {job.status}")
        raise HTTPException(
            status_code=400,
            detail=f"Job no completado. Estado actual: {job.status}"
        )
    
    if not job.result:
        logger.error(f"❌ Job {job_id} completed but no result available")
        raise HTTPException(
            status_code=500,
            detail="Resultado no disponible"
        )
    
    # Si se solicita un chunk específico
    if chunk is not None:
        chunks = job.result.get("chunks", [])
        if chunk < 0 or chunk >= len(chunks):
            logger.error(f"❌ Invalid chunk {chunk} for job {job_id}. Available: 0-{len(chunks)-1}")
            raise HTTPException(
                status_code=400,
                detail=f"Chunk inválido. Disponibles: 0-{len(chunks)-1}"
            )
        
        logger.info(f"✅ Returning chunk {chunk} for job {job_id}")
        return {
            "job_id": job_id,
            "chunk_index": chunk,
            "total_chunks": len(chunks),
            "chunk_content": chunks[chunk],
            "metadata": job.result.get("metadata", {})
        }
    
    # Retornar resultado completo
    logger.info(f"✅ Returning complete result for job {job_id}")
    return job.result

@app.get("/jobs")
async def list_jobs(status: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Listar jobs con filtros opcionales"""
    jobs_list = []
    
    for job in jobs_store.values():
        if status and job.status != status:
            continue
            
        job_info = {
            "job_id": job.job_id,
            "filename": job.filename,
            "status": job.status,
            "progress": job.progress,
            "created_at": job.created_at.isoformat(),
            "file_size": job.file_size
        }
        
        if job.completed_at:
            job_info["completed_at"] = job.completed_at.isoformat()
        
        jobs_list.append(job_info)
    
    # Ordenar por fecha de creación (más recientes primero)
    jobs_list.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Aplicar límite
    jobs_list = jobs_list[:limit]
    
    return {
        "jobs": jobs_list,
        "total": len(jobs_list),
        "filters": {"status": status, "limit": limit}
    }

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str) -> Dict[str, str]:
    """Eliminar un job del almacén"""
    if job_id not in jobs_store:
        raise HTTPException(
            status_code=404,
            detail="Job no encontrado"
        )
    
    del jobs_store[job_id]
    return {"message": f"Job {job_id} eliminado exitosamente"}

@app.get("/system/stats")
async def get_system_stats() -> Dict[str, Any]:
    """Obtener estadísticas del sistema"""
    memory_usage = get_memory_usage()
    
    # Estadísticas de jobs
    job_stats = {
        "total": len(jobs_store),
        "pending": sum(1 for job in jobs_store.values() if job.status == JobStatus.PENDING),
        "processing": sum(1 for job in jobs_store.values() if job.status == JobStatus.PROCESSING),
        "completed": sum(1 for job in jobs_store.values() if job.status == JobStatus.COMPLETED),
        "failed": sum(1 for job in jobs_store.values() if job.status == JobStatus.FAILED)
    }
    
    return {
        "system": {
            "memory_usage_mb": memory_usage / (1024*1024),
            "max_memory_mb": MAX_MEMORY_USAGE / (1024*1024),
            "memory_usage_percent": (memory_usage / MAX_MEMORY_USAGE) * 100
        },
        "jobs": job_stats,
        "configuration": {
            "max_file_size_mb": MAX_FILE_SIZE / (1024*1024),
            "large_file_threshold_mb": LARGE_FILE_THRESHOLD / (1024*1024),
            "conversion_timeout_seconds": CONVERSION_TIMEOUT,
            "chunk_size_lines": CHUNK_SIZE
        }
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint para monitoreo de la aplicación"""
    try:
        # Verificar memoria disponible
        memory_usage = get_memory_usage()
        memory_ok = memory_usage < MAX_MEMORY_USAGE * 0.9  # 90% del límite
        
        # Verificar directorio temporal
        temp_dir_ok = os.path.exists(TEMP_FILES_DIR) and os.access(TEMP_FILES_DIR, os.W_OK)
        
        # Verificar MarkItDown
        markitdown_ok = md_converter is not None
        
        # Limpiar archivos temporales antiguos
        cleaned_files = cleanup_old_temp_files()
        
        # Estado general
        healthy = memory_ok and temp_dir_ok and markitdown_ok
        
        health_data = {
            "status": "healthy" if healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "memory": {
                    "status": "ok" if memory_ok else "warning",
                    "usage_mb": round(memory_usage / (1024*1024), 2),
                    "limit_mb": round(MAX_MEMORY_USAGE / (1024*1024), 2),
                    "usage_percent": round((memory_usage / MAX_MEMORY_USAGE) * 100, 2)
                },
                "temp_directory": {
                    "status": "ok" if temp_dir_ok else "error",
                    "path": TEMP_FILES_DIR,
                    "writable": temp_dir_ok
                },
                "markitdown": {
                    "status": "ok" if markitdown_ok else "error",
                    "available": markitdown_ok
                }
            },
            "maintenance": {
                "cleaned_temp_files": cleaned_files
            },
            "active_jobs": {
                "total": len(jobs_store),
                "processing": sum(1 for job in jobs_store.values() if job.status == JobStatus.PROCESSING)
            }
        }
        
        logger.info("Health check realizado", **health_data["checks"])
        
        return health_data
        
    except Exception as e:
        logger.error("Error en health check", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

async def convert_multiple_files_to_markdown(files: List[UploadFile]) -> List[Dict[str, Any]]:
    """Convierte múltiples archivos DOCX/PDF a markdown usando MarkItDown con extracción de títulos"""
    converted_files = []
    
    for index, file in enumerate(files):
        # Validar cada archivo
        validate_file(file)
        
        # Leer contenido del archivo
        file_content = await file.read()
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Convertir usando MarkItDown
            result = md_converter.convert(temp_file_path)
            markdown_content = result.text_content
            
            # Extraer título del contenido
            title_info = extract_title_from_content(markdown_content, file.filename)
            
            # Crear información del archivo
            file_info = FileInfo(
                filename=file.filename,
                file_size=len(file_content),
                file_type=Path(file.filename).suffix[1:].lower(),
                order_index=index
            )
            file_info.title_info = title_info
            
            converted_files.append({
                "file_info": file_info,
                "content": markdown_content,
                "title": title_info.custom_title or title_info.extracted_title
            })
            
        except Exception as e:
            logger.error(f"Error convirtiendo {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error convirtiendo {file.filename}: {str(e)}")
        
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    return converted_files

def merge_markdown_contents(converted_files: List[Dict[str, Any]], main_title: str = "Documento Fusionado") -> str:
    """Fusiona múltiples contenidos markdown usando títulos extraídos como separadores"""
    merged_content = f"# {main_title}\n\n"
    merged_content += f"*Documento generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    merged_content += f"*Este documento contiene {len(converted_files)} archivo(s) fusionado(s)*\n\n"
    
    # Agregar índice de contenidos
    merged_content += "## Índice de Contenidos\n\n"
    for i, file_data in enumerate(converted_files, 1):
        title = file_data["title"]
        filename = file_data["file_info"].filename
        merged_content += f"{i}. [{title}](#{title.lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')}) - *{filename}*\n"
    
    merged_content += "\n---\n\n"
    
    # Agregar contenido de cada archivo con su título como encabezado
    for i, file_data in enumerate(converted_files, 1):
        title = file_data["title"]
        content = file_data["content"]
        file_info = file_data["file_info"]
        
        # Agregar separador y título del documento
        merged_content += f"## {i}. {title}\n\n"
        merged_content += f"*Archivo original: {file_info.filename}*\n"
        merged_content += f"*Tamaño: {file_info.file_size:,} bytes*\n"
        merged_content += f"*Método de extracción de título: {file_info.title_info.extraction_method}*\n\n"
        
        # Procesar contenido para ajustar niveles de encabezados
        processed_content = ""
        for line in content.split('\n'):
            # Incrementar nivel de encabezados para mantener jerarquía
            if line.startswith('#'):
                line = '#' + line
            processed_content += line + '\n'
        
        merged_content += processed_content
        merged_content += "\n---\n\n"
    
    return merged_content

@app.post("/merge-docx")
async def merge_docx_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    title: str = "Documento Fusionado",
    output_format: OutputFormat = OutputFormat.MARKDOWN,
    save_temp: bool = True,
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fusiona múltiples documentos DOCX convirtiéndolos primero a markdown
    y luego combinándolos en un solo documento
    """
    
    # Validar que se proporcionen archivos
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos un archivo")
    
    # Validar límite de archivos (máximo 10 para evitar sobrecarga)
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Máximo 10 archivos permitidos para fusión")
    
    # Crear job para el proceso de fusión
    job_id = str(uuid.uuid4())
    total_size = sum(file.size or 0 for file in files)
    filenames = [file.filename for file in files]
    
    job = ConversionJob(
        job_id=job_id,
        filename=f"merged_{len(files)}_files.{get_file_extension_for_format(output_format)}",
        file_size=total_size,
        output_format=output_format
    )
    jobs_store[job_id] = job
    
    logger.info("Iniciando fusión de documentos", 
                job_id=job_id, 
                files_count=len(files), 
                filenames=filenames,
                total_size=total_size)
    
    try:
        # Verificar memoria disponible
        memory_usage = get_memory_usage()
        if memory_usage > MAX_MEMORY_USAGE:
            raise HTTPException(
                status_code=503, 
                detail=f"Memoria insuficiente. Uso actual: {memory_usage / 1024 / 1024:.1f}MB"
            )
        
        # Procesar archivos de forma asíncrona
        background_tasks.add_task(
            process_merge_async, 
            job, 
            files, 
            title, 
            save_temp, 
            webhook_url
        )
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": f"Procesando fusión de {len(files)} archivos",
            "files": filenames,
            "estimated_time": f"{len(files) * 30} segundos"
        }
        
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        logger.error("Error iniciando fusión", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error procesando fusión: {str(e)}")

async def process_merge_async(
    job: ConversionJob, 
    files: List[UploadFile], 
    title: str, 
    save_temp: bool, 
    webhook_url: Optional[str]
) -> None:
    """Procesa la fusión de archivos de forma asíncrona"""
    
    try:
        job.status = JobStatus.PROCESSING
        job.start_time = time.time()
        
        # Enviar actualización inicial
        await send_websocket_update(job.job_id, {
            "type": "progress",
            "status": "processing",
            "progress": 10,
            "message": "Iniciando procesamiento de archivos"
        })
        
        logger.info("Iniciando conversión de archivos a markdown", job_id=job.job_id)
        
        # Convertir archivos a markdown con extracción de títulos
        await send_websocket_update(job.job_id, {
            "type": "progress",
            "status": "processing",
            "progress": 30,
            "message": "Convirtiendo archivos a markdown"
        })
        
        converted_files = await convert_multiple_files_to_markdown(files)
        
        logger.info("Fusionando contenidos markdown", job_id=job.job_id)
        
        # Fusionar contenidos usando títulos extraídos
        await send_websocket_update(job.job_id, {
            "type": "progress",
            "status": "processing",
            "progress": 70,
            "message": "Fusionando contenidos"
        })
        
        merged_content = merge_markdown_contents(converted_files, title)
        
        # Formatear según el formato de salida solicitado
        await send_websocket_update(job.job_id, {
            "type": "progress",
            "status": "processing",
            "progress": 90,
            "message": "Formateando contenido final"
        })
        
        formatted_content = format_content_for_output(merged_content, job.output_format)
        
        # Guardar resultado en el formato esperado por /result/{job_id}
        job.result = {
            "success": True,
            "job_id": job.job_id,
            "filename": job.filename,
            "content": formatted_content,
            "format": job.output_format.value,
            "files_merged": len(files),
            "processing_time": None  # Se actualizará después
        }
        job.status = JobStatus.COMPLETED
        job.end_time = time.time()
        job.processing_time = job.end_time - job.start_time
        
        # Actualizar el processing_time en el resultado
        job.result["processing_time"] = job.processing_time
        
        # Esperar un momento para asegurar que la conexión WebSocket esté establecida
        await asyncio.sleep(0.5)
        
        # Enviar actualización de finalización con resultado
        completion_message = {
            "type": "status_update",
            "status": "completed",
            "progress": 100,
            "message": "Procesamiento completado exitosamente",
            "result": job.result
        }
        logger.info(f"🔍 Sending completion message with result: {completion_message}", job_id=job.job_id)
        await send_websocket_update(job.job_id, completion_message)
        
        # Esperar un momento adicional para asegurar que el mensaje se envíe
        await asyncio.sleep(0.2)
        
        # Guardar archivo temporal si se solicita
        if save_temp:
            try:
                temp_file_path = save_temp_file(
                    formatted_content, 
                    job.job_id, 
                    job.filename, 
                    job.output_format
                )
                job.temp_file_path = temp_file_path
                logger.info("Archivo temporal guardado", 
                           job_id=job.job_id, 
                           path=temp_file_path)
            except Exception as e:
                logger.warning("Error guardando archivo temporal", 
                              job_id=job.job_id, 
                              error=str(e))
        
        logger.info("Fusión completada exitosamente", 
                   job_id=job.job_id, 
                   processing_time=job.processing_time,
                   files_merged=len(files))
        
        # Enviar webhook si se proporciona
        if webhook_url:
            webhook_data = {
                "job_id": job.job_id,
                "status": "completed",
                "files_merged": len(files),
                "processing_time": job.processing_time,
                "result_preview": formatted_content[:500] + "..." if len(formatted_content) > 500 else formatted_content
            }
            await send_webhook(webhook_url, webhook_data)
        
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.end_time = time.time()
        
        # Enviar actualización de error por WebSocket
        await send_websocket_update(job.job_id, {
            "type": "error",
            "status": "failed",
            "progress": 0,
            "message": f"Error en procesamiento: {str(e)}",
            "error": str(e)
        })
        
        logger.error("Error en fusión de documentos", 
                    job_id=job.job_id, 
                    error=str(e))
        
        # Enviar webhook de error si se proporciona
        if webhook_url:
            webhook_data = {
                "job_id": job.job_id,
                "status": "failed",
                "error": str(e)
            }
            await send_webhook(webhook_url, webhook_data)

@app.post("/process-zip")
async def process_zip_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = "Documentos desde ZIP",
    output_format: OutputFormat = OutputFormat.MARKDOWN,
    save_temp: bool = True,
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Procesa un archivo ZIP extrayendo documentos DOCX y PDF para fusionarlos
    """
    
    # Validar que sea un archivo ZIP
    if not file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos ZIP")
    
    # Leer contenido del archivo ZIP
    zip_content = await file.read()
    
    # Validar que sea un ZIP válido
    if not validate_zip_file(zip_content):
        raise HTTPException(status_code=400, detail="Archivo ZIP inválido o corrupto")
    
    # Extraer archivos del ZIP
    try:
        extracted_files = extract_files_from_zip(zip_content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando ZIP: {str(e)}")
    
    if not extracted_files:
        raise HTTPException(status_code=400, detail="No se encontraron archivos DOCX o PDF válidos en el ZIP")
    
    # Crear objetos UploadFile temporales para los archivos extraídos
    temp_files = []
    for extracted in extracted_files:
        # Crear un objeto similar a UploadFile
        temp_file = type('TempUploadFile', (), {
            'filename': extracted['filename'],
            'size': extracted['size'],
            'content_type': f"application/{extracted['type']}",
            'read': lambda content=extracted['content']: asyncio.coroutine(lambda: content)()
        })()
        temp_files.append(temp_file)
    
    # Crear job para el proceso
    job_id = str(uuid.uuid4())
    total_size = sum(f['size'] for f in extracted_files)
    
    job = ConversionJob(
        job_id=job_id,
        filename=f"zip_merged_{len(extracted_files)}_files.{get_file_extension_for_format(output_format)}",
        file_size=total_size,
        output_format=output_format
    )
    jobs_store[job_id] = job
    
    logger.info("Procesando archivo ZIP", 
                job_id=job_id, 
                zip_filename=file.filename,
                extracted_count=len(extracted_files),
                total_size=total_size)
    
    # Procesar archivos extraídos de forma asíncrona
    background_tasks.add_task(
        process_merge_async, 
        job, 
        temp_files, 
        title, 
        save_temp, 
        webhook_url
    )
    
    return {
        "job_id": job_id,
        "status": "processing",
        "message": f"Procesando {len(extracted_files)} archivos extraídos del ZIP",
        "zip_filename": file.filename,
        "extracted_files": [f['filename'] for f in extracted_files],
        "estimated_time": f"{len(extracted_files) * 30} segundos"
    }

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint para actualizaciones en tiempo real del progreso de jobs
    """
    await websocket.accept()
    
    # Registrar conexión WebSocket
    websocket_connections[job_id] = websocket
    
    try:
        # Enviar estado inicial si el job existe
        if job_id in jobs_store:
            job = jobs_store[job_id]
            initial_status = {
                "type": "status_update",
                "job_id": job_id,
                "status": job.status.value,
                "progress": 0 if job.status == JobStatus.PENDING else 50 if job.status == JobStatus.PROCESSING else 100,
                "message": f"Job {job.status.value}"
            }
            await websocket.send_text(json.dumps(initial_status))
        
        # Mantener conexión activa
        while True:
            try:
                # Esperar por mensajes del cliente (ping/pong)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Responder a ping con pong
                if message == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # Enviar ping para mantener conexión activa
                await websocket.send_text(json.dumps({"type": "ping"}))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado para job {job_id}")
    except Exception as e:
        logger.error(f"Error en WebSocket para job {job_id}: {str(e)}")
    finally:
        # Limpiar conexión
        websocket_connections.pop(job_id, None)

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "API de conversión de documentos funcionando correctamente",
        "version": "2.1",
        "features": "Procesamiento asíncrono, seguimiento en tiempo real, respuestas por chunks, monitoreo de memoria, archivos temporales, integración n8n, fusión de documentos, extracción de títulos, soporte ZIP, WebSocket",
        "endpoints": "POST /convert, POST /convert-and-save, POST /merge-docx, POST /process-zip, WS /ws/{job_id}, GET /download/{job_id}, GET /status/{job_id}, GET /result/{job_id}, GET /jobs, DELETE /jobs/{job_id}, GET /system/stats, GET /health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)