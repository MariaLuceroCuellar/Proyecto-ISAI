from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class NivelesMembresia(Base):
    __tablename__ = "NivelesMembresia"
    
    id_nivel = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_nivel = Column(String(50), unique=True, nullable=False)
    descuento_porcentaje = Column(DECIMAL(5, 2), default=0.00)
    puntos_por_compra = Column(Integer, default=1)
    
    # Relaciones
    clientes = relationship("Clientes", back_populates="nivel_membresia")

class Clientes(Base):
    __tablename__ = "Clientes"
    
    id_cliente = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    telefono = Column(String(15))
    fecha_registro = Column(DateTime, default=func.now())
    fecha_ultima_compra = Column(DateTime)
    puntos_acumulados = Column(Integer, default=0)
    id_nivel = Column(Integer, ForeignKey("NivelesMembresia.id_nivel"), default=1)
    id_status = Column(Integer, ForeignKey("Status.id_status"), default=1)
    
    # Relaciones
    nivel_membresia = relationship("NivelesMembresia", back_populates="clientes")
    status = relationship("Status")
    pedidos = relationship("Pedidos", back_populates="cliente")
    historial_membresia = relationship("HistorialMembresia", back_populates="cliente")

class HistorialMembresia(Base):
    __tablename__ = "HistorialMembresia"
    
    id_historial = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_cliente = Column(Integer, ForeignKey("Clientes.id_cliente", ondelete="CASCADE"), nullable=False)
    id_nivel_anterior = Column(Integer, ForeignKey("NivelesMembresia.id_nivel"), nullable=False)
    id_nuevo_nivel = Column(Integer, ForeignKey("NivelesMembresia.id_nivel"), nullable=False)
    fecha_cambio = Column(DateTime, default=func.now())
    motivo = Column(String(255))
    
    # Relaciones
    cliente = relationship("Clientes", back_populates="historial_membresia")
    nivel_anterior = relationship("NivelesMembresia", foreign_keys=[id_nivel_anterior])
    nuevo_nivel = relationship("NivelesMembresia", foreign_keys=[id_nuevo_nivel])