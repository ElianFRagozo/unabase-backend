#!/usr/bin/env python3
"""
Script rápido para iniciar el servidor Unabase
"""
from main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Unabase Document Processor...")
    uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)
