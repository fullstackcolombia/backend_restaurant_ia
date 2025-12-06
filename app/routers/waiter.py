from fastapi import APIRouter, HTTPException
from typing import Optional
from app.models.schemas import OrderStatus, OrderUpdate, TableStatus
from app.services.order_service import order_service
from app.services.table_service import table_service

router = APIRouter(prefix="/waiter", tags=["Waiter"])


@router.get("/orders")
async def get_waiter_orders(waiter_id: Optional[int] = None):
    """Obtiene pedidos para el mesero"""
    return await order_service.get_orders_for_waiter(waiter_id)


@router.get("/tables")
async def get_tables_status():
    """Obtiene el estado de todas las mesas"""
    return await table_service.get_tables_summary()


@router.get("/tables/available")
async def get_available_tables():
    """Obtiene mesas disponibles"""
    return await table_service.get_available_tables()


@router.get("/tables/occupied")
async def get_occupied_tables():
    """Obtiene mesas ocupadas con su pedido activo"""
    return await table_service.get_occupied_tables()


@router.patch("/orders/{order_id}/confirm")
async def confirm_order(order_id: int, waiter_id: Optional[int] = None):
    """Confirma un pedido para enviarlo a cocina"""
    update_data = OrderUpdate(status=OrderStatus.CONFIRMED, waiter_id=waiter_id)
    order = await order_service.update_order(order_id, update_data, waiter_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order


@router.patch("/orders/{order_id}/deliver")
async def deliver_order(order_id: int, waiter_id: Optional[int] = None):
    """Marca un pedido como entregado al cliente"""
    update_data = OrderUpdate(status=OrderStatus.DELIVERED, waiter_id=waiter_id)
    order = await order_service.update_order(order_id, update_data, waiter_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order


@router.patch("/tables/{table_id}/status")
async def update_table_status(table_id: int, status: TableStatus):
    """Actualiza el estado de una mesa"""
    table = await table_service.update_table_status(table_id, status)
    if not table:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return table


@router.get("/orders/table/{table_number}")
async def get_table_orders(table_number: int):
    """Obtiene los pedidos activos de una mesa"""
    return await order_service.get_orders_by_table(table_number)
