from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import jwt
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..config import settings
from ..models.empleados import Empleados
from ..schemas.auth import Token, UserLogin, PasswordChange
from ..dependencies import get_current_active_user
from ..core.auth import verify_password, get_password_hash

router = APIRouter()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/login", response_model=Token, summary="Iniciar sesión")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Autenticación de usuario y generación de token JWT.
    
    - **username**: Nombre de usuario
    - **password**: Contraseña
    """
    user = db.query(Empleados).filter(Empleados.nombre_usuario == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.id_status != 1:  # Asumiendo que 1 es el estatus activo
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Actualizar último acceso
    user.ultimo_acceso = datetime.utcnow()
    db.commit()
    
    # Crear token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.nombre_usuario}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", summary="Obtener información del usuario actual")
async def read_users_me(current_user: Empleados = Depends(get_current_active_user)):
    """
    Obtiene información del usuario autenticado actual.
    """
    user_data = {
        "id_empleado": current_user.id_empleado,
        "nombre": current_user.nombre,
        "apellidos": current_user.apellidos,
        "email": current_user.email,
        "nombre_usuario": current_user.nombre_usuario,
        "id_rol": current_user.id_rol,
        "id_puesto": current_user.id_puesto
    }
    return user_data

@router.post("/change-password", summary="Cambiar contraseña")
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Cambia la contraseña del usuario autenticado actual.
    
    - **old_password**: Contraseña actual
    - **new_password**: Nueva contraseña
    """
    # Verificar contraseña actual
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    # Actualizar contraseña
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Contraseña actualizada exitosamente"}