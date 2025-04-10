from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.compras import ComprasProveedores, DetallesCompra
from ..models.productos import Productos
from ..models.proveedores import Proveedores
from ..models.inventario import Inventario, TiposMovimiento
from ..schemas.compras import (
    Compra, CompraCreate, CompraUpdate, CompraDetalle, 
    DetalleCompra, RecepcionCompra
)
from ..dependencies import get_current_active_user, get_admin_user
from ..models.empleados import Empleados
from datetime import datetime, date
import random
import string

router = APIRouter()

# Generar número de compra único
def generar_numero_compra(db: Session):
    while True:
        # Formato: COMP-YYYYMMDD-XXXXX (donde X es un carácter alfanumérico)
        fecha = datetime.now().strftime("%Y%m%d")
        sufijo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        numero_compra = f"COMP-{fecha}-{sufijo}"
        
        # Verificar que no exista
        existe = db.query(ComprasProveedores).filter(ComprasProveedores.numero_compra == numero_compra).first()
        if not existe:
            return numero_compra

# Obtener todas las compras
@router.get("/", response_model=List[Compra], summary="Obtener lista de compras")
async def get_compras(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(100, description="Número máximo de registros a devolver"),
    id_proveedor: Optional[int] = Query(None, description="Filtrar por proveedor"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[str] = Query(None, description="Filtrar desde fecha (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Filtrar hasta fecha (YYYY-MM-DD)"),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene la lista de compras a proveedores con paginación y filtros opcionales.
    """
    query = db.query(ComprasProveedores)
    
    # Aplicar filtros
    if id_proveedor:
        query = query.filter(ComprasProveedores.id_proveedor == id_proveedor)
    
    if estado:
        query = query.filter(ComprasProveedores.estado == estado)
    
    if fecha_desde:
        fecha_desde_obj = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
        query = query.filter(ComprasProveedores.fecha_orden >= fecha_desde_obj)
    
    if fecha_hasta:
        fecha_hasta_obj = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
        query = query.filter(ComprasProveedores.fecha_orden <= fecha_hasta_obj)
    
    return query.order_by(ComprasProveedores.fecha_orden.desc()).offset(skip).limit(limit).all()

# Obtener una compra por ID
@router.get("/{compra_id}", response_model=CompraDetalle, summary="Obtener compra por ID")
async def get_compra(
    compra_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene los detalles de una compra específica por su ID.
    """
    compra = db.query(ComprasProveedores).filter(ComprasProveedores.id_compra == compra_id).first()
    if compra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compra con ID {compra_id} no encontrada"
        )
    return compra

# Crear una nueva compra
@router.post("/", response_model=CompraDetalle, status_code=status.HTTP_201_CREATED, summary="Crear nueva compra")
async def create_compra(
    compra: CompraCreate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Crea una nueva compra a proveedor con sus detalles.
    """
    # Verificar si el proveedor existe
    proveedor = db.query(Proveedores).filter(Proveedores.id_proveedor == compra.id_proveedor).first()
    if not proveedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proveedor con ID {compra.id_proveedor} no encontrado"
        )
    
    # Verificar productos y calcular totales
    subtotal = 0
    detalles_procesados = []
    
    # Verificar que existan todos los productos
    for detalle in compra.detalles:
        producto = db.query(Productos).filter(
            Productos.id_producto == detalle.id_producto,
            Productos.id_status == 1  # Solo productos activos
        ).first()
        
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {detalle.id_producto} no encontrado o no está activo"
            )
        
        # Calcular subtotal de cada detalle
        subtotal_detalle = detalle.precio_unitario * detalle.cantidad_ordenada
        
        detalles_procesados.append({
            "id_producto": detalle.id_producto,
            "cantidad_ordenada": detalle.cantidad_ordenada,
            "precio_unitario": detalle.precio_unitario,
            "subtotal": subtotal_detalle
        })
        
        subtotal += subtotal_detalle
    
    # Calcular impuestos (16% por defecto)
    impuestos = subtotal * 0.16
    
    # Calcular total
    total = subtotal + impuestos
    
    # Generar número de compra
    numero_compra = generar_numero_compra(db)
    
    # Crear compra
    db_compra = ComprasProveedores(
        numero_compra=numero_compra,
        id_proveedor=compra.id_proveedor,
        fecha_orden=datetime.now(),
        fecha_estimada_llegada=compra.fecha_estimada_llegada,
        subtotal=subtotal,
        impuestos=impuestos,
        total=total,
        estado="pendiente",
        id_empleado=current_user.id_empleado if compra.id_empleado is None else compra.id_empleado,
        notas=compra.notas
    )
    
    db.add(db_compra)
    db.commit()
    db.refresh(db_compra)
    
    # Crear detalles de la compra
    for detalle in detalles_procesados:
        db_detalle = DetallesCompra(
            id_compra=db_compra.id_compra,
            id_producto=detalle["id_producto"],
            cantidad_ordenada=detalle["cantidad_ordenada"],
            cantidad_recibida=0,
            precio_unitario=detalle["precio_unitario"],
            subtotal=detalle["subtotal"],
            estado="pendiente"
        )
        db.add(db_detalle)
    
    db.commit()
    db.refresh(db_compra)
    
    return db_compra

# Actualizar estado de una compra
@router.put("/{compra_id}/estado", response_model=Compra, summary="Actualizar estado de compra")
async def update_estado_compra(
    compra_id: int,
    compra_update: CompraUpdate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Actualiza el estado de una compra existente.
    """
    # Verificar si la compra existe
    db_compra = db.query(ComprasProveedores).filter(ComprasProveedores.id_compra == compra_id).first()
    if db_compra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compra con ID {compra_id} no encontrada"
        )
    
    # Actualizar estado si se proporciona
    if compra_update.estado:
        estados_validos = ["pendiente", "procesado", "entregado", "cancelado"]
        if compra_update.estado not in estados_validos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido. Estados válidos: {', '.join(estados_validos)}"
            )
        
        db_compra.estado = compra_update.estado
    
    # Actualizar fecha estimada si se proporciona
    if compra_update.fecha_estimada_llegada:
        db_compra.fecha_estimada_llegada = compra_update.fecha_estimada_llegada
    
    # Actualizar notas si se proporcionan
    if compra_update.notas is not None:
        db_compra.notas = compra_update.notas
    
    db.commit()
    db.refresh(db_compra)
    
    return db_compra

