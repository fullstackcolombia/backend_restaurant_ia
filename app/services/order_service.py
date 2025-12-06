from typing import List, Optional
from datetime import datetime, date
from app.database import supabase
from app.models import OrderCreate, OrderStatus
from app.models.schemas import PaymentStatus, PaymentMethod, OrderUpdate


class OrderService:
    """Servicio para gestionar pedidos"""
    
    TAX_RATE = 0.16  # 16% IVA
    
    @staticmethod
    async def create_order(order_data: OrderCreate) -> dict:
        """Crea un nuevo pedido"""
        if not supabase:
            return {"error": "Database not configured"}
        
        # Calcular totales
        subtotal = 0
        order_items = []
        
        for item in order_data.items:
            menu_item = supabase.table("menu_items").select("price, name").eq("id", item.menu_item_id).single().execute()
            if menu_item.data:
                unit_price = float(menu_item.data["price"])
                item_subtotal = unit_price * item.quantity
                subtotal += item_subtotal
                order_items.append({
                    "menu_item_id": item.menu_item_id,
                    "quantity": item.quantity,
                    "unit_price": unit_price,
                    "subtotal": item_subtotal,
                    "special_instructions": item.special_instructions
                })
        
        tax = subtotal * OrderService.TAX_RATE
        total = subtotal + tax
        
        # Crear pedido
        order_response = supabase.table("orders").insert({
            "table_number": order_data.table_number,
            "customer_name": order_data.customer_name,
            "notes": order_data.notes,
            "waiter_id": order_data.waiter_id,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "tip": 0,
            "discount": 0,
            "status": OrderStatus.PENDING.value,
            "payment_status": PaymentStatus.PENDING.value
        }).execute()
        
        if not order_response.data:
            return {"error": "Failed to create order"}
        
        order_id = order_response.data[0]["id"]
        
        # Crear items
        for item in order_items:
            item["order_id"] = order_id
        
        supabase.table("order_items").insert(order_items).execute()
        
        # Actualizar estado de la mesa
        if order_data.table_number:
            supabase.table("tables").update({
                "status": "occupied"
            }).eq("number", order_data.table_number).execute()
        
        # Registrar en historial
        await OrderService._log_status_change(order_id, OrderStatus.PENDING.value, order_data.waiter_id)
        
        return {
            **order_response.data[0],
            "items": order_items
        }
        
        supabase.table("order_items").insert(order_items).execute()
        
        return {
            **order_response.data[0],
            "items": order_items
        }
    
    @staticmethod
    async def get_order(order_id: int) -> Optional[dict]:
        """Obtiene un pedido con sus items"""
        if not supabase:
            return None
        
        order = supabase.table("orders").select("*").eq("id", order_id).single().execute()
        if not order.data:
            return None
        
        items = supabase.table("order_items").select("*, menu_items(name)").eq("order_id", order_id).execute()
        
        # Agregar nombre del item
        items_with_names = []
        for item in (items.data or []):
            item_data = {**item}
            if item.get("menu_items"):
                item_data["menu_item_name"] = item["menu_items"]["name"]
            items_with_names.append(item_data)
        
        return {
            **order.data,
            "items": items_with_names
        }
    
    @staticmethod
    async def get_orders(
        status: Optional[OrderStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        table_number: Optional[int] = None,
        waiter_id: Optional[int] = None
    ) -> List[dict]:
        """Obtiene pedidos con filtros"""
        if not supabase:
            return []
        
        query = supabase.table("orders").select("*")
        
        if status:
            query = query.eq("status", status.value)
        if payment_status:
            query = query.eq("payment_status", payment_status.value)
        if table_number:
            query = query.eq("table_number", table_number)
        if waiter_id:
            query = query.eq("waiter_id", waiter_id)
        
        response = query.order("created_at", desc=True).execute()
        return response.data or []
    
    @staticmethod
    async def get_orders_by_status_list(statuses: List[OrderStatus]) -> List[dict]:
        """Obtiene pedidos por lista de estados"""
        if not supabase:
            return []
        
        status_values = [s.value for s in statuses]
        response = supabase.table("orders").select(
            "*, order_items(*, menu_items(name))"
        ).in_("status", status_values).order("created_at").execute()
        
        return response.data or []
    
    @staticmethod
    async def update_order(order_id: int, update_data: OrderUpdate, employee_id: Optional[int] = None) -> Optional[dict]:
        """Actualiza un pedido"""
        if not supabase:
            return None
        
        update_dict = {}
        
        if update_data.status:
            update_dict["status"] = update_data.status.value
            now = datetime.now().isoformat()
            if update_data.status == OrderStatus.READY:
                update_dict["prepared_at"] = now
            elif update_data.status == OrderStatus.DELIVERED:
                update_dict["delivered_at"] = now
        
        if update_data.payment_status:
            update_dict["payment_status"] = update_data.payment_status.value
            if update_data.payment_status == PaymentStatus.PAID:
                update_dict["paid_at"] = datetime.now().isoformat()
        
        if update_data.payment_method:
            update_dict["payment_method"] = update_data.payment_method.value
        
        if update_data.tip is not None:
            update_dict["tip"] = update_data.tip
        
        if update_data.discount is not None:
            update_dict["discount"] = update_data.discount
            order = await OrderService.get_order(order_id)
            if order:
                new_total = float(order.get("subtotal", 0)) + float(order.get("tax", 0)) + float(order.get("tip", 0)) - update_data.discount
                update_dict["total"] = max(0, new_total)
        
        if update_data.notes:
            update_dict["notes"] = update_data.notes
        if update_data.cook_id:
            update_dict["cook_id"] = update_data.cook_id
        if update_data.waiter_id:
            update_dict["waiter_id"] = update_data.waiter_id
        if update_data.cashier_id:
            update_dict["cashier_id"] = update_data.cashier_id
        
        if not update_dict:
            return await OrderService.get_order(order_id)
        
        supabase.table("orders").update(update_dict).eq("id", order_id).execute()
        
        if update_data.status:
            await OrderService._log_status_change(order_id, update_data.status.value, employee_id)
        
        return await OrderService.get_order(order_id)
    
    @staticmethod
    async def update_order_status(order_id: int, status: OrderStatus, employee_id: Optional[int] = None) -> Optional[dict]:
        """Actualiza solo el estado de un pedido"""
        update_data = OrderUpdate(status=status)
        return await OrderService.update_order(order_id, update_data, employee_id)
    
    @staticmethod
    async def process_payment(
        order_id: int, 
        payment_method: PaymentMethod,
        tip: float = 0,
        discount: float = 0,
        cashier_id: Optional[int] = None
    ) -> Optional[dict]:
        """Procesa el pago de un pedido"""
        if not supabase:
            print("ERROR: Supabase not configured")
            return None
        
        try:
            order = await OrderService.get_order(order_id)
            if not order:
                print(f"ERROR: Order {order_id} not found")
                return None
            
            # Calcular subtotal desde los items si es 0
            subtotal = float(order.get("subtotal", 0))
            if subtotal == 0:
                # Obtener items y calcular subtotal
                items = order.get("order_items", [])
                subtotal = sum(float(item.get("subtotal", 0)) for item in items)
            
            tax = subtotal * OrderService.TAX_RATE  # Calcular IVA
            total = subtotal + tax + tip - discount
            
            update_dict = {
                "payment_method": payment_method.value,
                "payment_status": PaymentStatus.PAID.value,
                "status": OrderStatus.COMPLETED.value,
                "tip": tip,
                "discount": discount,
                "subtotal": subtotal,
                "tax": tax,
                "total": max(0, total),
                "paid_at": datetime.now().isoformat()
            }
            
            # Solo agregar cashier_id si no es None
            if cashier_id is not None:
                update_dict["cashier_id"] = cashier_id
            
            print(f"Updating order {order_id} with: {update_dict}")
            supabase.table("orders").update(update_dict).eq("id", order_id).execute()
            
            # Liberar mesa (ignorar errores)
            try:
                if order.get("table_number"):
                    supabase.table("tables").update({
                        "status": "cleaning"
                    }).eq("number", order["table_number"]).execute()
            except Exception as e:
                print(f"Warning: Could not update table status: {e}")
            
            # Log status change (ignorar errores)
            try:
                await OrderService._log_status_change(order_id, OrderStatus.COMPLETED.value, cashier_id, f"Pago: {payment_method.value}")
            except Exception as e:
                print(f"Warning: Could not log status change: {e}")
            
            return await OrderService.get_order(order_id)
        except Exception as e:
            print(f"ERROR in process_payment: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @staticmethod
    async def get_orders_for_kitchen() -> dict:
        """Obtiene pedidos organizados para cocina"""
        if not supabase:
            return {"pending": [], "preparing": [], "ready": []}
        
        pending = await OrderService.get_orders_by_status_list([OrderStatus.PENDING, OrderStatus.CONFIRMED])
        preparing = await OrderService.get_orders_by_status_list([OrderStatus.PREPARING])
        ready = await OrderService.get_orders_by_status_list([OrderStatus.READY])
        
        return {
            "pending": pending,
            "preparing": preparing,
            "ready": ready
        }
    
    @staticmethod
    async def get_orders_for_waiter(waiter_id: Optional[int] = None) -> dict:
        """Obtiene pedidos para mesero"""
        if not supabase:
            return {"ready_to_deliver": [], "my_active_orders": []}
        
        ready = await OrderService.get_orders_by_status_list([OrderStatus.READY])
        
        my_orders = []
        if waiter_id:
            response = supabase.table("orders").select(
                "*, order_items(*, menu_items(name))"
            ).eq("waiter_id", waiter_id).in_(
                "status", [OrderStatus.PENDING.value, OrderStatus.CONFIRMED.value, 
                          OrderStatus.PREPARING.value, OrderStatus.READY.value, 
                          OrderStatus.DELIVERED.value]
            ).order("created_at", desc=True).execute()
            my_orders = response.data or []
        
        return {
            "ready_to_deliver": ready,
            "my_active_orders": my_orders
        }
    
    @staticmethod
    async def get_orders_for_cashier() -> dict:
        """Obtiene pedidos para caja"""
        if not supabase:
            return {"pending_payment": [], "completed_today": []}
        
        pending = supabase.table("orders").select(
            "*, order_items(*, menu_items(name))"
        ).eq("payment_status", PaymentStatus.PENDING.value).in_(
            "status", [OrderStatus.DELIVERED.value, OrderStatus.COMPLETED.value]
        ).order("created_at").execute()
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        completed = supabase.table("orders").select("*").eq(
            "payment_status", PaymentStatus.PAID.value
        ).gte("paid_at", today.isoformat()).order("paid_at", desc=True).execute()
        
        return {
            "pending_payment": pending.data or [],
            "completed_today": completed.data or []
        }
    
    @staticmethod
    async def get_kitchen_stats() -> dict:
        """Estadísticas para cocina"""
        orders = await OrderService.get_orders_for_kitchen()
        return {
            "pending_orders": len(orders["pending"]),
            "preparing_orders": len(orders["preparing"]),
            "ready_orders": len(orders["ready"])
        }
    
    @staticmethod
    async def get_cashier_stats(filter_date: Optional[date] = None) -> dict:
        """Estadísticas para caja - por defecto hoy o fecha específica"""
        if not supabase:
            return {}
        
        # Usar fecha proporcionada o hoy
        target_date = filter_date if filter_date else datetime.now().date()
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        sales = supabase.table("orders").select("total, payment_method").eq(
            "payment_status", PaymentStatus.PAID.value
        ).gte("paid_at", start_of_day.isoformat()).lte("paid_at", end_of_day.isoformat()).execute()
        
        total_sales = sum(float(o["total"]) for o in (sales.data or []))
        cash_total = sum(float(o["total"]) for o in (sales.data or []) if o.get("payment_method") == "cash")
        card_total = sum(float(o["total"]) for o in (sales.data or []) if o.get("payment_method") == "card")
        
        pending = supabase.table("orders").select("id").eq(
            "payment_status", PaymentStatus.PENDING.value
        ).in_("status", [OrderStatus.DELIVERED.value]).execute()
        
        return {
            "total_sales_today": total_sales,
            "orders_completed_today": len(sales.data or []),
            "pending_payments": len(pending.data or []),
            "cash_total": cash_total,
            "card_total": card_total,
            "filter_date": target_date.isoformat()
        }
    
    @staticmethod
    async def get_orders_history(page: int = 1, limit: int = 20, status: Optional[str] = None) -> dict:
        """Obtiene historial de pedidos paginado"""
        if not supabase:
            return {"orders": [], "total": 0, "page": page, "limit": limit, "pages": 0}
        
        offset = (page - 1) * limit
        
        # Query para contar total
        count_query = supabase.table("orders").select("id", count="exact")
        if status:
            count_query = count_query.eq("status", status)
        count_result = count_query.execute()
        total = count_result.count or 0
        
        # Query para obtener datos
        data_query = supabase.table("orders").select("*, order_items(*, menu_items(name))")
        if status:
            data_query = data_query.eq("status", status)
        
        result = data_query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        
        return {
            "orders": result.data or [],
            "total": total,
            "page": page,
            "limit": limit,
            "pages": total_pages
        }
    
    @staticmethod
    async def _log_status_change(order_id: int, status: str, changed_by: Optional[int] = None, notes: str = None):
        """Registra cambio de estado en historial"""
        if not supabase:
            return
        try:
            supabase.table("order_status_history").insert({
                "order_id": order_id,
                "status": status,
                "changed_by": changed_by,
                "notes": notes
            }).execute()
        except:
            pass  # Ignorar errores de historial
    
    @staticmethod
    async def get_orders_by_table(table_number: int) -> List[dict]:
        """Obtiene pedidos por número de mesa"""
        if not supabase:
            return []
        
        response = supabase.table("orders").select("*").eq(
            "table_number", table_number
        ).neq("status", OrderStatus.COMPLETED.value).neq(
            "status", OrderStatus.CANCELLED.value
        ).execute()
        return response.data or []


order_service = OrderService()
