#!/usr/bin/env python3
"""
Script para ejecutar el servidor de manera estable
Evita problemas con múltiples ventanas de Cursor
"""

import uvicorn
from main import app
from config import settings

if __name__ == "__main__":
    print("🚀 Iniciando servidor Unabase Backend...")
    print(f"📍 Host: {settings.HOST}")
    print(f"🔌 Puerto: {settings.PORT}")
    print(f"🔧 Debug: {settings.DEBUG}")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=False,  # Deshabilitado para evitar múltiples ventanas
        reload_dirs=[],
        reload_excludes=["*"],
        log_level="info"
    )
