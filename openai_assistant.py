import openai
import logging
import json
from typing import Dict, Any, List
from config import settings

logger = logging.getLogger(__name__)

class OpenAIAssistant:
    def __init__(self):
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Inicializa el cliente de OpenAI"""
        try:
            if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 20:
                self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("✅ OpenAIAssistant: Cliente OpenAI inicializado")
            else:
                logger.warning("⚠️ OpenAIAssistant: API Key no configurada")
        except Exception as e:
            logger.error(f"❌ OpenAIAssistant: Error inicializando cliente: {e}")
            self.client = None

    def process_document(self, image_base64: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un documento usando Chat Completions API"""
        if not self.client:
            logger.error("❌ OpenAIAssistant: Cliente no disponible")
            return self._get_fallback_data(context)

        try:
            # Crear mensaje con imagen
            clean_base64 = self._clean_base64(image_base64)
            logger.info(f"🔍 OpenAIAssistant: Base64 length: {len(clean_base64)}")
            logger.info(f"🔍 OpenAIAssistant: Base64 starts with: {clean_base64[:50]}...")

            # Detectar tipo de imagen automáticamente
            image_type = self._detect_image_type(clean_base64)
            logger.info(f"🔍 OpenAIAssistant: Tipo de imagen detectado: {image_type}")

            # Crear URL de imagen válida
            image_url = f"data:image/{image_type};base64,{clean_base64}"
            logger.info(f"🔍 OpenAIAssistant: URL de imagen creada: {image_url[:100]}...")

            # Usar Chat Completions API con GPT-4 Vision
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un experto en procesamiento de documentos fiscales chilenos. Tu trabajo es:

1. ANALIZAR documentos fiscales (boletas, facturas, recibos, notas de crédito)
2. EXTRAER información estructurada de manera precisa
3. VALIDAR datos extraídos según reglas de negocio chilenas
4. REFINAR resultados cuando sea necesario
5. PROPORCIONAR metadatos de confianza

REGLAS IMPORTANTES:
- Siempre responde en formato JSON válido
- Usa formatos chilenos (DD/MM/YYYY, RUT XX.XXX.XXX-X)
- Valida RUTs chilenos
- Identifica tipos de documentos correctamente
- Extrae datos de contacto cuando estén disponibles
- Calcula confianza basada en completitud y calidad

CAMPOS OBLIGATORIOS A EXTRAER:
- referencia: Número de folio/documento
- tipoDocumento: Tipo de documento
- numeroDocumento: Número del documento
- fecha: Fecha en formato DD/MM/YYYY
- moneda: Código de moneda (CLP, USD, etc.)
- nombre: Nombre del emisor
- rut: RUT del emisor
- total: Monto total
- detalle: Descripción de productos/servicios
- impuestos: Información de impuestos
- email: Correo electrónico si está disponible
- telefono: Teléfono si está disponible
- direccion: Dirección si está disponible

CAMPOS ADICIONALES PARA FACTURAS:
- porcentaje: Porcentaje de IVA
- codigo_postal: Código postal
- ciudad: Ciudad o comuna

Siempre proporciona un score de confianza (0-100) y notas sobre la calidad del procesamiento."""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Analiza este documento fiscal y extrae todos los datos disponibles. Contexto: Usuario {context.get('userData', {}).get('userId', 'N/A')}, Empresa {context.get('userData', {}).get('empresa', 'N/A')}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )

            # Extraer respuesta
            response_text = response.choices[0].message.content
            logger.info(f"🔍 OpenAIAssistant: Respuesta: {response_text[:200]}...")

            # Parsear JSON de la respuesta
            extracted_data = self._parse_json_response(response_text)

            if extracted_data:
                logger.info("✅ OpenAIAssistant: Procesamiento completado")
                return extracted_data
            else:
                logger.warning("⚠️ OpenAIAssistant: No se pudo parsear la respuesta")
                return self._get_fallback_data(context)

        except Exception as e:
            logger.error(f"❌ OpenAIAssistant: Error en process_document: {e}")
            return self._get_fallback_data(context)

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parsea la respuesta JSON del assistant"""
        try:
            # Buscar JSON en la respuesta
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                logger.warning("⚠️ OpenAIAssistant: No se encontró JSON en la respuesta")
                return {}
        except Exception as e:
            logger.error(f"❌ OpenAIAssistant: Error parseando JSON: {e}")
            return {}

    def _clean_base64(self, image_base64: str) -> str:
        """Limpia el base64 removiendo prefijos"""
        if image_base64.startswith('data:image'):
            # Remover el prefijo data:image/jpeg;base64,
            return image_base64.split(',')[1]
        return image_base64

    def _detect_image_type(self, base64_data: str) -> str:
        """Detecta el tipo de imagen basado en los primeros bytes del base64"""
        try:
            # Los primeros caracteres del base64 indican el tipo de imagen
            if base64_data.startswith('iVBORw0KGgo'):
                return 'png'
            elif base64_data.startswith('/9j/'):
                return 'jpeg'
            elif base64_data.startswith('R0lGOD'):
                return 'gif'
            elif base64_data.startswith('UklGR'):
                return 'webp'
            else:
                # Por defecto, asumir JPEG
                return 'jpeg'
        except Exception:
            return 'jpeg'

    def _get_fallback_data(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Datos de fallback cuando el assistant no está disponible"""
        return {
            "referencia": "",
            "tipoDocumento": "Boleta",
            "numeroDocumento": "",
            "fecha": "",
            "moneda": "CLP",
            "nombre": "",
            "rut": "",
            "total": "",
            "detalle": "",
            "impuestos": "",
            "confidence": 0,
            "processing_notes": [
                "Assistant no disponible - datos de ejemplo"
            ],
            "processing_metadata": {
                "agent_type": "OpenAI Chat Completions",
                "assistant_id": "N/A",
                "confidence_score": 0
            }
        }
