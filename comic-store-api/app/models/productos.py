from sqlalchemy import Column, Integer, String, Text, ForeignKey, DECIMAL, Date, Boolean
from sqlalchemy.orm import relationship
from ..database import Base

class Categorias(Base):
    __tablename__ = "Categorias"
    
    id_categoria = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_categoria = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)
    
    # Relaciones
    productos = relationship("Productos", back_populates="categoria")

class Productos(Base):
    __tablename__ = "Productos"
    
    id_producto = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sku = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    id_categoria = Column(Integer, ForeignKey("Categorias.id_categoria"), nullable=False)
    stock_actual = Column(Integer, default=0)
    stock_minimo = Column(Integer, default=5)
    precio_compra = Column(DECIMAL(10, 2), nullable=False)
    precio_venta = Column(DECIMAL(10, 2), nullable=False)
    fecha_lanzamiento = Column(Date)
    imagen_url = Column(String(255))
    id_proveedor = Column(Integer, ForeignKey("Proveedores.id_proveedor", ondelete="SET NULL"))
    id_status = Column(Integer, ForeignKey("Status.id_status"), default=1)
    
    # Relaciones
    categoria = relationship("Categorias", back_populates="productos")
    proveedor = relationship("Proveedores", back_populates="productos")
    status = relationship("Status")
    comic = relationship("Comics", back_populates="producto", uselist=False)
    figura = relationship("FigurasColeccion", back_populates="producto", uselist=False)
    inventario = relationship("Inventario", back_populates="producto")
    detalles_pedido = relationship("DetallesPedido", back_populates="producto")
    detalles_compra = relationship("DetallesCompra", back_populates="producto")

class Comics(Base):
    __tablename__ = "Comics"
    
    id_comic = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_producto = Column(Integer, ForeignKey("Productos.id_producto", ondelete="CASCADE"), nullable=False, unique=True)
    titulo = Column(String(255), nullable=False)
    numero = Column(Integer)
    isbn = Column(String(20))
    fecha_publicacion = Column(Date)
    guionista = Column(String(100))
    sinopsis = Column(Text)
    
    # Relaciones
    producto = relationship("Productos", back_populates="comic")

class FigurasColeccion(Base):
    __tablename__ = "FigurasColeccion"
    
    id_figura = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_producto = Column(Integer, ForeignKey("Productos.id_producto", ondelete="CASCADE"), nullable=False, unique=True)
    personaje = Column(String(100))
    universo = Column(String(100))
    material = Column(String(100))
    edicion_limitada = Column(Boolean, default=False)
    numero_serie = Column(String(50))
    
    # Relaciones
    producto = relationship("Productos", back_populates="figura")