from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    menu_router, orders_router, voice_router,
    kitchen_router, waiter_router, cashier_router,
    employees_router, tables_router
)

app = FastAPI(
    title="Restaurant IA API",
    description="API para sistema de restaurante con comandos de voz e IA - Incluye gestión de cocina, meseros y caja",
    version="2.0.0"
)

# Configurar CORS para permitir el frontend de React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers públicos
app.include_router(menu_router)
app.include_router(orders_router)
app.include_router(voice_router)

# Routers de gestión
app.include_router(kitchen_router)
app.include_router(waiter_router)
app.include_router(cashier_router)
app.include_router(employees_router)
app.include_router(tables_router)


@app.get("/")
async def root():
    return {
        "message": "Restaurant IA API",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "menu": "/menu",
            "orders": "/orders",
            "voice": "/voice",
            "kitchen": "/kitchen",
            "waiter": "/waiter", 
            "cashier": "/cashier",
            "employees": "/employees",
            "tables": "/tables"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
