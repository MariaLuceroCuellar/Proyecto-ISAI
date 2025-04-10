from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.productos import Productos, Categorias, Comics, FigurasColeccion
from ..schemas.productos import (
    Producto, ProductoCreate, ProductoUpdate, ProductoDetalle,
    Categoria, CategoriaCreate, ComicCreate, ComicDetalle,
    FiguraColeccion, FiguraColeccionCreate, FiguraColeccionDetalle,
    ProductoCompletoCreate
)
from ..dependencies import get_current_active_user, get_admin_user
from ..models.empleados import Empleados
import os
import uuid
from datetime import datetime

router = APIRouter()

# Obtener todos los productos
@router.get("/", response_model=List[Producto], summary="Obtener lista de productos")
async def get_productos(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(100, description="Número máximo de registros a devolver"),
    search: Optional[str] = Query(None, description="Buscar por nombre o SKU"),
    categoria: Optional[int] = Query(None, description="Filtrar por categoría"),
    proveedor: Optional[int] = Query(None, description="Filtrar por proveedor"),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene la lista de productos con paginación y filtros opcionales.
    """
    query = db.query(Productos)
    
    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Productos.nombre.like(search_term)) | 
            (Productos.sku.like(search_term))
        )
    
    if categoria:
        query = query.filter(Productos.id_categoria == categoria)
    
    if proveedor:
        query = query.filter(Productos.id_proveedor == proveedor)
    
    return query.order_by(Productos.nombre).offset(skip).limit(limit).all()

# Obtener un producto por ID
@router.get("/{producto_id}", response_model=ProductoDetalle, summary="Obtener producto por ID")
async def get_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene los detalles de un producto específico por su ID.
    """
    producto = db.query(Productos).filter(Productos.id_producto == producto_id).first()
    if producto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    return producto

# Crear un nuevo producto
@router.post("/", response_model=Producto, status_code=status.HTTP_201_CREATED, summary="Crear nuevo producto")
async def create_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Crea un nuevo producto en el sistema.
    """
    # Verificar si el SKU ya existe
    db_producto = db.query(Productos).filter(Productos.sku == producto.sku).first()
    if db_producto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El SKU {producto.sku} ya está registrado"
        )
    
    # Verificar si la categoría existe
    categoria = db.query(Categorias).filter(Categorias.id_categoria == producto.id_categoria).first()
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categoría con ID {producto.id_categoria} no existe"
        )
    
    # Crear nuevo producto
    db_producto = Productos(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    
    return db_producto

# Actualizar un producto
@router.put("/{producto_id}", response_model=Producto, summary="Actualizar producto")
async def update_producto(
    producto_id: int,
    producto_update: ProductoUpdate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Actualiza los datos de un producto existente.
    """
    # Verificar si el producto existe
    db_producto = db.query(Productos).filter(Productos.id_producto == producto_id).first()
    if db_producto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    
    # Verificar si el SKU ya existe (si se está actualizando)
    if producto_update.sku and producto_update.sku != db_producto.sku:
        exists = db.query(Productos).filter(Productos.sku == producto_update.sku).first()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El SKU {producto_update.sku} ya está registrado"
            )
    
    # Verificar si la categoría existe (si se está actualizando)
    if producto_update.id_categoria:
        categoria = db.query(Categorias).filter(Categorias.id_categoria == producto_update.id_categoria).first()
        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Categoría con ID {producto_update.id_categoria} no existe"
            )
    
    # Actualizar producto
    update_data = producto_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_producto, key, value)
    
    db.commit()
    db.refresh(db_producto)
    
    return db_producto

# Eliminar un producto (soft delete)
@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar producto")
async def delete_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_admin_user)  # Solo administradores
):
    """
    Elimina un producto del sistema (soft delete).
    """
    # Verificar si el producto existe
    db_producto = db.query(Productos).filter(Productos.id_producto == producto_id).first()
    if db_producto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    
    # Soft delete (cambiar status a inactivo - asumiendo que 2 es "inactivo")
    db_producto.id_status = 2
    db.commit()
    
    return None

