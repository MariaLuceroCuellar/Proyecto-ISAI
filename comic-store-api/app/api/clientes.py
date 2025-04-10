from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.clientes import Clientes, NivelesMembresia, HistorialMembresia
from ..schemas.clientes import (
    Cliente, ClienteCreate, ClienteUpdate, ClienteDetalle,
    NivelMembresia, UpdateMembresia, HistorialMembresia as HistorialMembresiaSchema
)
from ..dependencies import get_current_active_user, get_admin_user
from ..models.empleados import Empleados

router = APIRouter()

# Obtener todos los clientes (con paginación y filtros)
@router.get("/", response_model=List[Cliente], summary="Obtener lista de clientes")
async def get_clientes(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(100, description="Número máximo de registros a devolver"),
    search: Optional[str] = Query(None, description="Buscar por nombre, apellidos o email"),
    nivel: Optional[int] = Query(None, description="Filtrar por nivel de membresía"),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene la lista de clientes con paginación y filtros opcionales.
    
    - **skip**: Número de registros a omitir (para paginación)
    - **limit**: Número máximo de registros a devolver
    - **search**: Búsqueda por nombre, apellidos o email
    - **nivel**: Filtrar por nivel de membresía
    """
    query = db.query(Clientes)
    
    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Clientes.nombre.like(search_term)) | 
            (Clientes.apellidos.like(search_term)) | 
            (Clientes.email.like(search_term))
        )
    
    if nivel:
        query = query.filter(Clientes.id_nivel == nivel)
    
    return query.offset(skip).limit(limit).all()

# Obtener un cliente por ID
@router.get("/{cliente_id}", response_model=ClienteDetalle, summary="Obtener cliente por ID")
async def get_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene los detalles de un cliente específico por su ID.
    
    - **cliente_id**: ID del cliente a consultar
    """
    cliente = db.query(Clientes).filter(Clientes.id_cliente == cliente_id).first()
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    return cliente

# Crear un nuevo cliente
@router.post("/", response_model=Cliente, status_code=status.HTTP_201_CREATED, summary="Crear nuevo cliente")
async def create_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Crea un nuevo cliente en el sistema.
    
    - **nombre**: Nombre del cliente
    - **apellidos**: Apellidos del cliente
    - **email**: Email del cliente (debe ser único)
    - **telefono**: Teléfono del cliente (opcional)
    - **id_nivel**: ID del nivel de membresía (opcional, predeterminado: 1)
    - **id_status**: ID del estado del cliente (opcional, predeterminado: 1)
    """
    # Verificar si el email ya existe
    db_cliente = db.query(Clientes).filter(Clientes.email == cliente.email).first()
    if db_cliente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El email {cliente.email} ya está registrado"
        )
    
    # Verificar si el nivel de membresía existe
    nivel = db.query(NivelesMembresia).filter(NivelesMembresia.id_nivel == cliente.id_nivel).first()
    if not nivel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nivel de membresía con ID {cliente.id_nivel} no existe"
        )
    
    # Crear nuevo cliente
    db_cliente = Clientes(**cliente.model_dump())
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    
    return db_cliente

# Actualizar un cliente
@router.put("/{cliente_id}", response_model=Cliente, summary="Actualizar cliente")
async def update_cliente(
    cliente_id: int,
    cliente_update: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Actualiza los datos de un cliente existente.
    
    - **cliente_id**: ID del cliente a actualizar
    - **cliente_update**: Datos del cliente a actualizar (cualquier campo es opcional)
    """
    # Verificar si el cliente existe
    db_cliente = db.query(Clientes).filter(Clientes.id_cliente == cliente_id).first()
    if db_cliente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    
    # Verificar si el email ya existe (si se está actualizando)
    if cliente_update.email and cliente_update.email != db_cliente.email:
        exists = db.query(Clientes).filter(Clientes.email == cliente_update.email).first()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El email {cliente_update.email} ya está registrado"
            )
    
    # Verificar si el nivel de membresía existe (si se está actualizando)
    if cliente_update.id_nivel:
        nivel = db.query(NivelesMembresia).filter(NivelesMembresia.id_nivel == cliente_update.id_nivel).first()
        if not nivel:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nivel de membresía con ID {cliente_update.id_nivel} no existe"
            )
    
    # Actualizar cliente
    update_data = cliente_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cliente, key, value)
    
    db.commit()
    db.refresh(db_cliente)
    
    return db_cliente

# Eliminar un cliente (soft delete)
@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar cliente")
async def delete_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_admin_user)  # Solo administradores
):
    """
    Elimina un cliente del sistema (soft delete).
    
    - **cliente_id**: ID del cliente a eliminar
    """
    # Verificar si el cliente existe
    db_cliente = db.query(Clientes).filter(Clientes.id_cliente == cliente_id).first()
    if db_cliente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    
    # Soft delete (cambiar status a inactivo - asumiendo que 2 es "inactivo")
    db_cliente.id_status = 2
    db.commit()
    
    return None

# Obtener membresía de un cliente
@router.get("/{cliente_id}/membresia", response_model=NivelMembresia, summary="Obtener membresía de cliente")
async def get_membresia(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene los detalles de la membresía de un cliente.
    
    - **cliente_id**: ID del cliente
    """
    # Verificar si el cliente existe
    cliente = db.query(Clientes).filter(Clientes.id_cliente == cliente_id).first()
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    
    nivel = db.query(NivelesMembresia).filter(NivelesMembresia.id_nivel == cliente.id_nivel).first()
    return nivel

# Actualizar membresía de un cliente
@router.put("/{cliente_id}/membresia", response_model=Cliente, summary="Actualizar membresía de cliente")
async def update_membresia(
    cliente_id: int,
    membresia: UpdateMembresia,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Actualiza el nivel de membresía de un cliente y registra el cambio en el historial.
    
    - **cliente_id**: ID del cliente
    - **id_nivel**: Nuevo ID de nivel de membresía
    - **motivo**: Motivo del cambio (opcional)
    """
    # Verificar si el cliente existe
    cliente = db.query(Clientes).filter(Clientes.id_cliente == cliente_id).first()
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    
    # Verificar si el nivel de membresía existe
    nivel = db.query(NivelesMembresia).filter(NivelesMembresia.id_nivel == membresia.id_nivel).first()
    if not nivel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nivel de membresía con ID {membresia.id_nivel} no existe"
        )
    
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

# Obtener historial de membresía
@router.get("/{cliente_id}/historial-membresia", response_model=List[HistorialMembresiaSchema], summary="Obtener historial de membresía")
async def get_historial_membresia(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene el historial de cambios de membresía de un cliente.
    
    - **cliente_id**: ID del cliente
    """
    # Verificar si el cliente existe
    cliente = db.query(Clientes).filter(Clientes.id_cliente == cliente_id).first()
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    
    historial = db.query(HistorialMembresia).filter(
        HistorialMembresia.id_cliente == cliente_id
    ).order_by(HistorialMembresia.fecha_cambio.desc()).all()
    
    return historial