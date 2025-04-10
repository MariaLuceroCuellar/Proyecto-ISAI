from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn

from .config import settings
from .api import auth, clientes, empleados, proveedores, productos, inventario, pedidos, compras

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="API para la tienda de cómics y figuras de acción"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejador de errores de validación
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Rutas API
app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(clientes.router, prefix="/clientes", tags=["Clientes"])
app.include_router(empleados.router, prefix="/empleados", tags=["Empleados"])
app.include_router(proveedores.router, prefix="/proveedores", tags=["Proveedores"])
app.include_router(productos.router, prefix="/productos", tags=["Productos"])
app.include_router(inventario.router, prefix="/inventario", tags=["Inventario"])
app.include_router(pedidos.router, prefix="/pedidos", tags=["Pedidos"])
app.include_router(compras.router, prefix="/compras", tags=["Compras"])

@app.get("/", tags=["Raíz"])
async def root():
    return {"message": "Bienvenido a la API de la tienda de cómics"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)