# Crear producto completo (producto + comic o figura)
@router.post("/completo", response_model=ProductoDetalle, status_code=status.HTTP_201_CREATED, summary="Crear producto completo")
async def create_producto_completo(
    producto_completo: ProductoCompletoCreate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Crea un producto completo con sus detalles específicos (comic o figura).
    """
    # Verificar si el SKU ya existe
    db_producto = db.query(Productos).filter(Productos.sku == producto_completo.producto.sku).first()
    if db_producto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El SKU {producto_completo.producto.sku} ya está registrado"
        )
    
    # Crear nuevo producto
    db_producto = Productos(**producto_completo.producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    
    # Crear comic o figura según corresponda
    if producto_completo.comic:
        db_comic = Comics(
            id_producto=db_producto.id_producto,
            **producto_completo.comic.model_dump()
        )
        db.add(db_comic)
    elif producto_completo.figura:
        db_figura = FigurasColeccion(
            id_producto=db_producto.id_producto,
            **producto_completo.figura.model_dump()
        )
        db.add(db_figura)
    
    db.commit()
    db.refresh(db_producto)
    
    return db_producto

# Obtener todos los comics
@router.get("/comics", response_model=List[ComicDetalle], summary="Obtener lista de comics")
async def get_comics(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(100, description="Número máximo de registros a devolver"),
    search: Optional[str] = Query(None, description="Buscar por título")
):
    """
    Obtiene la lista de comics.
    """
    query = db.query(Comics).join(Productos)
    
    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(Comics.titulo.like(search_term))
    
    return query.offset(skip).limit(limit).all()

# Obtener un comic por ID
@router.get("/comics/{comic_id}", response_model=ComicDetalle, summary="Obtener comic por ID")
async def get_comic(
    comic_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de un comic específico por su ID.
    """
    comic = db.query(Comics).filter(Comics.id_comic == comic_id).first()
    if comic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comic con ID {comic_id} no encontrado"
        )
    return comic

# Obtener todas las figuras
@router.get("/figuras", response_model=List[FiguraColeccionDetalle], summary="Obtener lista de figuras")
async def get_figuras(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(100, description="Número máximo de registros a devolver"),
    search: Optional[str] = Query(None, description="Buscar por personaje o universo")
):
    """
    Obtiene la lista de figuras de colección.
    """
    query = db.query(FigurasColeccion).join(Productos)
    
    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (FigurasColeccion.personaje.like(search_term)) | 
            (FigurasColeccion.universo.like(search_term))
        )
    
    return query.offset(skip).limit(limit).all()

# Obtener una figura por ID
@router.get("/figuras/{figura_id}", response_model=FiguraColeccionDetalle, summary="Obtener figura por ID")
async def get_figura(
    figura_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de una figura específica por su ID.
    """
    figura = db.query(FigurasColeccion).filter(FigurasColeccion.id_figura == figura_id).first()
    if figura is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Figura con ID {figura_id} no encontrada"
        )
    return figura

# Obtener todas las categorías
@router.get("/categorias", response_model=List[Categoria], summary="Obtener lista de categorías")
async def get_categorias(
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de todas las categorías de productos.
    """
    return db.query(Categorias).all()

# Crear nueva categoría
@router.post("/categorias", response_model=Categoria, status_code=status.HTTP_201_CREATED, summary="Crear nueva categoría")
async def create_categoria(
    categoria: CategoriaCreate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Crea una nueva categoría de productos.
    """
    # Verificar si la categoría ya existe
    db_categoria = db.query(Categorias).filter(Categorias.nombre_categoria == categoria.nombre_categoria).first()
    if db_categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La categoría {categoria.nombre_categoria} ya existe"
        )
    
    # Crear nueva categoría
    db_categoria = Categorias(**categoria.model_dump())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    
    return db_categoria

# Actualizar una categoría
@router.put("/categorias/{categoria_id}", response_model=Categoria, summary="Actualizar categoría")
async def update_categoria(
    categoria_id: int,
    categoria: CategoriaCreate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Actualiza una categoría existente.
    """
    # Verificar si la categoría existe
    db_categoria = db.query(Categorias).filter(Categorias.id_categoria == categoria_id).first()
    if db_categoria is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoría con ID {categoria_id} no encontrada"
        )
    
    # Verificar si el nombre ya existe (si se está actualizando)
    if categoria.nombre_categoria != db_categoria.nombre_categoria:
        exists = db.query(Categorias).filter(Categorias.nombre_categoria == categoria.nombre_categoria).first()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La categoría {categoria.nombre_categoria} ya existe"
            )
    
    # Actualizar categoría
    db_categoria.nombre_categoria = categoria.nombre_categoria
    db_categoria.descripcion = categoria.descripcion
    
    db.commit()
    db.refresh(db_categoria)
    
    return db_categoria