from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.empleados import Empleados, Puestos
from ..models.base import Roles
from ..schemas.empleados import (
    Empleado, EmpleadoCreate, EmpleadoUpdate, EmpleadoDetalle,
    Puesto, PuestoCreate, Rol, RolCreate, EmpleadoAdminCreate
)
from ..dependencies import get_current_active_user, get_admin_user
from ..core.auth import get_password_hash

router = APIRouter()

# Obtener todos los empleados
@router.get("/", response_model=List[Empleado], summary="Obtener lista de empleados")
async def get_empleados(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(100, description="Número máximo de registros a devolver"),
    search: Optional[str] = Query(None, description="Buscar por nombre, apellidos o email"),
    puesto: Optional[int] = Query(None, description="Filtrar por puesto"),
    current_user: Empleados = Depends(get_admin_user)  # Solo administradores
):
    """
    Obtiene la lista de empleados con paginación y filtros opcionales.
    
    Requiere permisos de administrador.
    """
    query = db.query(Empleados)
    
    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Empleados.nombre.like(search_term)) | 
            (Empleados.apellidos.like(search_term)) | 
            (Empleados.email.like(search_term))
        )
    
    if puesto:
        query = query.filter(Empleados.id_puesto == puesto)
    
    return query.offset(skip).limit(limit).all()

# Obtener un empleado por ID
@router.get("/{empleado_id}", response_model=EmpleadoDetalle, summary="Obtener empleado por ID")
async def get_empleado(
    empleado_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene los detalles de un empleado específico por su ID.
    
    Los empleados pueden ver su propia información, pero solo los administradores
    pueden ver la información de otros empleados.
    """
    # Verificar permisos
    if current_user.id_empleado != empleado_id and current_user.id_rol != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver la información de este empleado"
        )
    
    empleado = db.query(Empleados).filter(Empleados.id_empleado == empleado_id).first()
    if empleado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con ID {empleado_id} no encontrado"
        )
    return empleado

# Crear un nuevo empleado (solo administradores)
@router.post("/", response_model=Empleado, status_code=status.HTTP_201_CREATED, summary="Crear nuevo empleado")
async def create_empleado(
    empleado: EmpleadoCreate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_admin_user)
):
    """
    Crea un nuevo empleado en el sistema.
    
    Requiere permisos de administrador.
    """
    # Verificar si el email ya existe
    db_empleado = db.query(Empleados).filter(Empleados.email == empleado.email).first()
    if db_empleado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El email {empleado.email} ya está registrado"
        )
    
    # Verificar si el nombre de usuario ya existe
    db_username = db.query(Empleados).filter(Empleados.nombre_usuario == empleado.nombre_usuario).first()
    if db_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El nombre de usuario {empleado.nombre_usuario} ya está registrado"
        )
    
    # Verificar si el puesto existe
    puesto = db.query(Puestos).filter(Puestos.id_puesto == empleado.id_puesto).first()
    if not puesto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Puesto con ID {empleado.id_puesto} no existe"
        )
    
    # Verificar si el rol existe (si se proporciona)
    if empleado.id_rol:
        rol = db.query(Roles).filter(Roles.id_rol == empleado.id_rol).first()
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol con ID {empleado.id_rol} no existe"
            )
    
    # Crear nuevo empleado
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

# Actualizar un empleado
@router.put("/{empleado_id}", response_model=Empleado, summary="Actualizar empleado")
async def update_empleado(
    empleado_id: int,
    empleado_update: EmpleadoUpdate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Actualiza los datos de un empleado existente.
    
    Los empleados pueden actualizar su propia información (excepto rol y estado),
    pero solo los administradores pueden actualizar la información de otros empleados.
    """
    # Verificar permisos
    is_admin = current_user.id_rol == 1
    is_self = current_user.id_empleado == empleado_id
    
    if not is_admin and not is_self:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar la información de este empleado"
        )
    
    # Restringir campos para no administradores
    if not is_admin and is_self:
        if empleado_update.id_rol is not None or empleado_update.id_status is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para actualizar el rol o estado"
            )
    
    # Verificar si el empleado existe
    db_empleado = db.query(Empleados).filter(Empleados.id_empleado == empleado_id).first()
    if db_empleado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con ID {empleado_id} no encontrado"
        )
    
    # Verificar si el email ya existe (si se está actualizando)
    if empleado_update.email and empleado_update.email != db_empleado.email:
        exists = db.query(Empleados).filter(Empleados.email == empleado_update.email).first()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El email {empleado_update.email} ya está registrado"
            )
    
    # Verificar si el puesto existe (si se está actualizando)
    if empleado_update.id_puesto:
        puesto = db.query(Puestos).filter(Puestos.id_puesto == empleado_update.id_puesto).first()
        if not puesto:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Puesto con ID {empleado_update.id_puesto} no existe"
            )
    
    # Verificar si el rol existe (si se está actualizando)
    if empleado_update.id_rol:
        rol = db.query(Roles).filter(Roles.id_rol == empleado_update.id_rol).first()
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol con ID {empleado_update.id_rol} no existe"
            )
    
    # Actualizar empleado
    update_data = empleado_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_empleado, key, value)
    
    db.commit()
    db.refresh(db_empleado)
    
    return db_empleado

