from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.pedidos import Pedidos, DetallesPedido, EstadosPedido
from ..models.productos import Productos
from ..models.clientes import Clientes, NivelesMembresia
from ..models.inventario import Inventario, TiposMovimiento
from ..schemas.pedidos import (
    Pedido, PedidoCreate, PedidoUpdate, PedidoDetalle, 
    DetallePedido, EstadoPedido
)
from ..dependencies import get_current_active_user, get_admin_user
from ..models.empleados import Empleados
from datetime import datetime
import random
import string
from decimal import Decimal

router = APIRouter()

# Generar número de pedido único
def generar_numero_pedido(db: Session):
    while True:
        # Formato: PED-YYYYMMDD-XXXXX (donde X es un carácter alfanumérico)
        fecha = datetime.now().strftime("%Y%m%d")
        sufijo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        numero_pedido = f"PED-{fecha}-{sufijo}"
        
        # Verificar que no exista
        existe = db.query(Pedidos).filter(Pedidos.numero_pedido == numero_pedido).first()
        if not existe:
            return numero_pedido

# Obtener todos los pedidos
@router.get("/", response_model=List[Pedido], summary="Obtener lista de pedidos")
async def get_pedidos(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(100, description="Número máximo de registros a devolver"),
    id_cliente: Optional[int] = Query(None, description="Filtrar por cliente"),
    id_estado: Optional[int] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[str] = Query(None, description="Filtrar desde fecha (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Filtrar hasta fecha (YYYY-MM-DD)"),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene la lista de pedidos con paginación y filtros opcionales.
    """
    query = db.query(Pedidos)
    
    # Aplicar filtros
    if id_cliente:
        query = query.filter(Pedidos.id_cliente == id_cliente)
    
    if id_estado:
        query = query.filter(Pedidos.id_estado == id_estado)
    
    if fecha_desde:
        fecha_desde_obj = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
        query = query.filter(Pedidos.fecha_creacion >= fecha_desde_obj)
    
    if fecha_hasta:
        fecha_hasta_obj = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
        query = query.filter(Pedidos.fecha_creacion <= fecha_hasta_obj)
    
    return query.order_by(Pedidos.fecha_creacion.desc()).offset(skip).limit(limit).all()

# Obtener un pedido por ID
@router.get("/{pedido_id}", response_model=PedidoDetalle, summary="Obtener pedido por ID")
async def get_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene los detalles de un pedido específico por su ID.
    """
    pedido = db.query(Pedidos).filter(Pedidos.id_pedido == pedido_id).first()
    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {pedido_id} no encontrado"
        )
    return pedido

