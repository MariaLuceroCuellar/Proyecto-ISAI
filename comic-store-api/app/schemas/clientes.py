from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class NivelMembresiaBase(BaseModel):
    nombre_nivel: str
    descuento_porcentaje: float
    puntos_por_compra: int

class NivelMembresiaCreate(NivelMembresiaBase):
    pass

class NivelMembresia(NivelMembresiaBase):
    id_nivel: int
    
    class Config:
        from_attributes = True

class ClienteBase(BaseModel):
    nombre: str
    apellidos: str
    email: EmailStr
    telefono: Optional[str] = None

class ClienteCreate(ClienteBase):
    id_nivel: Optional[int] = 1
    id_status: Optional[int] = 1

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    puntos_acumulados: Optional[int] = None
    id_nivel: Optional[int] = None
    id_status: Optional[int] = None

class Cliente(ClienteBase):
    id_cliente: int
    fecha_registro: datetime
    fecha_ultima_compra: Optional[datetime] = None
    puntos_acumulados: int
    id_nivel: int
    id_status: int
    
    class Config:
        from_attributes = True

class ClienteDetalle(Cliente):
    nivel_membresia: NivelMembresia
    
    class Config:
        from_attributes = True

class HistorialMembresiaBase(BaseModel):
    id_nivel_anterior: int
    id_nuevo_nivel: int
    motivo: Optional[str] = None

class HistorialMembresiaCreate(HistorialMembresiaBase):
    id_cliente: int

class HistorialMembresia(HistorialMembresiaBase):
    id_historial: int
    id_cliente: int
    fecha_cambio: datetime
    
    class Config:
        from_attributes = True

class UpdateMembresia(BaseModel):
    id_nivel: int
    motivo: Optional[str] = None