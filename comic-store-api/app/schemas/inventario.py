from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TipoMovimientoBase(BaseModel):
    nombre_tipo: str
    descripcion: Optional[str] = None

class TipoMovimiento(TipoMovimientoBase):
    id_tipo_movimiento: int
    
    class Config:
        from_attributes = True

class MovimientoInventarioBase(BaseModel):
    id_producto: int
    id_tipo_movimiento: int
    cantidad: int
    stock_anterior: int
    stock_nuevo: int
    motivo: Optional[str] = None
    id_documento: Optional[int] = None
    tipo_documento: Optional[str] = None

class MovimientoInventarioCreate(BaseModel):
    id_producto: int
    id_tipo_movimiento: int
    cantidad: int
    motivo: Optional[str] = None
    id_documento: Optional[int] = None
    tipo_documento: Optional[str] = None

class MovimientoInventario(MovimientoInventarioBase):
    id_movimiento: int
    id_empleado: Optional[int] = None
    fecha_movimiento: datetime
    
    class Config:
        from_attributes = True

class MovimientoInventarioDetalle(MovimientoInventario):
    tipo_movimiento: TipoMovimiento
    
    class Config:
        from_attributes = True

class AjusteInventario(BaseModel):
    id_producto: int
    nueva_cantidad: int
    motivo: str