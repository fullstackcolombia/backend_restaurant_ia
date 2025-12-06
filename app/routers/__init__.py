from app.routers.menu import router as menu_router
from app.routers.orders import router as orders_router
from app.routers.voice import router as voice_router
from app.routers.kitchen import router as kitchen_router
from app.routers.waiter import router as waiter_router
from app.routers.cashier import router as cashier_router
from app.routers.employees import router as employees_router
from app.routers.tables import router as tables_router

__all__ = [
    "menu_router", 
    "orders_router", 
    "voice_router",
    "kitchen_router",
    "waiter_router",
    "cashier_router",
    "employees_router",
    "tables_router"
]