# Eliminar un empleado (soft delete - solo administradores)
@router.delete("/{empleado_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar empleado")
async def delete_empleado(
    empleado_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_admin_user)
):
    """
    Elimina un empleado del sistema (soft delete).
    
    Requiere permisos de administrador.
    """
    # Verificar si el empleado existe
    db_empleado = db.query(Empleados).filter(Empleados.id_empleado == empleado_id).first()
    if db_empleado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con ID {empleado_id} no encontrado"
        )
    
    # No permitir eliminar al administrador principal (asumiendo que tiene ID 1)
    if db_empleado.id_rol == 1 and db_empleado.id_empleado == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar al administrador principal"
        )
    
    # Soft delete (cambiar status a inactivo - asumiendo que 2 es "inactivo")
    db_empleado.id_status = 2
    db.commit()
    
    return None

# Crear un administrador (solo super admin)
@router.post("/admin", response_model=Empleado, status_code=status.HTTP_201_CREATED, summary="Crear administrador")
async def create_admin(
    empleado: EmpleadoAdminCreate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_admin_user)
):
    """
    Crea un nuevo empleado con permisos de administrador.
    
    Requiere permisos de administrador.
    """
    # Verificar si el rol es de administrador (asumiendo que 1 es el rol de administrador)
    if empleado.id_rol != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID de rol proporcionado no corresponde a un administrador"
        )
    
    # Utilizar la función de crear empleado regular
    return await create_empleado(empleado, db, current_user)

# Obtener todos los puestos
@router.get("/puestos", response_model=List[Puesto], summary="Obtener lista de puestos")
async def get_puestos(
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene la lista de todos los puestos.
    """
    return db.query(Puestos).all()

# Crear un nuevo puesto (solo administradores)
@router.post("/puestos", response_model=Puesto, status_code=status.HTTP_201_CREATED, summary="Crear nuevo puesto")
async def create_puesto(
    puesto: PuestoCreate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_admin_user)
):
    """
    Crea un nuevo puesto en el sistema.
    
    Requiere permisos de administrador.
    """
    # Verificar si el nombre ya existe
    db_puesto = db.query(Puestos).filter(Puestos.nombre_puesto == puesto.nombre_puesto).first()
    if db_puesto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El puesto {puesto.nombre_puesto} ya existe"
        )
    
    # Crear nuevo puesto
    db_puesto = Puestos(**puesto.model_dump())
    db.add(db_puesto)
    db.commit()
    db.refresh(db_puesto)
    
    return db_puesto

# Obtener todos los roles (solo administradores)
@router.get("/roles", response_model=List[Rol], summary="Obtener lista de roles")
async def get_roles(
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_admin_user)
):
    """
    Obtiene la lista de todos los roles.
    
    Requiere permisos de administrador.
    """
    return db.query(Roles).all()

# Crear un nuevo rol (solo administradores)
@router.post("/roles", response_model=Rol, status_code=status.HTTP_201_CREATED, summary="Crear nuevo rol")
async def create_rol(
    rol: RolCreate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_admin_user)
):
    """
    Crea un nuevo rol en el sistema.
    
    Requiere permisos de administrador.
    """
    # Verificar si el nombre ya existe
    db_rol = db.query(Roles).filter(Roles.nombre_rol == rol.nombre_rol).first()
    if db_rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El rol {rol.nombre_rol} ya existe"
        )
    
    # Crear nuevo rol
    db_rol = Roles(**rol.model_dump())
    db.add(db_rol)
    db.commit()
    db.refresh(db_rol)
    
    return db_rol