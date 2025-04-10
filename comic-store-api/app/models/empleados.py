from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
from .logs import LogsSistema

class Puestos(Base):
    __tablename__ = "Puestos"
    
    id_puesto = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_puesto = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)
    
    # Relaciones
    empleados = relationship("Empleados", back_populates="puesto")

class Empleados(Base):
    __tablename__ = "Empleados"
    
    id_empleado = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    telefono = Column(String(15))
    id_puesto = Column(Integer, ForeignKey("Puestos.id_puesto"), nullable=False)
    fecha_contratacion = Column(Date)
    fecha_nacimiento = Column(Date)
    id_status = Column(Integer, ForeignKey("Status.id_status"), default=1)
    
    # Campos para usuario del sistema
    nombre_usuario = Column(String(50), unique=True)
    password_hash = Column(String(255))
    id_rol = Column(Integer, ForeignKey("Roles.id_rol"))
    ultimo_acceso = Column(DateTime)
    
    # Relaciones
    puesto = relationship("Puestos", back_populates="empleados")
    status = relationship("Status")
    rol = relationship("Roles")
    pedidos = relationship("Pedidos", back_populates="empleado")
    inventario_movimientos = relationship("Inventario", back_populates="empleado")
    compras = relationship("ComprasProveedores", back_populates="empleado")
    logs = relationship("LogsSistema", back_populates="empleado")