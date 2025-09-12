# Guía de Despliegue en Coolify

## Descripción
Esta guía te ayudará a desplegar tu API de conversión de documentos (DOCX/PDF a texto/markdown) en Coolify paso a paso.

## Prerrequisitos
- Cuenta en GitHub o GitLab
- Servidor con Coolify instalado
- Acceso a Coolify dashboard

## Paso 1: Preparar el Repositorio Git

### 1.1 Inicializar Git (si no está inicializado)
```bash
git init
git add .
git commit -m "Initial commit: FastAPI document conversion API"
```

### 1.2 Crear repositorio en GitHub/GitLab
1. Ve a GitHub.com o GitLab.com
2. Crea un nuevo repositorio (público o privado)
3. Copia la URL del repositorio

### 1.3 Conectar repositorio local con remoto
```bash
git remote add origin https://github.com/tu-usuario/tu-repositorio.git
git branch -M main
git push -u origin main
```

## Paso 2: Configuración en Coolify

### 2.1 Crear Nuevo Proyecto
1. Accede a tu dashboard de Coolify
2. Haz clic en "+ New Resource"
3. Selecciona "Application"
4. Elige "Public Repository" o "Private Repository" según tu caso

### 2.2 Configurar Repositorio
1. **Repository URL**: Pega la URL de tu repositorio
2. **Branch**: `main` (o la rama que uses)
3. **Build Pack**: Selecciona "Docker" (ya que tienes Dockerfile)
4. **Root Directory**: Deja vacío (a menos que tu app esté en subdirectorio)

### 2.3 Configuración de Build
1. **Dockerfile Path**: `./Dockerfile`
2. **Docker Context**: `./`
3. **Build Command**: (Coolify lo detectará automáticamente del Dockerfile)

## Paso 3: Variables de Entorno

### 3.1 Variables Requeridas
En la sección "Environment Variables" de Coolify, agrega:

```env
# Configuración básica
ENVIRONMENT=production
LOG_LEVEL=info

# Configuración de archivos
MAX_FILE_SIZE_MB=50
TEMP_FILE_RETENTION_HOURS=24
MAX_PAGES_SYNC=100
JOB_TIMEOUT_MINUTES=30

# Configuración de procesamiento
CHUNK_SIZE=1024
MAX_CONCURRENT_JOBS=5

# Configuración de Google Drive (opcional)
GOOGLE_DRIVE_ENABLED=false
# GOOGLE_DRIVE_FOLDER_ID=tu_folder_id
# GOOGLE_CREDENTIALS_JSON='{"type": "service_account", ...}'

# Configuración de Webhooks (opcional)
WEBHOOK_ENABLED=false
# WEBHOOK_URL=https://tu-webhook-url.com/webhook
# WEBHOOK_SECRET=tu_secreto_webhook
```

### 3.2 Variables Sensibles
Para variables sensibles como credenciales de Google Drive:
1. Usa la opción "Secret" en Coolify
2. No las pongas en texto plano en el repositorio

## Paso 4: Configuración de Red y Puertos

### 4.1 Puerto de la Aplicación
1. **Port**: `8000` (puerto interno del contenedor)
2. **Publicly Accessible**: Activar si quieres acceso público
3. **Domain**: Configura tu dominio personalizado o usa el subdominio de Coolify

### 4.2 Health Check
Coolify detectará automáticamente el endpoint `/health` definido en la aplicación.

## Paso 5: Configuración de Almacenamiento

### 5.1 Volúmenes Persistentes
Para mantener archivos temporales entre reinicios:
1. Ve a "Storages"
2. Agrega un nuevo volumen:
   - **Name**: `temp-files`
   - **Mount Path**: `/app/temp_files`
   - **Host Path**: `/var/lib/coolify/temp-files` (o ruta de tu preferencia)

## Paso 6: Despliegue

### 6.1 Iniciar Despliegue
1. Revisa toda la configuración
2. Haz clic en "Deploy"
3. Coolify comenzará el proceso de build y despliegue

