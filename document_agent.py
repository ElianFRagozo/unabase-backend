#!/usr/bin/env python3
"""
Agente inteligente de OpenAI para procesamiento de documentos fiscales
"""
import openai
import base64
import json
import re
from typing import Dict, Any, Optional, List
from config import settings
import logging

logger = logging.getLogger(__name__)

class DocumentAgent:
    """
    Agente inteligente que procesa documentos fiscales usando OpenAI
    """
    
    def __init__(self):
        self.client = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Inicializa el cliente de OpenAI"""
        try:
            if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 20:
                self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("✅ DocumentAgent: Cliente OpenAI inicializado")
            else:
                logger.warning("⚠️ DocumentAgent: API Key no configurada")
        except Exception as e:
            logger.error(f"❌ DocumentAgent: Error inicializando cliente: {e}")
            self.client = None
    
    def process_document(self, image_base64: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa un documento fiscal usando el agente inteligente
        
        Args:
            image_base64: Imagen del documento en base64
            context: Contexto adicional (usuario, empresa, etc.)
        
        Returns:
            Dict con los datos extraídos y metadatos del procesamiento
        """
        if not self.client:
            return self._get_fallback_data(context)
        
        try:
            # Paso 1: Análisis inicial del documento
            document_analysis = self._analyze_document_type(image_base64)
            
            # Paso 2: Extracción específica según el tipo
            extracted_data = self._extract_document_data(image_base64, document_analysis)
            
            # Paso 3: Validación y refinamiento
            validated_data = self._validate_and_refine(extracted_data, document_analysis)
            
            # Paso 3.5: Refinamiento iterativo para campos faltantes
            refined_data = self._iterative_refinement(validated_data, image_base64, document_analysis)
            
            # Paso 4: Generar metadatos de confianza
            confidence_metadata = self._generate_confidence_metadata(refined_data, document_analysis)
            
            # Combinar todos los resultados
            result = {
                **refined_data,
                **confidence_metadata,
                "processing_metadata": {
                    "agent_version": "1.0.0",
                    "processing_steps": len([document_analysis, extracted_data, validated_data]),
                    "document_type": document_analysis.get("type", "unknown"),
                    "confidence_score": confidence_metadata.get("confidence", 0)
                }
            }
            
            logger.info(f"✅ DocumentAgent: Procesamiento completado con confianza {confidence_metadata.get('confidence', 0)}%")
            return result
            
        except Exception as e:
            logger.error(f"❌ DocumentAgent: Error procesando documento: {e}")
            return self._get_fallback_data(context)
    
    def _analyze_document_type(self, image_base64: str) -> Dict[str, Any]:
        """
        Analiza el tipo de documento y sus características
        """
        try:
            # Limpiar base64
            clean_base64 = self._clean_base64(image_base64)
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un experto en análisis de documentos fiscales chilenos. 
                        Analiza la imagen y determina:
                        1. Tipo de documento (Boleta, Factura, Recibo, Nota de Crédito, etc.)
                        2. Calidad de la imagen (buena, media, mala)
                        3. Idioma del documento (español, inglés, etc.)
                        4. Formato (digital, escaneado, fotografía)
                        5. Complejidad (simple, moderada, compleja)
                        
                        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido, sin texto adicional.
                        Ejemplo: {"type": "Boleta", "quality": "buena", "language": "es", "format": "digital", "complexity": "simple"}"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analiza este documento fiscal y determina su tipo y características:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{clean_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            analysis_text = response.choices[0].message.content
            logger.info(f"🔍 DocumentAgent: Respuesta análisis: {analysis_text[:200]}...")
            return self._parse_json_response(analysis_text)
            
        except Exception as e:
            logger.error(f"Error analizando tipo de documento: {e}")
            return {"type": "unknown", "quality": "unknown", "language": "es", "format": "unknown", "complexity": "simple"}
    
    def _extract_document_data(self, image_base64: str, document_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae datos específicos según el tipo de documento
        """
        try:
            clean_base64 = self._clean_base64(image_base64)
            doc_type = document_analysis.get("type", "Boleta")
            
            # Prompt específico según el tipo de documento
            extraction_prompt = self._get_extraction_prompt(doc_type)
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"""Eres un experto en extracción de datos de documentos fiscales chilenos.
{extraction_prompt}
                        
IMPORTANTE:
- Extrae SOLO datos que estén claramente visibles
- Si un campo no es visible, déjalo vacío
- Usa formato de fecha DD/MM/YYYY
- Usa formato de RUT XX.XXX.XXX-X
- Los montos deben ser números sin símbolos de moneda
- Responde ÚNICAMENTE en formato JSON válido, sin texto adicional
- Ejemplo: {{"referencia": "12345", "tipoDocumento": "Boleta", "fecha": "15/10/2024", "total": "15000"}}"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Extrae los datos de este {doc_type}:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{clean_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            extracted_text = response.choices[0].message.content
            logger.info(f"🔍 DocumentAgent: Respuesta extracción: {extracted_text[:200]}...")
            return self._parse_json_response(extracted_text)
            
        except Exception as e:
            logger.error(f"Error extrayendo datos: {e}")
            return {}
    
    def _validate_and_refine(self, extracted_data: Dict[str, Any], document_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida y refina los datos extraídos
        """
        try:
            # Si no hay datos extraídos, devolver datos vacíos
            if not extracted_data or extracted_data.get("error"):
                logger.warning("⚠️ DocumentAgent: No hay datos para validar")
                return {
                    "referencia": "",
                    "tipoDocumento": document_analysis.get("type", "Boleta"),
                    "numeroDocumento": "",
                    "fecha": "",
                    "moneda": "CLP",
                    "nombre": "",
                    "rut": "",
                    "total": "",
                    "detalle": "",
                    "impuestos": "",
                    "porcentaje": ""
                }
            
            validation_prompt = f"""
Valida y refina estos datos extraídos de un {document_analysis.get('type', 'documento')}:

Datos extraídos: {json.dumps(extracted_data, indent=2)}

Reglas de validación:
1. Fecha debe estar en formato DD/MM/YYYY
2. RUT debe estar en formato XX.XXX.XXX-X
3. Montos deben ser números válidos
4. Nombres no deben estar vacíos
5. Referencias deben ser alfanuméricas

Corrige cualquier error y devuelve los datos validados en formato JSON.

IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido, sin texto adicional.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": validation_prompt
                    }
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            validated_text = response.choices[0].message.content
            logger.info(f"🔍 DocumentAgent: Respuesta validación: {validated_text[:200]}...")
            return self._parse_json_response(validated_text)
            
        except Exception as e:
            logger.error(f"Error validando datos: {e}")
            return extracted_data
    
    def _iterative_refinement(self, validated_data: Dict[str, Any], image_base64: str, document_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refinamiento iterativo para campos faltantes importantes
        """
        try:
            # Detectar campos faltantes importantes
            missing_fields = self._detect_missing_important_fields(validated_data)
            
            if not missing_fields:
                logger.info("✅ DocumentAgent: Todos los campos importantes están presentes")
                return validated_data
            
            logger.info(f"🔄 DocumentAgent: Campos faltantes detectados: {missing_fields}")
            
            # Procesar imagen nuevamente con instrucciones específicas
            refined_data = self._refine_with_specific_instructions(
                image_base64, 
                validated_data, 
                missing_fields, 
                document_analysis
            )
            
            # Combinar datos originales con refinamientos
            final_data = {**validated_data, **refined_data}
            
            logger.info(f"✅ DocumentAgent: Refinamiento completado. Campos añadidos: {list(refined_data.keys())}")
            return final_data
            
        except Exception as e:
            logger.error(f"Error en refinamiento iterativo: {e}")
            return validated_data
    
    def _detect_missing_important_fields(self, data: Dict[str, Any]) -> List[str]:
        """
        Detecta campos importantes que están faltantes
        """
        important_fields = {
            "email": ["email", "correo", "e-mail", "mail"],
            "telefono": ["telefono", "teléfono", "fono", "phone"],
            "direccion": ["direccion", "dirección", "address", "domicilio"],
            "ciudad": ["ciudad", "city", "comuna"],
            "codigo_postal": ["codigo_postal", "código postal", "postal", "zip"]
        }
        
        missing = []
        
        for field_name, variations in important_fields.items():
            # Verificar si el campo está vacío o no existe
            field_value = data.get(field_name, "")
            if not field_value or field_value.strip() == "":
                # Verificar si hay alguna variación del campo
                found_variation = False
                for variation in variations:
                    if data.get(variation, "").strip():
                        found_variation = True
                        break
                
                if not found_variation:
                    missing.append(field_name)
        
        return missing
    
    def _refine_with_specific_instructions(self, image_base64: str, current_data: Dict[str, Any], missing_fields: List[str], document_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refina la extracción con instrucciones específicas para campos faltantes
        """
        try:
            clean_base64 = self._clean_base64(image_base64)
            
            # Crear instrucciones específicas para campos faltantes
            specific_instructions = self._create_specific_instructions(missing_fields)
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"""Eres un experto en extracción de datos de documentos fiscales chilenos.
                        
{specific_instructions}

IMPORTANTE:
- Busca ESPECÍFICAMENTE los campos que faltan
- Si encuentras un campo, extráelo
- Si no lo encuentras, déjalo vacío
- Responde ÚNICAMENTE en formato JSON válido
- Ejemplo: {{"email": "contacto@empresa.cl", "telefono": "+56912345678"}}"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Busca específicamente estos campos en el documento: {', '.join(missing_fields)}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{clean_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            refined_text = response.choices[0].message.content
            logger.info(f"🔍 DocumentAgent: Respuesta refinamiento: {refined_text[:200]}...")
            return self._parse_json_response(refined_text)
            
        except Exception as e:
            logger.error(f"Error en refinamiento específico: {e}")
            return {}
    
    def _create_specific_instructions(self, missing_fields: List[str]) -> str:
        """
        Crea instrucciones específicas para campos faltantes
        """
        instructions = []
        
        for field in missing_fields:
            if field == "email":
                instructions.append("""
                - email: Busca direcciones de correo electrónico (formato: usuario@dominio.com)
                  Busca en: pie de página, encabezado, datos de contacto, información de la empresa
                """)
            elif field == "telefono":
                instructions.append("""
                - telefono: Busca números de teléfono (formato: +56912345678, 9-1234-5678, etc.)
                  Busca en: datos de contacto, información de la empresa, pie de página
                """)
            elif field == "direccion":
                instructions.append("""
                - direccion: Busca dirección física completa
                  Busca en: datos de la empresa, información de contacto, pie de página
                """)
            elif field == "ciudad":
                instructions.append("""
                - ciudad: Busca ciudad o comuna
                  Busca en: dirección, datos de la empresa, información de contacto
                """)
            elif field == "codigo_postal":
                instructions.append("""
                - codigo_postal: Busca código postal o ZIP
                  Busca en: dirección, datos de la empresa
                """)
        
        return "\n".join(instructions)
    
    def _generate_confidence_metadata(self, validated_data: Dict[str, Any], document_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera metadatos de confianza basados en la calidad de extracción
        """
        try:
            # Calcular confianza basada en campos completos
            required_fields = ["referencia", "fecha", "total", "nombre"]
            completed_fields = sum(1 for field in required_fields if validated_data.get(field))
            base_confidence = (completed_fields / len(required_fields)) * 100
            
            # Ajustar según calidad de imagen
            quality_multiplier = {
                "buena": 1.0,
                "media": 0.8,
                "mala": 0.6
            }.get(document_analysis.get("quality", "media"), 0.8)
            
            final_confidence = min(int(base_confidence * quality_multiplier), 100)
            
            return {
                "confidence": final_confidence,
                "quality_assessment": document_analysis.get("quality", "unknown"),
                "completeness_score": completed_fields,
                "processing_notes": self._generate_processing_notes(validated_data, document_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error generando metadatos: {e}")
            return {"confidence": 0, "quality_assessment": "unknown", "completeness_score": 0}
    
    def _get_extraction_prompt(self, doc_type: str) -> str:
        """Obtiene el prompt de extracción específico para el tipo de documento"""
        prompts = {
            "Boleta": """
            Extrae de esta BOLETA:
            - referencia: Número de folio
            - tipoDocumento: "Boleta"
            - numeroDocumento: Número de la boleta
            - fecha: Fecha de emisión
            - moneda: "CLP"
            - nombre: Nombre del local/comercio
            - rut: RUT del comercio
            - total: Monto total
            - detalle: Productos/servicios
            - impuestos: IVA si es visible
            """,
            "Factura": """
            Extrae de esta FACTURA:
            - referencia: Número de folio
            - tipoDocumento: "Factura"
            - numeroDocumento: Número de factura
            - fecha: Fecha de emisión
            - moneda: Moneda (CLP, USD, etc.)
            - nombre: Razón social del emisor
            - rut: RUT del emisor
            - total: Monto total
            - detalle: Descripción de servicios/productos
            - impuestos: IVA y otros impuestos
            """,
            "Recibo": """
            Extrae de este RECIBO:
            - referencia: Número de recibo
            - tipoDocumento: "Recibo"
            - numeroDocumento: Número del recibo
            - fecha: Fecha de emisión
            - moneda: Moneda
            - nombre: Nombre del emisor
            - rut: RUT del emisor
            - total: Monto total
            - detalle: Concepto del pago
            - impuestos: Si aplica
            """,
            "Factura Electrónica": """
            Extrae de esta FACTURA ELECTRÓNICA:
            - referencia: Número de folio
            - tipoDocumento: "Factura Electrónica"
            - numeroDocumento: Número de factura
            - fecha: Fecha de emisión
            - moneda: Moneda (CLP, USD, etc.)
            - nombre: Razón social del emisor
            - rut: RUT del emisor
            - total: Monto total
            - detalle: Descripción de servicios/productos
            - impuestos: IVA y otros impuestos
            - porcentaje: Porcentaje de IVA si es visible
            """
        }
        return prompts.get(doc_type, prompts["Boleta"])
    
    def _clean_base64(self, image_base64: str) -> str:
        """Limpia el base64 removiendo prefijos"""
        if image_base64.startswith('data:image'):
            return image_base64.split(',')[1]
        return image_base64
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """
        Parsea una respuesta de OpenAI que puede contener JSON con texto adicional
        """
        try:
            # Intentar parsear directamente
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                # Buscar JSON entre ```json y ```
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                
                # Buscar JSON entre { y }
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                
                # Buscar JSON al inicio de la respuesta
                lines = text.strip().split('\n')
                for line in lines:
                    if line.strip().startswith('{'):
                        return json.loads(line)
                
                logger.warning(f"⚠️ DocumentAgent: No se pudo extraer JSON de: {text[:100]}...")
                return {}
                
            except Exception as e:
                logger.error(f"❌ DocumentAgent: Error parseando JSON: {e}")
                return {}
    
    def _generate_processing_notes(self, data: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Genera notas sobre el procesamiento"""
        notes = []
        
        if analysis.get("quality") == "mala":
            notes.append("Imagen de baja calidad - algunos datos pueden ser imprecisos")
        
        if not data.get("rut"):
            notes.append("RUT no detectado - verificar manualmente")
        
        if not data.get("fecha"):
            notes.append("Fecha no detectada - verificar manualmente")
        
        if data.get("confidence", 0) < 70:
            notes.append("Confianza baja - revisar datos extraídos")
        
        return notes
    
    def _get_fallback_data(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Datos de fallback cuando el agente no está disponible"""
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
            "confidence": 0,
            "quality_assessment": "unknown",
            "processing_notes": ["Agente no disponible - datos de ejemplo"],
            "processing_metadata": {
                "agent_version": "1.0.0",
                "processing_steps": 0,
                "document_type": "unknown",
                "confidence_score": 0
            }
        }
