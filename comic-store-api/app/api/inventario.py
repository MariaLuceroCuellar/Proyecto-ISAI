from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.inventario import Inventario, TiposMovimiento
from ..models.productos import Productos
from ..schemas.inventario import (
    MovimientoInventario, MovimientoInventarioCreate, 
    MovimientoInventarioDetalle, TipoMovimiento, AjusteInventario
)
from ..schemas.productos import ProductoDetalle 
from ..dependencies import get_current_active_user, get_admin_user
from ..models.empleados import Empleados
from datetime import datetime

router = APIRouter()

# Obtener movimientos de inventario
@router.get("/movimientos", response_model=List[MovimientoInventarioDetalle], summary="Obtener movimientos de inventario")
async def get_movimientos(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(100, description="Número máximo de registros a devolver"),
    id_producto: Optional[int] = Query(None, description="Filtrar por producto"),
    tipo_movimiento: Optional[int] = Query(None, description="Filtrar por tipo de movimiento"),
    fecha_desde: Optional[str] = Query(None, description="Filtrar desde fecha (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Filtrar hasta fecha (YYYY-MM-DD)"),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene la lista de movimientos de inventario con filtros opcionales.
    """
    query = db.query(Inventario)
    
    # Aplicar filtros
    if id_producto:
        query = query.filter(Inventario.id_producto == id_producto)
    
    if tipo_movimiento:
        query = query.filter(Inventario.id_tipo_movimiento == tipo_movimiento)
    
    if fecha_desde:
        fecha_desde_obj = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
        query = query.filter(Inventario.fecha_movimiento >= fecha_desde_obj)
    
    if fecha_hasta:
        fecha_hasta_obj = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
        query = query.filter(Inventario.fecha_movimiento <= fecha_hasta_obj)
    
    return query.order_by(Inventario.fecha_movimiento.desc()).offset(skip).limit(limit).all()

# Crear un movimiento de inventario
@router.post("/movimientos", response_model=MovimientoInventario, status_code=status.HTTP_201_CREATED, summary="Crear movimiento de inventario")
async def create_movimiento(
    movimiento: MovimientoInventarioCreate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Crea un nuevo movimiento de inventario.
    """
    # Verificar si el producto existe
    producto = db.query(Productos).filter(Productos.id_producto == movimiento.id_producto).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {movimiento.id_producto} no encontrado"
        )
    
    # Verificar si el tipo de movimiento existe
    tipo_movimiento = db.query(TiposMovimiento).filter(TiposMovimiento.id_tipo_movimiento == movimiento.id_tipo_movimiento).first()
    if not tipo_movimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de movimiento con ID {movimiento.id_tipo_movimiento} no encontrado"
        )
    
    # Calcular nuevo stock según el tipo de movimiento
    stock_anterior = producto.stock_actual
    stock_nuevo = stock_anterior
    
    if tipo_movimiento.nombre_tipo == "entrada":
        stock_nuevo = stock_anterior + movimiento.cantidad
    elif tipo_movimiento.nombre_tipo == "salida":
        if stock_anterior < movimiento.cantidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Stock actual: {stock_anterior}, Cantidad solicitada: {movimiento.cantidad}"
            )
        stock_nuevo = stock_anterior - movimiento.cantidad
    elif tipo_movimiento.nombre_tipo == "ajuste":
        stock_nuevo = movimiento.cantidad  # Para ajustes, la cantidad es el nuevo stock
    
    # Crear movimiento
    db_movimiento = Inventario(
        id_producto=movimiento.id_producto,
        id_tipo_movimiento=movimiento.id_tipo_movimiento,
        cantidad=movimiento.cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=stock_nuevo,
        id_empleado=current_user.id_empleado,
        motivo=movimiento.motivo,
        id_documento=movimiento.id_documento,
        tipo_documento=movimiento.tipo_documento
    )
    
    # Actualizar stock del producto
    producto.stock_actual = stock_nuevo
    
    db.add(db_movimiento)
    db.commit()
    db.refresh(db_movimiento)
    
    return db_movimiento

# Realizar ajuste de inventario
@router.post("/ajuste", response_model=MovimientoInventario, status_code=status.HTTP_201_CREATED, summary="Realizar ajuste de inventario")
async def ajuste_inventario(
    ajuste: AjusteInventario,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_admin_user)  # Solo administradores
):
    """
    Realiza un ajuste de inventario para un producto.
    """
    # Verificar si el producto existe
    producto = db.query(Productos).filter(Productos.id_producto == ajuste.id_producto).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {ajuste.id_producto} no encontrado"
        )
    
    # Obtener tipo de movimiento "ajuste"
    tipo_ajuste = db.query(TiposMovimiento).filter(TiposMovimiento.nombre_tipo == "ajuste").first()
    if not tipo_ajuste:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de movimiento 'ajuste' no encontrado"
        )
    
    # Crear movimiento de ajuste
    stock_anterior = producto.stock_actual
    stock_nuevo = ajuste.nueva_cantidad
    
    db_movimiento = Inventario(
        id_producto=ajuste.id_producto,
        id_tipo_movimiento=tipo_ajuste.id_tipo_movimiento,
        cantidad=ajuste.nueva_cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=stock_nuevo,
        id_empleado=current_user.id_empleado,
        motivo=ajuste.motivo,
        tipo_documento="ajuste"
    )
    
    # Actualizar stock del producto
    producto.stock_actual = stock_nuevo
    
    db.add(db_movimiento)
    db.commit()
    db.refresh(db_movimiento)
    
    return db_movimiento

# Obtener productos con stock bajo
@router.get("/alerta-stock", response_model=List[ProductoDetalle], summary="Obtener productos con stock bajo")
async def get_alerta_stock(
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene la lista de productos con stock por debajo del mínimo.
    """
    
    productos = db.query(Productos).filter(
        Productos.stock_actual < Productos.stock_minimo,
        Productos.id_status == 1  # Solo productos activos
    ).all()
    
    return productos

# Obtener tipos de movimiento
@router.get("/tipos-movimiento", response_model=List[TipoMovimiento], summary="Obtener tipos de movimiento")
async def get_tipos_movimiento(
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene la lista de tipos de movimiento de inventario.
    """
    return db.query(TiposMovimiento).all()