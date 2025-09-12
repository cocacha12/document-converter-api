# 📄 Document Converter API

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A powerful and fast API for converting PDF and DOCX documents to Markdown or plain text using Microsoft's MarkItDown library. Perfect for document processing, content extraction, and text analysis workflows.

## ✨ Features

- 🔄 **Document Conversion**: Convert PDF and DOCX files to Markdown or plain text
- ⚡ **Powered by MarkItDown**: Uses Microsoft's advanced document processing library
- 🚀 **Async Processing**: Handle multiple documents simultaneously
- 📥 **Direct Downloads**: Get converted files instantly via download endpoints
- 🏥 **Health Checks**: Built-in monitoring and status endpoints
- 🐳 **Docker Ready**: Containerized for easy deployment
- 📊 **RESTful API**: Clean and intuitive API design
- 🔒 **Production Ready**: Structured logging and error handling

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/cocacha12/document-converter-api.git
cd document-converter-api

# Run with Docker Compose
docker-compose up -d

# API will be available at http://localhost:8000
```

### Local Installation

```bash
# Clone and setup
git clone https://github.com/cocacha12/document-converter-api.git
cd document-converter-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📖 API Usage

### Convert Document

**Endpoint:** `POST /convert`

#### Convert to Markdown (default)

```bash
curl -X POST "http://localhost:8000/convert" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

#### Convert to Plain Text

```bash
curl -X POST "http://localhost:8000/convert?format=text" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.docx"
```

#### Python Example

```python
import requests

# Convert PDF to Markdown
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/convert',
        files={'file': f}
    )
    result = response.json()
    print(result['content'])

# Convert DOCX to Text
with open('document.docx', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/convert',
        files={'file': f},
        params={'format': 'text'}
    )
    result = response.json()
    print(result['content'])
```

### Download Converted File

**Endpoint:** `GET /download/{job_id}`

```bash
# After conversion, use the job_id to download
curl -X GET "http://localhost:8000/download/{job_id}" \
  --output converted_document.txt
```

### Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/convert` | Convert PDF/DOCX to Markdown/Text |
| `GET` | `/download/{job_id}` | Download converted file |
| `GET` | `/health` | Health check endpoint |
| `GET` | `/` | API documentation (Swagger UI) |

## 🔧 Configuration

### Environment Variables

```bash
# Server Configuration
PORT=8000
HOST=0.0.0.0

# File Processing
MAX_FILE_SIZE=50MB
TEMP_DIR=./temp_files

# Logging
LOG_LEVEL=INFO
```

### Supported File Types

- **PDF**: `.pdf`
- **DOCX**: `.docx`

### Output Formats

- **Markdown**: Rich formatting preserved
- **Plain Text**: Clean text extraction

## 🐳 Deployment

### Docker

```bash
# Build image
docker build -t document-converter-api .

# Run container
docker run -p 8000:8000 document-converter-api
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./temp_files:/app/temp_files
    environment:
      - LOG_LEVEL=INFO
```

### Cloud Deployment

This API is ready for deployment on:
- **Heroku**
- **Railway**
- **Render**
- **DigitalOcean App Platform**
- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**

## 🛠️ Development

### Project Structure

```
document-converter-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── models.py        # Pydantic models
│   └── utils.py         # Utility functions
├── temp_files/          # Temporary file storage
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [MarkItDown](https://github.com/microsoft/markitdown) - Microsoft's document processing library
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework for building APIs
- [Uvicorn](https://www.uvicorn.org/) - ASGI server implementation

## 📞 Support

If you have any questions or issues, please:
1. Check the [Issues](https://github.com/cocacha12/document-converter-api/issues) page
2. Create a new issue if needed
3. Star ⭐ the repository if you find it useful!

---

**Keywords**: document converter, PDF to markdown, DOCX to text, MarkItDown API, FastAPI, document processing, text extraction, file conversion