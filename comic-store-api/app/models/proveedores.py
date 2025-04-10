from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Proveedores(Base):
    __tablename__ = "Proveedores"
    
    id_proveedor = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    telefono = Column(String(15))
    direccion = Column(String(255))
    ciudad = Column(String(100))
    estado = Column(String(100))
    codigo_postal = Column(String(10))
    notas = Column(Text)
    tiempo_entrega_promedio = Column(Integer, comment="En días")
    id_status = Column(Integer, ForeignKey("Status.id_status"), default=1)
    
    # Relaciones
    status = relationship("Status")
    productos = relationship("Productos", back_populates="proveedor")
    compras = relationship("ComprasProveedores", back_populates="proveedor")