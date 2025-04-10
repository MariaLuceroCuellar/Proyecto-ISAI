from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class EstadosPedido(Base):
    __tablename__ = "EstadosPedido"
    
    id_estado = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_estado = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    
    # Relaciones
    pedidos = relationship("Pedidos", back_populates="estado")

class Pedidos(Base):
    __tablename__ = "Pedidos"
    
    id_pedido = Column(Integer, primary_key=True, index=True, autoincrement=True)
    numero_pedido = Column(String(20), unique=True, nullable=False)
    fecha_creacion = Column(DateTime, default=func.now())
    id_cliente = Column(Integer, ForeignKey("Clientes.id_cliente", ondelete="CASCADE"), nullable=False)
    id_empleado = Column(Integer, ForeignKey("Empleados.id_empleado", ondelete="SET NULL"))
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    impuestos = Column(DECIMAL(10, 2), nullable=False)
    descuento = Column(DECIMAL(10, 2), default=0.00)
    total = Column(DECIMAL(10, 2), nullable=False)
    id_estado = Column(Integer, ForeignKey("EstadosPedido.id_estado"), nullable=False)
    notas = Column(Text)
    
    # Relaciones
    cliente = relationship("Clientes", back_populates="pedidos")
    empleado = relationship("Empleados", back_populates="pedidos")
    estado = relationship("EstadosPedido", back_populates="pedidos")
    detalles = relationship("DetallesPedido", back_populates="pedido", cascade="all, delete-orphan")

class DetallesPedido(Base):
    __tablename__ = "DetallesPedido"
    
    id_detalle = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_pedido = Column(Integer, ForeignKey("Pedidos.id_pedido", ondelete="CASCADE"), nullable=False)
    id_producto = Column(Integer, ForeignKey("Productos.id_producto", ondelete="CASCADE"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    descuento_unitario = Column(DECIMAL(10, 2), default=0.00)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    
    # Relaciones
    pedido = relationship("Pedidos", back_populates="detalles")
    producto = relationship("Productos", back_populates="detalles_pedido")