### 6.2 Monitorear el Despliegue
1. Ve a la pestaña "Deployments"
2. Observa los logs en tiempo real
3. Espera a que el estado cambie a "Running"

## Paso 7: Verificación Post-Despliegue

### 7.1 Probar Endpoints
```bash
# Health check
curl https://tu-dominio.com/health

# Documentación API
curl https://tu-dominio.com/docs

# Test de conversión
curl -X POST "https://tu-dominio.com/convert" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.pdf" \
  -F "format=text"
```

### 7.2 Verificar Logs
1. En Coolify, ve a "Logs"
2. Revisa que no haya errores
3. Confirma que la aplicación inició correctamente

## Paso 8: Configuración de Dominio (Opcional)

### 8.1 Dominio Personalizado
1. Ve a "Domains"
2. Agrega tu dominio personalizado
3. Configura los registros DNS según las instrucciones
4. Coolify generará automáticamente certificados SSL

## Paso 9: Monitoreo y Mantenimiento

### 9.1 Logs y Métricas
- **Logs**: Accesibles desde el dashboard de Coolify
- **Métricas**: CPU, memoria, y uso de red
- **Alertas**: Configura notificaciones para errores

### 9.2 Actualizaciones
Para actualizar la aplicación:
1. Haz push de cambios a tu repositorio
2. Coolify detectará automáticamente los cambios
3. O manualmente haz clic en "Redeploy"

## Troubleshooting

### Problemas Comunes

#### 1. Error de Build
- Revisa los logs de build en Coolify
- Verifica que el Dockerfile esté correcto
- Asegúrate de que todas las dependencias estén en requirements.txt

#### 2. Aplicación no Inicia
- Revisa las variables de entorno
- Verifica que el puerto 8000 esté configurado correctamente
- Revisa los logs de la aplicación

#### 3. Errores de Permisos de Archivos
- Verifica que el volumen esté montado correctamente
- Asegúrate de que el usuario del contenedor tenga permisos de escritura

#### 4. Timeouts en Archivos Grandes
- Aumenta `JOB_TIMEOUT_MINUTES`
- Verifica que `MAX_FILE_SIZE_MB` sea apropiado
- Considera usar procesamiento asíncrono para archivos grandes

### Comandos Útiles

```bash
# Ver logs en tiempo real
docker logs -f container_name

# Acceder al contenedor
docker exec -it container_name /bin/bash

# Verificar espacio en disco
df -h

# Limpiar archivos temporales manualmente
find /app/temp_files -type f -mtime +1 -delete
```

## Configuraciones Avanzadas

### Auto-scaling (Si está disponible)
1. Configura réplicas mínimas y máximas
2. Define métricas de escalado (CPU, memoria)
3. Configura load balancer si es necesario

### Backup y Recuperación
1. Configura backups automáticos de volúmenes
2. Documenta el proceso de recuperación
3. Prueba regularmente los backups

## Seguridad

### Recomendaciones
1. **HTTPS**: Siempre usa HTTPS en producción
2. **Rate Limiting**: Considera implementar rate limiting
3. **File Validation**: La aplicación ya valida tipos de archivo
4. **Secrets**: Usa variables de entorno para información sensible
5. **Updates**: Mantén actualizado el sistema base y dependencias

### Variables de Seguridad Adicionales
```env
# Límites de seguridad
MAX_REQUESTS_PER_MINUTE=60
ALLOWED_ORIGINS=https://tu-dominio.com
SECURE_HEADERS=true
```

## Conclusión

Tu API de conversión de documentos ahora está desplegada en Coolify con:
- ✅ Procesamiento de DOCX y PDF
- ✅ Conversión a texto y markdown
- ✅ Procesamiento asíncrono para archivos grandes
- ✅ Endpoints de descarga directa
- ✅ Limpieza automática de archivos temporales
- ✅ Health checks y monitoreo
- ✅ Configuración para integración con n8n/Google Drive

¡Tu API está lista para usar en producción!

---

**Soporte**: Si encuentras problemas, revisa los logs en Coolify y consulta la documentación oficial de Coolify para configuraciones específicas de tu servidor.