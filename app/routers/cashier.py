from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import date
import traceback
from app.models.schemas import PaymentRequest, PaymentMethod, TableStatus
from app.services.order_service import order_service
from app.services.table_service import table_service

router = APIRouter(prefix="/cashier", tags=["Cashier"])


@router.get("/orders")
async def get_cashier_orders():
    """Obtiene pedidos para caja (pendientes de pago y completados hoy)"""
    return await order_service.get_orders_for_cashier()


@router.get("/stats")
async def get_cashier_stats(filter_date: Optional[date] = Query(None, description="Fecha para filtrar estadísticas (YYYY-MM-DD)")):
    """Obtiene estadísticas de caja del día o de una fecha específica"""
    return await order_service.get_cashier_stats(filter_date)


@router.get("/history")
async def get_orders_history(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(20, ge=1, le=100, description="Items por página"),
    status: Optional[str] = Query(None, description="Filtrar por estado")
):
    """Obtiene historial de pedidos paginado"""
    return await order_service.get_orders_history(page, limit, status)


@router.post("/orders/{order_id}/pay")
async def process_payment(order_id: int, payment: PaymentRequest):
    """Procesa el pago de un pedido"""
    try:
        print(f"Processing payment for order {order_id}: {payment}")
        order = await order_service.process_payment(
            order_id=order_id,
            payment_method=payment.payment_method,
            tip=payment.tip,
            discount=payment.discount,
            cashier_id=payment.cashier_id
        )
        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        return order
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing payment: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}")
async def get_order_for_payment(order_id: int):
    """Obtiene los detalles de un pedido para pago"""
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order


@router.get("/tables/{table_number}/bill")
async def get_table_bill(table_number: int):
    """Obtiene la cuenta de una mesa"""
    orders = await order_service.get_orders_by_table(table_number)
    if not orders:
        raise HTTPException(status_code=404, detail="No hay pedidos activos en esta mesa")
    
    # Calcular totales
    subtotal = sum(float(o.get("subtotal", 0)) for o in orders)
    tax = sum(float(o.get("tax", 0)) for o in orders)
    total = sum(float(o.get("total", 0)) for o in orders)
    
    return {
        "table_number": table_number,
        "orders": orders,
        "summary": {
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "orders_count": len(orders)
        }
    }


@router.patch("/tables/{table_id}/clean")
async def mark_table_clean(table_id: int):
    """Marca una mesa como disponible después de limpiarla"""
    table = await table_service.update_table_status(table_id, TableStatus.AVAILABLE)
    if not table:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return table
