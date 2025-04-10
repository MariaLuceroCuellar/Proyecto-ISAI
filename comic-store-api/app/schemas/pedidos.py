from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class EstadoPedidoBase(BaseModel):
    nombre_estado: str
    descripcion: Optional[str] = None

class EstadoPedido(EstadoPedidoBase):
    id_estado: int
    
    class Config:
        from_attributes = True

class DetallePedidoBase(BaseModel):
    id_producto: int
    cantidad: int
    precio_unitario: Decimal
    descuento_unitario: Optional[Decimal] = Decimal("0.0")
    subtotal: Decimal

class DetallePedidoCreate(DetallePedidoBase):
    pass

class DetallePedido(DetallePedidoBase):
    id_detalle: int
    id_pedido: int
    
    class Config:
        from_attributes = True

class PedidoBase(BaseModel):
    numero_pedido: str
    id_cliente: int
    id_empleado: Optional[int] = None
    subtotal: Decimal
    impuestos: Decimal
    descuento: Optional[Decimal] = Decimal("0.0")
    total: Decimal
    id_estado: int
    notas: Optional[str] = None

class PedidoCreate(BaseModel):
    id_cliente: int
    id_empleado: Optional[int] = None
    detalles: List[DetallePedidoCreate]
    notas: Optional[str] = None

class PedidoUpdate(BaseModel):
    id_estado: Optional[int] = None
    notas: Optional[str] = None

class Pedido(PedidoBase):
    id_pedido: int
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class PedidoDetalle(Pedido):
    detalles: List[DetallePedido]
    
    class Config:
        from_attributes = True