from sqlalchemy.orm import Session
from typing import Optional, Dict, List, Any
from ..models.clientes import Clientes, NivelesMembresia, HistorialMembresia
from ..schemas.clientes import ClienteCreate, ClienteUpdate, UpdateMembresia

def get_clientes(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None, nivel: Optional[int] = None):
    query = db.query(Clientes)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Clientes.nombre.like(search_term)) | 
            (Clientes.apellidos.like(search_term)) | 
            (Clientes.email.like(search_term))
        )
    
    if nivel:
        query = query.filter(Clientes.id_nivel == nivel)
    
    total = query.count()
    clientes = query.offset(skip).limit(limit).all()
    
    return {"data": clientes, "total": total}

def get_cliente_by_id(db: Session, cliente_id: int):
    return db.query(Clientes).filter(Clientes.id_cliente == cliente_id).first()

def get_cliente_by_email(db: Session, email: str):
    return db.query(Clientes).filter(Clientes.email == email).first()

def create_cliente(db: Session, cliente: ClienteCreate):
    db_cliente = Clientes(**cliente.model_dump())
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

def update_cliente(db: Session, cliente_id: int, cliente: ClienteUpdate):
    db_cliente = get_cliente_by_id(db, cliente_id)
    if not db_cliente:
        return None
    
    update_data = cliente.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cliente, key, value)
    
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

def delete_cliente(db: Session, cliente_id: int):
    db_cliente = get_cliente_by_id(db, cliente_id)
    if not db_cliente:
        return False
    
    db_cliente.id_status = 2  # Inactivo
    db.commit()
    return True

def get_niveles_membresia(db: Session):
    return db.query(NivelesMembresia).all()

def get_historial_membresia(db: Session, cliente_id: int):
    return db.query(HistorialMembresia).filter(
        HistorialMembresia.id_cliente == cliente_id
    ).order_by(HistorialMembresia.fecha_cambio.desc()).all()

def update_membresia(db: Session, cliente_id: int, membresia: UpdateMembresia):
    cliente = get_cliente_by_id(db, cliente_id)
    if not cliente:
        return None
    
    # Si el nivel es el mismo, no hacer cambios
    if cliente.id_nivel == membresia.id_nivel:
        return cliente
    
    # Guardar nivel anterior
    id_nivel_anterior = cliente.id_nivel
    
    # Actualizar nivel
    cliente.id_nivel = membresia.id_nivel
    
    # Registrar en historial
    historial = HistorialMembresia(
        id_cliente=cliente_id,
        id_nivel_anterior=id_nivel_anterior,
        id_nuevo_nivel=membresia.id_nivel,
        motivo=membresia.motivo
    )
    
    db.add(historial)
    db.commit()
    db.refresh(cliente)
    
    return cliente