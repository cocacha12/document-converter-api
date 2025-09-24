# 🚀 Deployment Guide

This guide covers various deployment options for the Document Converter API. Choose the platform that best fits your needs.

## 📋 Prerequisites

- Git repository with your code
- Docker support (recommended)
- Basic understanding of environment variables

## 🔥 Nixpacks Deployment (Recommended)

### What is Nixpacks?

Nixpacks is a modern build system that automatically detects your project type and builds optimized containers without requiring a Dockerfile. It's perfect for FastAPI applications and handles all system dependencies automatically.

### Advantages of Nixpacks

- ✅ **No Docker Hub Issues**: Bypasses Docker Hub rate limits and authentication problems
- ✅ **Automatic Detection**: Detects Python/FastAPI projects automatically
- ✅ **System Dependencies**: Installs LibreOffice, Tesseract, Pandoc, and other tools automatically
- ✅ **Optimized Builds**: Creates smaller, faster containers
- ✅ **Zero Configuration**: Works out of the box with minimal setup

### Nixpacks Configuration

The project includes a `nixpacks.toml` file with all necessary configurations:

```toml
[variables]
PORT = "8000"
HOST = "0.0.0.0"
ENVIRONMENT = "production"

[phases.setup]
cmds = [
    "apt-get update",
    "apt-get install -y curl libmagic-dev poppler-utils tesseract-ocr tesseract-ocr-spa libreoffice pandoc qpdf",
    "apt-get clean",
    "rm -rf /var/lib/apt/lists/*"
]

[phases.install]
cmds = [
    "pip install --no-cache-dir -r requirements.txt"
]

[phases.build]
cmds = [
    "cd frontend && npm ci && npm run build"
]

[start]
cmd = "uvicorn main:app --host 0.0.0.0 --port $PORT"

[staticAssets]
"frontend/dist" = "/"
```

### Coolify Deployment with Nixpacks

1. **Connect Repository**
   - Go to your Coolify dashboard
   - Click "New Resource" → "Application"
   - Connect your GitHub repository
   - Select the `main` branch

2. **Select Build Method**
   - Choose **"Nixpacks"** as the build method
   - Coolify will automatically detect the `nixpacks.toml` configuration

3. **Configure Environment Variables**
   ```env
   PORT=8000
   HOST=0.0.0.0
   ENVIRONMENT=production
   MAX_FILE_SIZE=52428800
   TEMP_FILES_RETENTION_HOURS=24
   ALLOWED_ORIGINS=*
   ```

4. **Deploy**
   - Click "Deploy"
   - Nixpacks will automatically build and deploy your application
   - No Docker Hub authentication required!

### Troubleshooting Nixpacks

If you encounter issues:

1. **Check Build Logs**: Review the Nixpacks build output in Coolify
2. **Verify Configuration**: Ensure `nixpacks.toml` is in the root directory
3. **Environment Variables**: Make sure all required variables are set
4. **Dependencies**: All system dependencies are handled automatically

## 🐳 Docker Deployment (Alternative)

### System Dependencies

The application requires these system dependencies (included in Dockerfile):

- `libmagic-dev` - File type detection
- `poppler-utils` - PDF processing
- `tesseract-ocr` - OCR for scanned documents
- `tesseract-ocr-spa` - Spanish language pack
- `tesseract-ocr-eng` - English language pack
- `libreoffice` - Office document processing
- `pandoc` - Document conversion
- `qpdf` - PDF manipulation

### Quick Docker Setup

```bash
# Build and run with Docker
docker build -t document-converter-api .
docker run -p 8000:8000 document-converter-api

# Or use Docker Compose
docker-compose up -d
```

## ☁️ Cloud Platform Deployment

### 1. Heroku

```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set PORT=8000
heroku config:set HOST=0.0.0.0
heroku config:set LOG_LEVEL=INFO

# Deploy
git push heroku main
```

**Heroku Configuration:**
- Add `heroku/python` buildpack
- Set stack to `heroku-22` or later
- Configure dyno type: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 2. Railway

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Railway will automatically detect and deploy your FastAPI app

**Railway Environment Variables:**
```env
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
```

### 3. Render

1. Connect your GitHub repository
2. Choose "Web Service"
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 4. DigitalOcean App Platform

1. Create new app from GitHub repository
2. Configure as a "Web Service"
3. Set environment variables
4. Deploy with automatic scaling

### 5. AWS ECS/Fargate

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker build -t document-converter-api .
docker tag document-converter-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/document-converter-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/document-converter-api:latest
```

### 6. Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/document-converter-api
gcloud run deploy --image gcr.io/PROJECT-ID/document-converter-api --platform managed
```

### 7. Azure Container Instances

