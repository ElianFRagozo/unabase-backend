# 🧾 Unabase Document Processor API

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?style=for-the-badge&logo=fastapi&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange?style=for-the-badge&logo=openai&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**🚀 API backend inteligente para procesar documentos fiscales chilenos**

*Extrae información automáticamente de boletas, facturas y recibos usando IA*

</div>

---

## ✨ Características Principales

| 🎯 **Funcionalidad** | 📝 **Descripción** |
|---------------------|-------------------|
| 🔍 **Análisis Inteligente** | Procesa imágenes de documentos fiscales usando GPT-4-turbo |
| 📊 **Extracción Estructurada** | Extrae información en formato JSON con campos obligatorios y opcionales |
| ✅ **Validación Automática** | Valida los datos extraídos con niveles de confianza |
| 🚀 **API REST Moderna** | Endpoints bien documentados con FastAPI y Swagger UI |
| 🇨🇱 **Optimizado para Chile** | Validaciones específicas para RUT, fechas y formatos chilenos |

## 📋 Campos Extraídos

### 🔴 **Campos Obligatorios**
| Campo | Descripción | Formato |
|-------|-------------|---------|
| `referencia` | Referencia o número de folio del documento | String |
| `tipoDocumento` | Tipo de documento (Boleta, Factura, Recibo, etc.) | String |
| `numeroDocumento` | Número del documento | String |
| `fecha` | Fecha del documento | DD/MM/YYYY |
| `moneda` | Código de moneda (CLP, USD, EUR, etc.) | String |
| `nombre` | Nombre del proveedor/empresa emisora | String |
| `rut` | RUT chileno del proveedor | XX.XXX.XXX-X |
| `total` | Monto total del documento | Número |
| `detalle` | Descripción de los productos/servicios | String |

### 🟡 **Campos Opcionales**
| Campo | Descripción | Formato |
|-------|-------------|---------|
| `alias` | Nombre comercial o alias del proveedor | String |
| `email` | Email del proveedor si es visible | String |
| `impuestos` | Monto de impuestos si es visible | Número |
| `porcentaje` | Porcentaje de impuestos si es visible | String |

## 🚀 Instalación Rápida

### 📥 **Paso 1: Clonar el repositorio**
```bash
git clone <repository-url>
cd unabase-backend
```

### 🐍 **Paso 2: Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 📦 **Paso 3: Instalar dependencias**
```bash
pip install -r requirements.txt
```

### ⚙️ **Paso 4: Configurar variables de entorno**
```bash
cp config.example .env
# Editar .env y agregar tu OPENAI_API_KEY
```

## ⚙️ Configuración

Crear archivo `.env` con:
```env
# 🔑 Configuración de OpenAI
OPENAI_API_KEY=tu_api_key_de_openai_aqui

# 🌐 Configuración del servidor
PORT=8000
HOST=0.0.0.0

# 🛠️ Configuración de desarrollo
DEBUG=False
```

## 🎯 Uso

### 🚀 **Iniciar el servidor**
```bash
python main.py
```

### 📚 **Documentación de la API**
- 🔍 **Swagger UI**: `http://localhost:8000/docs`
- 📖 **ReDoc**: `http://localhost:8000/redoc`
- ❤️ **Health Check**: `http://localhost:8000/health`

## 🔌 Endpoints de la API

### 📄 **1. POST `/api/process-document`**
*Procesa una imagen de documento fiscal y extrae información*

**📥 Request:**
```json
{
  "image": "base64_image_data",
  "expenseId": "string",
  "userData": {
    "userId": "string",
    "empresa": "string"
  }
}
```

