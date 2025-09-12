#!/usr/bin/env python3
"""
Script de prueba para la API de procesamiento de documentos
"""

import requests
import base64
import json
import os

# Configuración
API_BASE_URL = "http://127.0.0.1:8000"

def test_health_endpoint():
    """Prueba el endpoint de salud"""
    print("🔍 Probando endpoint de salud...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_root_endpoint():
    """Prueba el endpoint raíz"""
    print("\n🔍 Probando endpoint raíz...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_sample_base64_image():
    """Crea una imagen de ejemplo en base64 (1x1 pixel PNG)"""
    # PNG de 1x1 pixel transparente
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

def test_process_document():
    """Prueba el endpoint de procesamiento de documentos"""
    print("\n🔍 Probando endpoint de procesamiento de documentos...")
    
    # Crear imagen de ejemplo
    sample_image = create_sample_base64_image()
    
    payload = {
        "image": sample_image,
        "expenseId": "test-expense-123",
        "userData": {
            "userId": "test-user-456",
            "empresa": "Empresa de Prueba"
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/process-document",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Documento procesado exitosamente")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Error en procesamiento: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_validate_data():
    """Prueba el endpoint de validación de datos"""
    print("\n🔍 Probando endpoint de validación de datos...")
    
    sample_data = {
        "referencia": "BOL-2024-001",
        "tipoDocumento": "Boleta",
        "numeroDocumento": "8752",
        "fecha": "15/12/2024",
        "moneda": "CLP",
        "nombre": "Ferretería El Constructor",
        "rut": "76.123.456-7",
        "total": "10000",
        "detalle": "Compra de materiales de construcción"
    }
    
    payload = {
        "extractedData": sample_data,
        "confidence": 95
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/validate-extracted-data",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Datos validados exitosamente")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Error en validación: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de la API de procesamiento de documentos")
    print("=" * 60)
    
    # Verificar que el servidor esté corriendo
    if not test_health_endpoint():
        print("\n❌ El servidor no está corriendo o no está configurado correctamente")
        print("💡 Asegúrate de que:")
        print("   1. El servidor esté corriendo: python main.py")
        print("   2. Tengas configurado OPENAI_API_KEY en .env")
        return
    
    # Ejecutar todas las pruebas
    tests = [
        ("Endpoint raíz", test_root_endpoint),
        ("Procesamiento de documentos", test_process_document),
        ("Validación de datos", test_validate_data)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        success = test_func()
        results.append((test_name, success))
    
    # Resumen de resultados
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(results)} pruebas pasaron")
    
    if passed == len(results):
        print("🎉 ¡Todas las pruebas pasaron! La API está funcionando correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa la configuración y los logs.")

if __name__ == "__main__":
    main()
