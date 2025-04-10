from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base

class TipoDocumentoEnum(str, enum.Enum):
    pedido = "pedido"
    compra = "compra"
    ajuste = "ajuste"

class TiposMovimiento(Base):
    __tablename__ = "TiposMovimiento"
    
    id_tipo_movimiento = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_tipo = Column(Enum("entrada", "salida", "ajuste", name="tipo_movimiento_enum"), unique=True, nullable=False)
    descripcion = Column(Text)
    
    # Relaciones
    movimientos = relationship("Inventario", back_populates="tipo_movimiento")

class Inventario(Base):
    __tablename__ = "Inventario"
    
    id_movimiento = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_producto = Column(Integer, ForeignKey("Productos.id_producto", ondelete="CASCADE"), nullable=False)
    id_tipo_movimiento = Column(Integer, ForeignKey("TiposMovimiento.id_tipo_movimiento"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    stock_anterior = Column(Integer, nullable=False)
    stock_nuevo = Column(Integer, nullable=False)
    id_empleado = Column(Integer, ForeignKey("Empleados.id_empleado", ondelete="SET NULL"))
    fecha_movimiento = Column(DateTime, default=func.now())
    motivo = Column(String(255))
    id_documento = Column(Integer, comment="Puede ser ID de pedido, compra, etc.")
    tipo_documento = Column(Enum("pedido", "compra", "ajuste", name="tipo_documento_enum"), comment="Tipo de documento relacionado")
    
    # Relaciones
    producto = relationship("Productos", back_populates="inventario")
    tipo_movimiento = relationship("TiposMovimiento", back_populates="movimientos")
    empleado = relationship("Empleados", back_populates="inventario_movimientos")