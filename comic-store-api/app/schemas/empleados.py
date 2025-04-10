from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date

class PuestoBase(BaseModel):
    nombre_puesto: str
    descripcion: Optional[str] = None

class PuestoCreate(PuestoBase):
    pass

class Puesto(PuestoBase):
    id_puesto: int
    
    class Config:
        from_attributes = True

class RolBase(BaseModel):
    nombre_rol: str
    descripcion: Optional[str] = None

class RolCreate(RolBase):
    pass

class Rol(RolBase):
    id_rol: int
    
    class Config:
        from_attributes = True

class EmpleadoBase(BaseModel):
    nombre: str
    apellidos: str
    email: EmailStr
    telefono: Optional[str] = None
    id_puesto: int
    fecha_contratacion: Optional[date] = None
    fecha_nacimiento: Optional[date] = None

class EmpleadoCreate(EmpleadoBase):
    nombre_usuario: str
    password: str
    id_rol: Optional[int] = None
    id_status: Optional[int] = 1

class EmpleadoUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    id_puesto: Optional[int] = None
    fecha_contratacion: Optional[date] = None
    fecha_nacimiento: Optional[date] = None
    id_rol: Optional[int] = None
    id_status: Optional[int] = None

class Empleado(EmpleadoBase):
    id_empleado: int
    id_status: int
    nombre_usuario: str
    id_rol: Optional[int] = None
    ultimo_acceso: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class EmpleadoDetalle(Empleado):
    puesto: Puesto
    rol: Optional[Rol] = None
    
    class Config:
        from_attributes = True

class EmpleadoAdminCreate(EmpleadoCreate):
    id_rol: int