**📤 Response:**
```json
{
  "success": true,
  "data": {
    "documentData": {
      "referencia": "BOL-2024-001",
      "tipoDocumento": "Boleta",
      "numeroDocumento": "8752",
      "fecha": "15/12/2024",
      "moneda": "CLP"
    },
    "providerData": {
      "nombre": "Ferretería El Constructor",
      "alias": "El Constructor",
      "email": "ventas@constructor.cl",
      "rut": "76.123.456-7"
    },
    "detailsData": {
      "lineaAsociar": "Materiales",
      "porcentaje": "19%",
      "impuestos": "1300",
      "total": "10000",
      "detalle": "Compra de materiales de construcción"
    },
    "confidence": 95,
    "extractedFields": ["referencia", "tipoDocumento", "numeroDocumento", "fecha", "moneda", "nombre", "rut", "total", "detalle"],
    "missingFields": ["email", "impuestos"]
  }
}
```

### ✅ **2. POST `/api/validate-extracted-data`**
*Valida los datos extraídos por ChatGPT*

**📥 Request:**
```json
{
  "extractedData": {
    "referencia": "BOL-2024-001",
    "tipoDocumento": "Boleta",
    "numeroDocumento": "8752",
    "fecha": "15/12/2024",
    "moneda": "CLP",
    "nombre": "Ferretería El Constructor",
    "rut": "76.123.456-7",
    "total": "10000",
    "detalle": "Compra de materiales de construcción"
  },
  "confidence": 95
}
```

**📤 Response:**
```json
{
  "success": true,
  "data": {
    "isValid": true,
    "confidence": 95,
    "validationResults": {
      "is_valid": true,
      "errors": [],
      "warnings": [],
      "field_validations": {
        "referencia": true,
        "tipoDocumento": true,
        "numeroDocumento": true,
        "fecha": true,
        "moneda": true,
        "nombre": true,
        "rut": true,
        "total": true,
        "detalle": true
      }
    },
    "recommendations": ["Datos válidos - listo para procesar"]
  }
}
```

## 🧪 Ejemplo de Uso con cURL

```bash
# 📄 Procesar documento
curl -X POST "http://localhost:8000/api/process-document" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
    "expenseId": "exp-123",
    "userData": {
      "userId": "user-456",
      "empresa": "Mi Empresa"
    }
  }'
```

## 📁 Estructura del Proyecto

```
unabase-backend/
├── 🚀 main.py              # Aplicación principal FastAPI
├── 🔌 routes.py            # Definición de endpoints
├── 📋 models.py            # Modelos Pydantic
├── 🤖 openai_service.py    # Servicio de integración con OpenAI
├── ⚙️ config.py            # Configuración de la aplicación
├── 📦 requirements.txt     # Dependencias Python
├── 🧪 test_api.py          # Script de pruebas
├── 📖 README.md           # Este archivo
└── 🚫 .gitignore          # Archivos ignorados por Git
```

## 📦 Dependencias Principales

| Librería | Versión | Propósito |
|----------|---------|-----------|
| 🚀 **FastAPI** | 0.104+ | Framework web moderno y rápido |
| 🤖 **OpenAI** | 1.3+ | Cliente para GPT-4-turbo |
| ✅ **Pydantic** | 2.5+ | Validación de datos |
| 🌐 **Uvicorn** | 0.24+ | Servidor ASGI |
| 📝 **Python-multipart** | 0.0.6+ | Manejo de formularios multipart |

## ⚠️ Notas Importantes

| 🔑 **Aspecto** | 📝 **Descripción** |
|----------------|-------------------|
| **API Key** | Necesitas una API key válida de OpenAI |
| **Formato de imagen** | Acepta imágenes en base64 |
| **Límites** | Respeta los límites de rate de OpenAI |
| **Confianza** | El sistema calcula automáticamente el nivel de confianza |
| **Validación** | Incluye validación de formatos (fecha, RUT, montos) |

## 🛠️ Desarrollo

Para desarrollo local:
```bash
# 📦 Instalar en modo desarrollo
pip install -e .

# 🔄 Ejecutar con recarga automática
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🚀 Producción

Para producción:
```bash
# 📦 Instalar dependencias
pip install -r requirements.txt

# 🌐 Ejecutar servidor
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

<div align="center">

**🎉 ¡Backend listo para procesar documentos fiscales chilenos!**

*Desarrollado con ❤️ para Unabase*

</div>
