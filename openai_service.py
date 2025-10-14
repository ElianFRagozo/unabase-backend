import openai
import base64
import json
import re
from typing import Dict, Any, Optional
from config import settings

class OpenAIService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        print(f"🔧 OpenAI Service Init: API Key length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0}")
        
        if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 20:
            try:
                self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                print(f"✅ OpenAI Service: Cliente creado exitosamente")
            except Exception as e:
                print(f"❌ OpenAI Service: Error creando cliente: {e}")
                self.client = None
        else:
            print(f"⚠️ OpenAI Service: API Key inválida o muy corta")
            self.client = None
    
    def analyze_document_image(self, image_base64: str) -> Dict[str, Any]:
        """
        Analiza una imagen de documento fiscal usando GPT-4 Vision
        """
        print(f"🔍 OpenAI Service: Cliente disponible: {self.client is not None}")
        print(f"🔍 OpenAI Service: API Key configurada: {bool(settings.OPENAI_API_KEY)}")
        
        if not self.client:
            print("⚠️ OpenAI Service: Usando datos de ejemplo - API Key no configurada")
            # Retornar datos de ejemplo si no hay API key configurada
            return self._get_sample_data()
        
        try:
            print(f"🔍 OpenAI Service: Procesando imagen...")
            print(f"🔍 OpenAI Service: Longitud base64: {len(image_base64)}")
            
            # Remover el prefijo data:image si existe
            if image_base64.startswith('data:image'):
                image_base64 = image_base64.split(',')[1]
                print(f"🔍 OpenAI Service: Removido prefijo data:image")
            
            print(f"🔍 OpenAI Service: Enviando a GPT-4...")
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analiza esta imagen de un documento fiscal (boleta, factura, recibo) y extrae la siguiente información en formato JSON:

OBLIGATORIO extraer:
- referencia: Referencia o número de folio del documento
- tipoDocumento: Tipo de documento (Boleta, Factura, Recibo, etc.)
- numeroDocumento: Número del documento
- fecha: Fecha del documento (formato DD/MM/YYYY)
- moneda: Código de moneda (CLP, USD, EUR, etc.)
- nombre: Nombre del proveedor/empresa emisora
- rut: RUT chileno del proveedor (formato XX.XXX.XXX-X)
- total: Monto total del documento
- detalle: Descripción de los productos/servicios
- impuestos: Monto de impuestos si es visible
- porcentaje: Porcentaje de impuestos si es visible

OPCIONAL extraer:
- alias: Nombre comercial o alias del proveedor
- email: Email del proveedor si es visible
- impuestos: Monto de impuestos si es visible
- porcentaje: Porcentaje de impuestos si es visible

