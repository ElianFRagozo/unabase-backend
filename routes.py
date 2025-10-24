from fastapi import APIRouter, HTTPException, status, Request
from typing import Dict, Any
import logging
import json
from models import (
    ProcessDocumentRequest, 
    ProcessDocumentResponse,
    ValidateDataRequest,
    ValidateDataResponse
)
from openai_service import OpenAIService
from document_agent import DocumentAgent
from openai_assistant import OpenAIAssistant

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
openai_service = OpenAIService()
document_agent = DocumentAgent()
openai_assistant = OpenAIAssistant()

@router.post("/api/process-document", response_model=ProcessDocumentResponse)
async def process_document(request: ProcessDocumentRequest):
    """
    Procesa una imagen de documento fiscal y extrae información usando ChatGPT
    """
    try:
        logger.info(f"Processing document for expenseId: {request.expenseId}")
        logger.info(f"User: {request.userData.userId}, Empresa: {request.userData.empresa}")
        
        # Validar que la imagen esté presente
        if not request.image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image data is required"
            )
        
        # Validar formato base64
        try:
            import base64
            # Intentar decodificar para validar que es base64 válido
            base64.b64decode(request.image.split(',')[-1] if ',' in request.image else request.image)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 image format"
            )
        
        # Procesar la imagen con el OpenAI Assistant real
        logger.info("🤖 Usando OpenAI Assistant para procesamiento inteligente...")
        context = {
            "expenseId": request.expenseId,
            "userData": {
                "userId": request.userData.userId,
                "empresa": request.userData.empresa
            }
        }
        extracted_data = openai_assistant.process_document(request.image, context)
        
        # Agregar metadata del request
        extracted_data["expenseId"] = request.expenseId
        extracted_data["userData"] = {
            "userId": request.userData.userId,
            "empresa": request.userData.empresa
        }
        
        logger.info(f"Successfully processed document. Confidence: {extracted_data.get('confidence', 0)}%")
        logger.info(f"Extracted data keys: {list(extracted_data.keys())}")
        logger.info(f"Sample extracted data: {json.dumps({k: v for k, v in extracted_data.items() if k not in ['expenseId', 'userData']}, indent=2)}")
        
        return ProcessDocumentResponse(
            success=True,
            data=extracted_data
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )

@router.post("/api/validate-extracted-data")
async def validate_extracted_data(request: Request):
    """
    Valida los datos extraídos por ChatGPT
    """
    try:
        # Obtener datos del request
        body = await request.json()
        logger.info(f"Raw request data: {json.dumps(body, indent=2)}")
        
        # Extraer datos de manera flexible
        extracted_data = body.get("extractedData", {})
        confidence_raw = body.get("confidence", 0)
        
        # Convertir confidence a int si es necesario
        try:
            confidence = int(confidence_raw)
        except (ValueError, TypeError):
            logger.warning(f"Invalid confidence value: {confidence_raw}, using 0")
            confidence = 0
        
        logger.info(f"Validating extracted data with confidence: {confidence}%")
        logger.info(f"Extracted data keys: {list(extracted_data.keys()) if extracted_data else 'None'}")
        
        # Validar confidence
        if not (0 <= confidence <= 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confidence must be between 0 and 100"
            )
        
        # Validar que hay datos para validar
        if not extracted_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Extracted data is required"
            )
        
        # Realizar validaciones específicas
        validation_results = _validate_document_data(extracted_data)
        
        # Determinar si los datos son válidos
        is_valid = (
            validation_results["is_valid"] and 
            confidence >= 70  # Umbral mínimo de confianza
        )
        
        response_data = {
            "isValid": is_valid,
            "confidence": confidence,
            "validationResults": validation_results,
            "recommendations": _generate_recommendations(validation_results, confidence)
        }
        
        logger.info(f"Validation completed. Valid: {is_valid}")
        
        return {
            "success": True,
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating data: {str(e)}")
        logger.error(f"Request data type: {type(request)}")
        logger.error(f"Request data: {request}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating data: {str(e)}"
        )

@router.post("/api/debug-validate-data")
async def debug_validate_data(request: Request):
    """
    Endpoint de debug para ver qué datos está enviando el frontend
    """
    try:
        body = await request.json()
        logger.info(f"DEBUG - Raw request body: {json.dumps(body, indent=2)}")
        
        return {
            "success": True,
            "received_data": body,
            "data_types": {
                "extractedData_type": type(body.get("extractedData", None)).__name__,
                "confidence_type": type(body.get("confidence", None)).__name__,
                "confidence_value": body.get("confidence", None)
            }
        }
    except Exception as e:
        logger.error(f"Debug error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def _validate_document_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida los datos del documento extraído
    """
    validation_results = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "field_validations": {}
    }
    
    # Validar campos obligatorios
    required_fields = [
        "referencia", "tipoDocumento", "numeroDocumento", 
        "fecha", "moneda", "nombre", "rut", "total", "detalle"
    ]
    
    for field in required_fields:
        if not data.get(field):
            validation_results["errors"].append(f"Campo obligatorio '{field}' no encontrado")
            validation_results["is_valid"] = False
            validation_results["field_validations"][field] = False
        else:
            validation_results["field_validations"][field] = True
    
    # Validaciones específicas
    if data.get("fecha"):
        if not _is_valid_date_format(data["fecha"]):
            validation_results["warnings"].append("Formato de fecha no está en DD/MM/YYYY")
            validation_results["field_validations"]["fecha"] = False
    
    if data.get("rut"):
        if not _is_valid_rut_format(data["rut"]):
            validation_results["warnings"].append("Formato de RUT no es válido (debe ser XX.XXX.XXX-X)")
            validation_results["field_validations"]["rut"] = False
    
    if data.get("total"):
        if not _is_valid_amount(data["total"]):
            validation_results["warnings"].append("Formato de monto total no es válido")
            validation_results["field_validations"]["total"] = False
    
    return validation_results

def _is_valid_date_format(date_str: str) -> bool:
    """
    Valida formato de fecha DD/MM/YYYY
    """
    import re
    pattern = r'^\d{1,2}/\d{1,2}/\d{4}$'
    return bool(re.match(pattern, date_str))

def _is_valid_rut_format(rut_str: str) -> bool:
    """
    Valida formato de RUT chileno XX.XXX.XXX-X
    """
    import re
    pattern = r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$'
    return bool(re.match(pattern, rut_str))

def _is_valid_amount(amount_str: str) -> bool:
    """
    Valida que el monto sea un número válido
    """
    try:
        float(amount_str)
        return True
    except (ValueError, TypeError):
        return False

def _generate_recommendations(validation_results: Dict[str, Any], confidence: int) -> list:
    """
    Genera recomendaciones basadas en los resultados de validación
    """
    recommendations = []
    
    if confidence < 70:
        recommendations.append("Confianza baja - considerar revisión manual")
    
    if validation_results["errors"]:
        recommendations.append("Corregir campos obligatorios faltantes")
    
    if validation_results["warnings"]:
        recommendations.append("Revisar formatos de campos con advertencias")
    
    if not recommendations:
        recommendations.append("Datos válidos - listo para procesar")
    
    return recommendations