# Crear un nuevo pedido
@router.post("/", response_model=PedidoDetalle, status_code=status.HTTP_201_CREATED, summary="Crear nuevo pedido")
async def create_pedido(
    pedido: PedidoCreate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Crea un nuevo pedido con sus detalles.
    """
    # Verificar si el cliente existe
    cliente = db.query(Clientes).filter(Clientes.id_cliente == pedido.id_cliente).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {pedido.id_cliente} no encontrado"
        )
    
    # Obtener nivel de membresía del cliente para aplicar descuento
    nivel_membresia = db.query(NivelesMembresia).filter(NivelesMembresia.id_nivel == cliente.id_nivel).first()
    descuento_porcentaje = nivel_membresia.descuento_porcentaje if nivel_membresia else 0
    
    # Verificar productos y calcular totales
    subtotal = 0
    impuestos = 0
    detalles_procesados = []
    
    # Verificar que existan todos los productos y haya stock suficiente
    for detalle in pedido.detalles:
        producto = db.query(Productos).filter(
            Productos.id_producto == detalle.id_producto,
            Productos.id_status == 1  # Solo productos activos
        ).first()
        
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {detalle.id_producto} no encontrado o no está activo"
            )
        
        if producto.stock_actual < detalle.cantidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para el producto {producto.nombre}. Disponible: {producto.stock_actual}, Solicitado: {detalle.cantidad}"
            )
        
        # Calcular subtotal de cada detalle
        precio_unitario = producto.precio_venta
        descuento_unitario = (precio_unitario * descuento_porcentaje) / 100
        subtotal_detalle = (precio_unitario - descuento_unitario) * detalle.cantidad
        
        detalles_procesados.append({
            "id_producto": detalle.id_producto,
            "cantidad": detalle.cantidad,
            "precio_unitario": precio_unitario,
            "descuento_unitario": descuento_unitario,
            "subtotal": subtotal_detalle,
            "producto": producto  # Para actualizar el stock después
        })
        
        subtotal += subtotal_detalle
    
    # Calcular impuestos (16% por defecto)
    impuestos = subtotal * Decimal("0.16")
    
    # Calcular descuento total
    descuento_total = (subtotal * descuento_porcentaje) / 100
    
    # Calcular total
    total = subtotal + impuestos
    
    # Generar número de pedido
    numero_pedido = generar_numero_pedido(db)
    
    # Estado inicial de pedido (1: Pendiente)
    id_estado_inicial = 1
    
    # Crear pedido
    db_pedido = Pedidos(
        numero_pedido=numero_pedido,
        fecha_creacion=datetime.now(),
        id_cliente=pedido.id_cliente,
        id_empleado=current_user.id_empleado,
        subtotal=subtotal,
        impuestos=impuestos,
        descuento=descuento_total,
        total=total,
        id_estado=id_estado_inicial,
        notas=pedido.notas
    )
    
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    
    # Crear detalles del pedido
    for detalle in detalles_procesados:
        db_detalle = DetallesPedido(
            id_pedido=db_pedido.id_pedido,
            id_producto=detalle["id_producto"],
            cantidad=detalle["cantidad"],
            precio_unitario=detalle["precio_unitario"],
            descuento_unitario=detalle["descuento_unitario"],
            subtotal=detalle["subtotal"]
        )
        db.add(db_detalle)
        
        # Actualizar inventario (disminuir stock)
        producto = detalle["producto"]
        stock_anterior = producto.stock_actual
        stock_nuevo = stock_anterior - detalle["cantidad"]
        
        # Buscar tipo de movimiento "salida"
        tipo_salida = db.query(TiposMovimiento).filter(TiposMovimiento.nombre_tipo == "salida").first()
        
        # Registrar movimiento en inventario
        if tipo_salida:
            db_movimiento = Inventario(
                id_producto=detalle["id_producto"],
                id_tipo_movimiento=tipo_salida.id_tipo_movimiento,
                cantidad=detalle["cantidad"],
                stock_anterior=stock_anterior,
                stock_nuevo=stock_nuevo,
                id_empleado=current_user.id_empleado,
                motivo=f"Salida por pedido #{db_pedido.numero_pedido}",
                id_documento=db_pedido.id_pedido,
                tipo_documento="pedido"
            )
            db.add(db_movimiento)
        
        # Actualizar stock del producto
        producto.stock_actual = stock_nuevo
    
    # Actualizar fecha última compra del cliente
    cliente.fecha_ultima_compra = datetime.now()
    
    # Sumar puntos según nivel de membresía
    if nivel_membresia:
        puntos_a_sumar = nivel_membresia.puntos_por_compra
        cliente.puntos_acumulados += puntos_a_sumar
    
    db.commit()
    db.refresh(db_pedido)
    
    return db_pedido

# Actualizar estado de un pedido
@router.put("/{pedido_id}/estado", response_model=Pedido, summary="Actualizar estado de pedido")
async def update_estado_pedido(
    pedido_id: int,
    pedido_update: PedidoUpdate,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Actualiza el estado de un pedido existente.
    """
    # Verificar si el pedido existe
    db_pedido = db.query(Pedidos).filter(Pedidos.id_pedido == pedido_id).first()
    if db_pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {pedido_id} no encontrado"
        )
    
    # Verificar si el estado existe
    if pedido_update.id_estado:
        estado = db.query(EstadosPedido).filter(EstadosPedido.id_estado == pedido_update.id_estado).first()
        if not estado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estado con ID {pedido_update.id_estado} no encontrado"
            )
        
        # Actualizar estado
        db_pedido.id_estado = pedido_update.id_estado
    
    # Actualizar notas si se proporcionan
    if pedido_update.notas is not None:
        db_pedido.notas = pedido_update.notas
    
    db.commit()
    db.refresh(db_pedido)
    
    return db_pedido

# Cancelar un pedido
@router.post("/{pedido_id}/cancelar", response_model=Pedido, summary="Cancelar pedido")
async def cancelar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Cancela un pedido y devuelve los productos al inventario.
    """
    # Verificar si el pedido existe
    db_pedido = db.query(Pedidos).filter(Pedidos.id_pedido == pedido_id).first()
    if db_pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {pedido_id} no encontrado"
        )
    
    # Verificar que el pedido no esté ya entregado o cancelado
    if db_pedido.id_estado in [3, 4]:  # Asumiendo que 3 es entregado y 4 es cancelado
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede cancelar un pedido que ya está entregado o cancelado"
        )
    
    # Actualizar estado a cancelado (4)
    db_pedido.id_estado = 4
    
    # Obtener detalles del pedido
    detalles = db.query(DetallesPedido).filter(DetallesPedido.id_pedido == pedido_id).all()
    
    # Buscar tipo de movimiento "entrada"
    tipo_entrada = db.query(TiposMovimiento).filter(TiposMovimiento.nombre_tipo == "entrada").first()
    
    # Devolver productos al inventario
    for detalle in detalles:
        producto = db.query(Productos).filter(Productos.id_producto == detalle.id_producto).first()
        if producto:
            stock_anterior = producto.stock_actual
            stock_nuevo = stock_anterior + detalle.cantidad
            
            # Registrar movimiento en inventario
            if tipo_entrada:
                db_movimiento = Inventario(
                    id_producto=detalle.id_producto,
                    id_tipo_movimiento=tipo_entrada.id_tipo_movimiento,
                    cantidad=detalle.cantidad,
                    stock_anterior=stock_anterior,
                    stock_nuevo=stock_nuevo,
                    id_empleado=current_user.id_empleado,
                    motivo=f"Devolución por cancelación de pedido #{db_pedido.numero_pedido}",
                    id_documento=db_pedido.id_pedido,
                    tipo_documento="pedido"
                )
                db.add(db_movimiento)
            
            # Actualizar stock del producto
            producto.stock_actual = stock_nuevo
    
    db.commit()
    db.refresh(db_pedido)
    
    return db_pedido

# Obtener todos los estados de pedido
@router.get("/estados", response_model=List[EstadoPedido], summary="Obtener estados de pedido")
async def get_estados_pedido(
    db: Session = Depends(get_db),
    current_user: Empleados = Depends(get_current_active_user)
):
    """
    Obtiene la lista de todos los estados de pedido.
    """
    return db.query(EstadosPedido).all()