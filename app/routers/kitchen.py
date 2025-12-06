from fastapi import APIRouter, HTTPException
from typing import Optional
from app.models.schemas import OrderStatus, OrderUpdate
from app.services.order_service import order_service

router = APIRouter(prefix="/kitchen", tags=["Kitchen"])


@router.get("/orders")
async def get_kitchen_orders():
    """Obtiene todos los pedidos organizados para cocina"""
    return await order_service.get_orders_for_kitchen()


@router.get("/stats")
async def get_kitchen_stats():
    """Obtiene estadísticas de cocina"""
    return await order_service.get_kitchen_stats()


@router.patch("/orders/{order_id}/start")
async def start_preparing(order_id: int, cook_id: Optional[int] = None):
    """Marca un pedido como en preparación"""
    update_data = OrderUpdate(status=OrderStatus.PREPARING, cook_id=cook_id)
    order = await order_service.update_order(order_id, update_data, cook_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order


@router.patch("/orders/{order_id}/ready")
async def mark_ready(order_id: int, cook_id: Optional[int] = None):
    """Marca un pedido como listo para entregar"""
    update_data = OrderUpdate(status=OrderStatus.READY)
    order = await order_service.update_order(order_id, update_data, cook_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order


@router.patch("/orders/{order_id}/cancel")
async def cancel_order(order_id: int, cook_id: Optional[int] = None, notes: Optional[str] = None):
    """Cancela un pedido desde cocina"""
    update_data = OrderUpdate(status=OrderStatus.CANCELLED, notes=notes)
    order = await order_service.update_order(order_id, update_data, cook_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order
