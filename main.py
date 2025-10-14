from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn
from config import settings
from routes import router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Unabase Document Processor API",
    description="API para procesar documentos fiscales usando ChatGPT",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(router)

@app.get("/")
async def root():
    """
    Endpoint de salud de la API
    """
    return {
        "message": "Unabase Document Processor API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "process_document": "/api/process-document",
            "validate_data": "/api/validate-extracted-data",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """
    Endpoint de verificación de salud
    """
    try:
        # Validar configuración
        settings.validate()
        
        return {
            "status": "healthy",
            "openai_configured": bool(settings.OPENAI_API_KEY),
            "timestamp": "2024-01-01T00:00:00Z"  # En producción usar datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Manejador global de excepciones
    """
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    try:
        # Validar configuración antes de iniciar
        settings.validate()
        logger.info("Starting Unabase Document Processor API...")
        
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=False,  # Sin reload automático
            reload_dirs=[],  # Sin directorios a monitorear
            reload_excludes=["*"],  # Excluir todo del monitoreo
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        exit(1)
