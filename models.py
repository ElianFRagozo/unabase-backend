from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserData(BaseModel):
    userId: str
    empresa: str

class ProcessDocumentRequest(BaseModel):
    image: str = Field(..., description="Base64 encoded image data")
    expenseId: str
    userData: UserData

class DocumentData(BaseModel):
    referencia: Optional[str] = None
    tipoDocumento: Optional[str] = None
    numeroDocumento: Optional[str] = None
    fecha: Optional[str] = None
    moneda: Optional[str] = None
    nombre: Optional[str] = None
    rut: Optional[str] = None
    total: Optional[str] = None
    detalle: Optional[str] = None

class ProviderData(BaseModel):
    nombre: Optional[str] = None
    alias: Optional[str] = None
    email: Optional[str] = None
    rut: Optional[str] = None

class DetailsData(BaseModel):
    lineaAsociar: Optional[str] = None
    porcentaje: Optional[str] = None
    impuestos: Optional[str] = None
    total: Optional[str] = None
    detalle: Optional[str] = None

class ProcessDocumentResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ValidateDataRequest(BaseModel):
    extractedData: Dict[str, Any]
    confidence: int = Field(..., ge=0, le=100)

class ValidateDataResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
