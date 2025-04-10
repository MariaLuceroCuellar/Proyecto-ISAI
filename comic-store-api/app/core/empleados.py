from sqlalchemy.orm import Session
from typing import Optional, Dict, List, Any
from ..models.empleados import Empleados, Puestos, Roles
from ..schemas.empleados import EmpleadoCreate, EmpleadoUpdate
from .auth import get_password_hash

def get_empleados(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None, puesto: Optional[int] = None):
    query = db.query(Empleados)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Empleados.nombre.like(search_term)) | 
            (Empleados.apellidos.like(search_term)) | 
            (Empleados.email.like(search_term))
        )
    
    if puesto:
        query = query.filter(Empleados.id_puesto == puesto)
    
    total = query.count()
    empleados = query.offset(skip).limit(limit).all()
    
    return {"data": empleados, "total": total}

def get_empleado_by_id(db: Session, empleado_id: int):
    return db.query(Empleados).filter(Empleados.id_empleado == empleado_id).first()

def get_empleado_by_email(db: Session, email: str):
    return db.query(Empleados).filter(Empleados.email == email).first()

def get_empleado_by_username(db: Session, username: str):
    return db.query(Empleados).filter(Empleados.nombre_usuario == username).first()

def create_empleado(db: Session, empleado: EmpleadoCreate):
    hashed_password = get_password_hash(empleado.password)
    
    db_empleado = Empleados(
        nombre=empleado.nombre,
        apellidos=empleado.apellidos,
        email=empleado.email,
        telefono=empleado.telefono,
        id_puesto=empleado.id_puesto,
        fecha_contratacion=empleado.fecha_contratacion,
        fecha_nacimiento=empleado.fecha_nacimiento,
        id_status=empleado.id_status,
        nombre_usuario=empleado.nombre_usuario,
        password_hash=hashed_password,
        id_rol=empleado.id_rol
    )
    
    db.add(db_empleado)
    db.commit()
    db.refresh(db_empleado)
    return db_empleado

def update_empleado(db: Session, empleado_id: int, empleado: EmpleadoUpdate):
    db_empleado = get_empleado_by_id(db, empleado_id)
    if not db_empleado:
        return None
    
    update_data = empleado.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_empleado, key, value)
    
    db.commit()
    db.refresh(db_empleado)
    return db_empleado

def delete_empleado(db: Session, empleado_id: int):
    db_empleado = get_empleado_by_id(db, empleado_id)
    if not db_empleado:
        return False
    
    db_empleado.id_status = 2  # Inactivo
    db.commit()
    return True

def get_puestos(db: Session):
    return db.query(Puestos).all()

def create_puesto(db: Session, puesto_data: Dict[str, Any]):
    db_puesto = Puestos(**puesto_data)
    db.add(db_puesto)
    db.commit()
    db.refresh(db_puesto)
    return db_puesto

def get_roles(db: Session):
    return db.query(Roles).all()

def create_rol(db: Session, rol_data: Dict[str, Any]):
    db_rol = Roles(**rol_data)
    db.add(db_rol)
    db.commit()
    db.refresh(db_rol)
    return db_rol