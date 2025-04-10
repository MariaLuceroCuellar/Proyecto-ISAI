from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base

class TipoAccionEnum(str, enum.Enum):
    crear = "crear"
    leer = "leer"
    actualizar = "actualizar"
    eliminar = "eliminar"
    login = "login"
    logout = "logout"
    error = "error"

class LogsSistema(Base):
    __tablename__ = "LogsSistema"
    
    id_log = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tipo_accion = Column(Enum("crear", "leer", "actualizar", "eliminar", "login", "logout", "error", name="tipo_accion_enum"), nullable=False)
    tabla_afectada = Column(String(100))
    id_registro_afectado = Column(Integer)
    fecha_hora = Column(DateTime, default=func.now())
    ip_usuario = Column(String(45))
    id_empleado = Column(Integer, ForeignKey("Empleados.id_empleado", ondelete="SET NULL"))
    detalle = Column(Text)
    
    # Relaciones
    empleado = relationship("Empleados", back_populates="logs")