# Registrar recepción de productos
@router.post("/{compra_id}/recepcion", response_model=CompraDetalle, summary="Registrar recepción de productos")
async def registrar_recepcion(
    compra_id: int,
    recepcion: RecepcionCompra,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Registra la recepción de productos de una compra y actualiza el inventario.
    """
    # Verificar si la compra existe
    db_compra = db.query(ComprasProveedores).filter(ComprasProveedores.id_compra == compra_id).first()
    if db_compra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compra con ID {compra_id} no encontrada"
        )
    
    # Verificar que la compra no esté cancelada
    if db_compra.estado == "cancelado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede recibir productos de una compra cancelada"
        )
    
    # Actualizar fecha de recepción
    db_compra.fecha_recepcion = recepcion.fecha_recepcion
    
    # Buscar tipo de movimiento "entrada"
    tipo_entrada = db.query(TiposMovimiento).filter(TiposMovimiento.nombre_tipo == "entrada").first()
    if not tipo_entrada:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tipo de movimiento 'entrada' no encontrado en el sistema"
        )
    
    # Procesar cada detalle de recepción
    todos_completos = True
    
    for detalle_recepcion in recepcion.detalles:
        id_detalle = detalle_recepcion.get("id_detalle")
        cantidad_recibida = detalle_recepcion.get("cantidad_recibida", 0)
        
        # Obtener el detalle de la compra
        detalle = db.query(DetallesCompra).filter(
            DetallesCompra.id_detalle == id_detalle,
            DetallesCompra.id_compra == compra_id
        ).first()
        
        if not detalle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Detalle con ID {id_detalle} no encontrado en esta compra"
            )
        
        # Verificar que la cantidad recibida sea válida
        if cantidad_recibida < 0 or cantidad_recibida > detalle.cantidad_ordenada:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cantidad recibida inválida para el producto con ID {detalle.id_producto}"
            )
        
        # Calcular nueva cantidad recibida total
        nueva_cantidad_recibida = detalle.cantidad_recibida + cantidad_recibida
        
        # Si ya se ha recibido todo, no hacer nada
        if detalle.cantidad_recibida == detalle.cantidad_ordenada:
            continue
        
        # Si hay productos por recibir, procesar la recepción
        if cantidad_recibida > 0:
            # Obtener el producto
            producto = db.query(Productos).filter(Productos.id_producto == detalle.id_producto).first()
            if not producto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Producto con ID {detalle.id_producto} no encontrado"
                )
            
            # Actualizar stock
            stock_anterior = producto.stock_actual
            stock_nuevo = stock_anterior + cantidad_recibida
            
            # Registrar movimiento en inventario
            db_movimiento = Inventario(
                id_producto=detalle.id_producto,
                id_tipo_movimiento=tipo_entrada.id_tipo_movimiento,
                cantidad=cantidad_recibida,
                stock_anterior=stock_anterior,
                stock_nuevo=stock_nuevo,
                id_empleado=current_user.id_empleado,
                motivo=f"Entrada por compra #{db_compra.numero_compra}",
                id_documento=db_compra.id_compra,
                tipo_documento="compra"
            )
            db.add(db_movimiento)
            
            # Actualizar stock del producto
            producto.stock_actual = stock_nuevo
            
            # Actualizar cantidad recibida en el detalle
            detalle.cantidad_recibida = nueva_cantidad_recibida
            
            # Actualizar estado del detalle
            if nueva_cantidad_recibida == detalle.cantidad_ordenada:
                detalle.estado = "completo"
            elif nueva_cantidad_recibida > 0:
                detalle.estado = "parcial"
                todos_completos = False
            else:
                todos_completos = False
        
    # Actualizar estado de la compra
    if todos_completos:
        db_compra.estado = "entregado"
    else:
        db_compra.estado = "procesado"
    
    db.commit()
    db.refresh(db_compra)
    
    return db_compra

# Cancelar una compra
@router.post("/{compra_id}/cancelar", response_model=Compra, summary="Cancelar compra")
async def cancelar_compra(
    compra_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_admin_user)  # Solo administradores
):
    """
    Cancela una compra a proveedor.
    """
    # Verificar si la compra existe
    db_compra = db.query(ComprasProveedores).filter(ComprasProveedores.id_compra == compra_id).first()
    if db_compra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compra con ID {compra_id} no encontrada"
        )
    
    # Verificar que la compra no esté ya entregada o cancelada
    if db_compra.estado in ["entregado", "cancelado"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede cancelar una compra que ya está entregada o cancelada"
        )
    
    # Actualizar estado a cancelado
    db_compra.estado = "cancelado"
    
    # Actualizar estado de los detalles
    detalles = db.query(DetallesCompra).filter(DetallesCompra.id_compra == compra_id).all()
    for detalle in detalles:
        if detalle.estado != "completo":  # No cancelar lo que ya se ha recibido
            detalle.estado = "cancelado"
    
    db.commit()
    db.refresh(db_compra)
    
    return db_compra