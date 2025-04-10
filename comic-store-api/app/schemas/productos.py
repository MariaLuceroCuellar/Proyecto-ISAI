from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class CategoriaBase(BaseModel):
    nombre_categoria: str
    descripcion: Optional[str] = None

class CategoriaCreate(CategoriaBase):
    pass

class Categoria(CategoriaBase):
    id_categoria: int
    
    class Config:
        from_attributes = True

class ProductoBase(BaseModel):
    sku: str
    nombre: str
    descripcion: Optional[str] = None
    id_categoria: int
    stock_actual: Optional[int] = 0
    stock_minimo: Optional[int] = 5
    precio_compra: float
    precio_venta: float
    fecha_lanzamiento: Optional[date] = None
    imagen_url: Optional[str] = None
    id_proveedor: Optional[int] = None

class ProductoCreate(ProductoBase):
    id_status: Optional[int] = 1

class ProductoUpdate(BaseModel):
    sku: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    id_categoria: Optional[int] = None
    stock_actual: Optional[int] = None
    stock_minimo: Optional[int] = None
    precio_compra: Optional[float] = None
    precio_venta: Optional[float] = None
    fecha_lanzamiento: Optional[date] = None
    imagen_url: Optional[str] = None
    id_proveedor: Optional[int] = None
    id_status: Optional[int] = None

class Producto(ProductoBase):
    id_producto: int
    id_status: int
    
    class Config:
        from_attributes = True

class ProductoDetalle(Producto):
    categoria: Categoria
    
    class Config:
        from_attributes = True

class ComicBase(BaseModel):
    titulo: str
    numero: Optional[int] = None
    isbn: Optional[str] = None
    fecha_publicacion: Optional[date] = None
    guionista: Optional[str] = None
    sinopsis: Optional[str] = None

class ComicCreate(ComicBase):
    id_producto: int

class Comic(ComicBase):
    id_comic: int
    id_producto: int
    
    class Config:
        from_attributes = True

class ComicDetalle(Comic):
    producto: Producto
    
    class Config:
        from_attributes = True

class FiguraColeccionBase(BaseModel):
    personaje: Optional[str] = None
    universo: Optional[str] = None
    material: Optional[str] = None
    edicion_limitada: Optional[bool] = False
    numero_serie: Optional[str] = None

class FiguraColeccionCreate(FiguraColeccionBase):
    id_producto: int

class FiguraColeccion(FiguraColeccionBase):
    id_figura: int
    id_producto: int
    
    class Config:
        from_attributes = True

class FiguraColeccionDetalle(FiguraColeccion):
    producto: Producto
    
    class Config:
        from_attributes = True

class ProductoCompletoCreate(BaseModel):
    producto: ProductoCreate
    comic: Optional[ComicBase] = None
    figura: Optional[FiguraColeccionBase] = None