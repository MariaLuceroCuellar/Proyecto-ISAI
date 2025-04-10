from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional

from .database import get_db
from .config import settings
from .models.empleados import Empleados
from .schemas.auth import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Empleados:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user = db.query(Empleados).filter(Empleados.nombre_usuario == token_data.username).first()
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_active_user(
    current_user: Empleados = Depends(get_current_user),
) -> Empleados:
    if current_user.id_status != 1:  # Asumiendo que 1 es el estatus activo
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

async def get_admin_user(
    current_user: Empleados = Depends(get_current_active_user),
) -> Empleados:
    if current_user.id_rol != 1:  # Asumiendo que 1 es el rol de administrador
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes",
        )
    return current_user