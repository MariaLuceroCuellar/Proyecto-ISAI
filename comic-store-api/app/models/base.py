from sqlalchemy import Column, Integer, String, Text
from ..database import Base

class Status(Base):
    __tablename__ = "Status"
    
    id_status = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_status = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    
class Roles(Base):
    __tablename__ = "Roles"
    id_rol = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_rol = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)