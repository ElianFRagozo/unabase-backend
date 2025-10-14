#!/usr/bin/env python3
"""
Servidor estable sin monitoreo de archivos
"""
import os
import uvicorn
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración del servidor
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def main():
    print("🚀 Iniciando Unabase Document Processor API...")
    print(f"📍 Servidor: http://{HOST}:{PORT}")
    print(f"🔑 OpenAI configurado: {'✅' if OPENAI_API_KEY else '❌'}")
    print("🛑 Presiona Ctrl+C para detener")
    print("=" * 50)
    
    # Ejecutar servidor sin ninguna funcionalidad de reload
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
        access_log=True,
        # Configuraciones adicionales para evitar monitoreo
        reload_dirs=None,
        reload_excludes=None,
        reload_delay=0,
    )

if __name__ == "__main__":
    main()
