from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.proveedores import Proveedores
from ..schemas.proveedores import (
    Proveedor, ProveedorCreate, ProveedorUpdate
)
from ..dependencies import get_current_active_user, get_admin_user
from ..models.empleados import Empleados

router = APIRouter()

# Obtener todos los proveedores
@router.get("/", response_model=List[Proveedor], summary="Obtener lista de proveedores")
async def get_proveedores(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(100, description="Número máximo de registros a devolver"),
    search: Optional[str] = Query(None, description="Buscar por nombre o email"),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene la lista de proveedores con paginación y filtros opcionales.
    """
    query = db.query(Proveedores)
    
    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Proveedores.nombre.like(search_term)) | 
            (Proveedores.email.like(search_term))
        )
    
    return query.order_by(Proveedores.nombre).offset(skip).limit(limit).all()

# Obtener un proveedor por ID
@router.get("/{proveedor_id}", response_model=Proveedor, summary="Obtener proveedor por ID")
async def get_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene los detalles de un proveedor específico por su ID.
    """
    proveedor = db.query(Proveedores).filter(Proveedores.id_proveedor == proveedor_id).first()
    if proveedor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proveedor con ID {proveedor_id} no encontrado"
        )
    return proveedor

# Crear un nuevo proveedor
@router.post("/", response_model=Proveedor, status_code=status.HTTP_201_CREATED, summary="Crear nuevo proveedor")
async def create_proveedor(
    proveedor: ProveedorCreate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_admin_user)  # Solo administradores
):
    """
    Crea un nuevo proveedor en el sistema.
    """
    # Verificar si el email ya existe
    db_proveedor = db.query(Proveedores).filter(Proveedores.email == proveedor.email).first()
    if db_proveedor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El email {proveedor.email} ya está registrado"
        )
    
    # Crear nuevo proveedor
    db_proveedor = Proveedores(**proveedor.model_dump())
    db.add(db_proveedor)
    db.commit()
    db.refresh(db_proveedor)
    
    return db_proveedor

# Actualizar un proveedor
@router.put("/{proveedor_id}", response_model=Proveedor, summary="Actualizar proveedor")
async def update_proveedor(
    proveedor_id: int,
    proveedor_update: ProveedorUpdate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_admin_user)  # Solo administradores
):
    """
    Actualiza los datos de un proveedor existente.
    """
    # Verificar si el proveedor existe
    db_proveedor = db.query(Proveedores).filter(Proveedores.id_proveedor == proveedor_id).first()
    if db_proveedor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proveedor con ID {proveedor_id} no encontrado"
        )
    
    # Verificar si el email ya existe (si se está actualizando)
    if proveedor_update.email and proveedor_update.email != db_proveedor.email:
        exists = db.query(Proveedores).filter(Proveedores.email == proveedor_update.email).first()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El email {proveedor_update.email} ya está registrado"
            )
    
    # Actualizar proveedor
    update_data = proveedor_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_proveedor, key, value)
    
    db.commit()
    db.refresh(db_proveedor)
    
    return db_proveedor

# Eliminar un proveedor (soft delete)
@router.delete("/{proveedor_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar proveedor")
async def delete_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_admin_user)  # Solo administradores
):
    """
    Elimina un proveedor del sistema (soft delete).
    """
    # Verificar si el proveedor existe
    db_proveedor = db.query(Proveedores).filter(Proveedores.id_proveedor == proveedor_id).first()
    if db_proveedor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proveedor con ID {proveedor_id} no encontrado"
        )
    
    # Soft delete (cambiar status a inactivo - asumiendo que 2 es "inactivo")
    db_proveedor.id_status = 2
    db.commit()
    
    return None