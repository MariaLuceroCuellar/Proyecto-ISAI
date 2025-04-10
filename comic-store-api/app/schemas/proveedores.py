from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class ProveedorBase(BaseModel):
    nombre: str
    email: EmailStr
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    codigo_postal: Optional[str] = None
    notas: Optional[str] = None
    tiempo_entrega_promedio: Optional[int] = None

class ProveedorCreate(ProveedorBase):
    id_status: Optional[int] = 1

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    codigo_postal: Optional[str] = None
    notas: Optional[str] = None
    tiempo_entrega_promedio: Optional[int] = None
    id_status: Optional[int] = None

class Proveedor(ProveedorBase):
    id_proveedor: int
    id_status: int
    
    class Config:
        from_attributes = True