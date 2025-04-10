from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, DECIMAL, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base

class EstadoCompraEnum(str, enum.Enum):
    pendiente = "pendiente"
    procesado = "procesado"
    entregado = "entregado"
    cancelado = "cancelado"

class EstadoDetalleCompraEnum(str, enum.Enum):
    pendiente = "pendiente"
    parcial = "parcial"
    completo = "completo"
    cancelado = "cancelado"

class ComprasProveedores(Base):
    __tablename__ = "ComprasProveedores"
    
    id_compra = Column(Integer, primary_key=True, index=True, autoincrement=True)
    numero_compra = Column(String(20), unique=True, nullable=False)
    id_proveedor = Column(Integer, ForeignKey("Proveedores.id_proveedor"), nullable=False)
    fecha_orden = Column(DateTime, default=func.now())
    fecha_estimada_llegada = Column(Date)
    fecha_recepcion = Column(Date)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    impuestos = Column(DECIMAL(10, 2), nullable=False)
    total = Column(DECIMAL(10, 2), nullable=False)
    estado = Column(Enum("pendiente", "procesado", "entregado", "cancelado", name="estado_compra_enum"), default="pendiente")
    id_empleado = Column(Integer, ForeignKey("Empleados.id_empleado", ondelete="SET NULL"))
    notas = Column(Text)
    
    # Relaciones
    proveedor = relationship("Proveedores", back_populates="compras")
    empleado = relationship("Empleados", back_populates="compras")
    detalles = relationship("DetallesCompra", back_populates="compra", cascade="all, delete-orphan")

class DetallesCompra(Base):
    __tablename__ = "DetallesCompra"
    
    id_detalle = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_compra = Column(Integer, ForeignKey("ComprasProveedores.id_compra", ondelete="CASCADE"), nullable=False)
    id_producto = Column(Integer, ForeignKey("Productos.id_producto"), nullable=False)
    cantidad_ordenada = Column(Integer, nullable=False)
    cantidad_recibida = Column(Integer, default=0)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    estado = Column(Enum("pendiente", "parcial", "completo", "cancelado", name="estado_detalle_compra_enum"), default="pendiente")
    
    # Relaciones
    compra = relationship("ComprasProveedores", back_populates="detalles")
    producto = relationship("Productos", back_populates="detalles_compra")