```bash
# Deploy to Azure
az container create \
  --resource-group myResourceGroup \
  --name document-converter-api \
  --image your-registry/document-converter-api:latest \
  --ports 8000 \
  --environment-variables PORT=8000 HOST=0.0.0.0
```

## 🔧 Environment Variables

### Required Variables

```env
# Server Configuration
PORT=8000
HOST=0.0.0.0

# File Processing
MAX_FILE_SIZE=52428800
LARGE_FILE_THRESHOLD=5242880
CONVERSION_TIMEOUT=300
CHUNK_SIZE=1000

# Temporary Files
TEMP_FILES_DIR=./temp_files
TEMP_FILES_RETENTION_HOURS=24
MAX_TEMP_FILES=100

# Logging
ENVIRONMENT=production
LOG_LEVEL=INFO

# CORS Configuration
ALLOWED_ORIGINS=*
```

### Optional Variables

```env
# Webhook for notifications (optional)
WEBHOOK_URL=https://your-webhook-url.com/webhook

# Custom timeout settings
REQUEST_TIMEOUT=60
KEEP_ALIVE_TIMEOUT=5
```

## 📊 Resource Requirements

### Minimum Requirements
- **CPU**: 0.5 cores
- **RAM**: 512MB
- **Storage**: 2GB
- **Network**: HTTP/HTTPS access

### Recommended for Production
- **CPU**: 1-2 cores
- **RAM**: 1-2GB
- **Storage**: 5-10GB
- **Timeout**: 300 seconds

## 🏥 Health Checks

Configure health checks for your deployment:

- **Endpoint**: `/health`
- **Port**: 8000 (or your configured port)
- **Method**: GET
- **Expected Response**: 200 OK
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

### Extended Health Check

For more detailed monitoring:
- **Endpoint**: `/health?extended=true`
- **Includes**: System stats, memory usage, temp file cleanup

## 📈 Monitoring Endpoints

- `GET /health` - Basic health check
- `GET /health?extended=true` - Extended health check with cleanup
- `GET /system/stats` - System statistics and job metrics
- `GET /jobs` - Active jobs list

## 🔒 Security Considerations

### Production Security

1. **Environment Variables**: Never commit secrets to version control
2. **CORS**: Configure `ALLOWED_ORIGINS` appropriately
3. **File Size Limits**: Set reasonable `MAX_FILE_SIZE`
4. **Rate Limiting**: Consider implementing rate limiting
5. **HTTPS**: Always use HTTPS in production

### Recommended Security Headers

```python
# Add to your FastAPI app
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com"])
```

## 🐛 Troubleshooting

### Common Issues

1. **Memory Errors**
   - Increase memory allocation
   - Adjust `LARGE_FILE_THRESHOLD`
   - Monitor `/system/stats` endpoint

2. **Timeout Issues**
   - Increase `CONVERSION_TIMEOUT`
   - Check file size limits
   - Monitor processing time

3. **File Permission Errors**
   - Ensure write permissions for `TEMP_FILES_DIR`
   - Check Docker volume mounts
   - Verify user permissions

4. **System Dependencies**
   - Use provided Dockerfile
   - Install all required system packages
   - Check OCR language packs

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### Log Analysis

The application provides structured JSON logging in production:
- Request/response logging
- Error tracking
- Performance metrics
- System resource usage

## 📝 Deployment Checklist

- [ ] Repository connected to deployment platform
- [ ] Environment variables configured
- [ ] Health checks enabled
- [ ] Resource limits set appropriately
- [ ] HTTPS configured
- [ ] Domain/subdomain configured
- [ ] Monitoring/logging enabled
- [ ] Backup strategy in place
- [ ] Security headers configured
- [ ] CORS settings appropriate for your use case

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to Platform
      run: |
        # Your deployment commands here
        echo "Deploying to production..."
```

### Automated Testing

```yaml
- name: Run Tests
  run: |
    pip install pytest pytest-asyncio httpx
    pytest
```

## 📞 Support

If you encounter issues during deployment:

1. Check the application logs
2. Verify environment variables
3. Test health endpoints
4. Review resource usage
5. Consult platform-specific documentation

For platform-specific help:
- **Heroku**: [Heroku Dev Center](https://devcenter.heroku.com/)
- **Railway**: [Railway Docs](https://docs.railway.app/)
- **Render**: [Render Docs](https://render.com/docs)
- **DigitalOcean**: [App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- **AWS**: [ECS Documentation](https://docs.aws.amazon.com/ecs/)
- **Google Cloud**: [Cloud Run Docs](https://cloud.google.com/run/docs)
- **Azure**: [Container Instances Docs](https://docs.microsoft.com/en-us/azure/container-instances/)

---

**Happy Deploying! 🚀**