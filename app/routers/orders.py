from fastapi import APIRouter, HTTPException
from typing import Optional
from app.models import OrderCreate, OrderStatus
from app.services.order_service import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/")
async def create_order(order: OrderCreate):
    """Crea un nuevo pedido"""
    if not order.items:
        raise HTTPException(status_code=400, detail="El pedido debe tener al menos un item")
    
    result = await order_service.create_order(order)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/")
async def get_orders(status: Optional[OrderStatus] = None):
    """Obtiene todos los pedidos, opcionalmente filtrados por estado"""
    return await order_service.get_orders(status)


@router.get("/{order_id}")
async def get_order(order_id: int):
    """Obtiene un pedido por ID"""
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order


@router.patch("/{order_id}/status")
async def update_order_status(order_id: int, status: OrderStatus):
    """Actualiza el estado de un pedido"""
    order = await order_service.update_order_status(order_id, status)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order


@router.get("/table/{table_number}")
async def get_orders_by_table(table_number: int):
    """Obtiene pedidos activos por número de mesa"""
    return await order_service.get_orders_by_table(table_number)
