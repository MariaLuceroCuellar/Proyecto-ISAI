from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

class DetalleCompraBase(BaseModel):
    id_producto: int
    cantidad_ordenada: int
    precio_unitario: float
    subtotal: float

class DetalleCompraCreate(DetalleCompraBase):
    pass

class DetalleCompra(DetalleCompraBase):
    id_detalle: int
    id_compra: int
    cantidad_recibida: int = 0
    estado: str
    
    class Config:
        from_attributes = True

class CompraBase(BaseModel):
    numero_compra: str
    id_proveedor: int
    fecha_estimada_llegada: Optional[date] = None
    subtotal: float
    impuestos: float
    total: float
    estado: Optional[str] = "pendiente"
    id_empleado: Optional[int] = None
    notas: Optional[str] = None

class CompraCreate(BaseModel):
    id_proveedor: int
    fecha_estimada_llegada: Optional[date] = None
    detalles: List[DetalleCompraCreate]
    id_empleado: Optional[int] = None
    notas: Optional[str] = None

class CompraUpdate(BaseModel):
    fecha_estimada_llegada: Optional[date] = None
    estado: Optional[str] = None
    notas: Optional[str] = None

class Compra(CompraBase):
    id_compra: int
    fecha_orden: datetime
    fecha_recepcion: Optional[date] = None
    
    class Config:
        from_attributes = True

class CompraDetalle(Compra):
    detalles: List[DetalleCompra]
    
    class Config:
        from_attributes = True

class RecepcionCompra(BaseModel):
    fecha_recepcion: date
    detalles: List[dict]  # Lista de {id_detalle, cantidad_recibida}