IMPORTANTE:
- Si no encuentras un campo, devuelve null
- Para montos, usa solo números (sin símbolos de moneda)
- Para fechas, usa formato DD/MM/YYYY
- Para RUT, usa formato XX.XXX.XXX-X
- Responde SOLO con el JSON, sin explicaciones adicionales"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            # Extraer el JSON de la respuesta
            content = response.choices[0].message.content.strip()
            
            # Limpiar la respuesta para extraer solo el JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                extracted_data = json.loads(json_str)
            else:
                # Si no se encuentra JSON, intentar parsear toda la respuesta
                extracted_data = json.loads(content)
            
            # Validar y limpiar los datos extraídos
            cleaned_data = self._clean_extracted_data(extracted_data)
            
            # Calcular confidence basado en campos encontrados
            confidence = self._calculate_confidence(cleaned_data)
            
            # Determinar campos encontrados y faltantes
            extracted_fields, missing_fields = self._categorize_fields(cleaned_data)
            
            return {
                "documentData": {
                    "referencia": cleaned_data.get("referencia"),
                    "tipoDocumento": cleaned_data.get("tipoDocumento"),
                    "numeroDocumento": cleaned_data.get("numeroDocumento"),
                    "fecha": cleaned_data.get("fecha"),
                    "moneda": cleaned_data.get("moneda")
                },
                "providerData": {
                    "nombre": cleaned_data.get("nombre"),
                    "alias": cleaned_data.get("alias"),
                    "email": cleaned_data.get("email"),
                    "rut": cleaned_data.get("rut")
                },
                "detailsData": {
                    "lineaAsociar": None,  # Campo adicional que puede ser calculado
                    "porcentaje": cleaned_data.get("porcentaje"),
                    "impuestos": cleaned_data.get("impuestos"),
                    "total": cleaned_data.get("total"),
                    "detalle": cleaned_data.get("detalle")
                },
                "confidence": confidence,
                "extractedFields": extracted_fields,
                "missingFields": missing_fields
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON response: {str(e)}")
        except Exception as e:
            raise Exception(f"Error analyzing document: {str(e)}")
    
    def _clean_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpia y valida los datos extraídos
        """
        cleaned = {}
        
        for key, value in data.items():
            if value is None or value == "" or value == "null":
                cleaned[key] = None
            else:
                # Limpiar strings
                if isinstance(value, str):
                    cleaned[key] = value.strip()
                else:
                    cleaned[key] = value
        
        # Validar formato de fecha
        if cleaned.get("fecha"):
            cleaned["fecha"] = self._validate_date_format(cleaned["fecha"])
        
        # Validar formato de RUT
        if cleaned.get("rut"):
            cleaned["rut"] = self._validate_rut_format(cleaned["rut"])
        
        # Limpiar montos (solo números)
        for field in ["total", "impuestos"]:
            if cleaned.get(field):
                cleaned[field] = self._clean_amount(cleaned[field])
        
        return cleaned
    
    def _validate_date_format(self, date_str: str) -> Optional[str]:
        """
        Valida y convierte fecha al formato DD/MM/YYYY
        """
        if not date_str:
            return None
        
        # Patrones de fecha comunes
        patterns = [
            r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})',  # DD/MM/YYYY o DD-MM-YYYY
            r'(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})',  # YYYY/MM/DD o YYYY-MM-DD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                if len(groups[0]) == 4:  # YYYY/MM/DD
                    return f"{groups[2]}/{groups[1]}/{groups[0]}"
                else:  # DD/MM/YYYY
                    return f"{groups[0]}/{groups[1]}/{groups[2]}"
        
        return date_str  # Retornar original si no se puede convertir
    
    def _validate_rut_format(self, rut_str: str) -> Optional[str]:
        """
        Valida y convierte RUT al formato XX.XXX.XXX-X
        """
        if not rut_str:
            return None
        
        # Limpiar RUT
        rut_clean = re.sub(r'[^\d\-kK]', '', rut_str)
        
        # Patrón para RUT chileno
        rut_pattern = r'(\d{1,2})\.?(\d{3})\.?(\d{3})[\-]?([\dkK])'
        match = re.search(rut_pattern, rut_clean)
        
        if match:
            return f"{match.group(1)}.{match.group(2)}.{match.group(3)}-{match.group(4).upper()}"
        
        return rut_str  # Retornar original si no se puede convertir
    
    def _clean_amount(self, amount_str: str) -> Optional[str]:
        """
        Limpia montos para que solo contengan números
        """
        if not amount_str:
            return None
        
        # Extraer solo números y punto decimal
        cleaned = re.sub(r'[^\d\.]', '', str(amount_str))
        
        # Validar que sea un número válido
        try:
            float(cleaned)
            return cleaned
        except ValueError:
            return None
    
    def _calculate_confidence(self, data: Dict[str, Any]) -> int:
        """
        Calcula el nivel de confianza basado en campos encontrados
        """
        required_fields = [
            "referencia", "tipoDocumento", "numeroDocumento", 
            "fecha", "moneda", "nombre", "rut", "total", "detalle"
        ]
        
        optional_fields = ["alias", "email", "impuestos", "porcentaje"]
        
        found_required = sum(1 for field in required_fields if data.get(field) is not None)
        found_optional = sum(1 for field in optional_fields if data.get(field) is not None)
        
        # Calcular confidence: 70% por campos obligatorios + 30% por campos opcionales
        required_score = (found_required / len(required_fields)) * 70
        optional_score = (found_optional / len(optional_fields)) * 30
        
        return int(required_score + optional_score)
    
    def _categorize_fields(self, data: Dict[str, Any]) -> tuple:
        """
        Categoriza campos en encontrados y faltantes
        """
        all_fields = [
            "referencia", "tipoDocumento", "numeroDocumento", 
            "fecha", "moneda", "nombre", "rut", "total", "detalle",
            "alias", "email", "impuestos", "porcentaje"
        ]
        
        extracted_fields = [field for field in all_fields if data.get(field) is not None]
        missing_fields = [field for field in all_fields if data.get(field) is None]
        
        return extracted_fields, missing_fields
    
    def _get_sample_data(self) -> Dict[str, Any]:
        """
        Retorna datos de ejemplo cuando no hay API key configurada
        """
        return {
        }
