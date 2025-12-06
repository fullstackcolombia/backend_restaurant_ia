from typing import List, Optional
from app.database import supabase
from app.models.schemas import TableStatus, TableUpdate


class TableService:
    """Servicio para gestionar mesas"""
    
    @staticmethod
    async def get_tables() -> List[dict]:
        """Obtiene todas las mesas"""
        if not supabase:
            return []
        
        response = supabase.table("tables").select("*").order("number").execute()
        return response.data or []
    
    @staticmethod
    async def get_table(table_id: int) -> Optional[dict]:
        """Obtiene una mesa por ID"""
        if not supabase:
            return None
        
        response = supabase.table("tables").select("*").eq("id", table_id).single().execute()
        return response.data
    
    @staticmethod
    async def get_table_by_number(number: int) -> Optional[dict]:
        """Obtiene una mesa por número"""
        if not supabase:
            return None
        
        response = supabase.table("tables").select("*").eq("number", number).single().execute()
        return response.data
    
    @staticmethod
    async def create_table(data: dict) -> Optional[dict]:
        """Crea una nueva mesa"""
        if not supabase:
            return None
        
        response = supabase.table("tables").insert(data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    async def update_table(table_id: int, data: dict) -> Optional[dict]:
        """Actualiza una mesa"""
        if not supabase:
            return None
        # Verificar que existe
        existing = supabase.table("tables").select("id").eq("id", table_id).execute()
        if not existing.data:
            return None
        update_data = {k: v for k, v in data.items() if v is not None and k not in ['id', 'created_at']}
        response = supabase.table("tables").update(update_data).eq("id", table_id).execute()
        if response.data:
            return response.data[0]
        return await TableService.get_table(table_id)
    
    @staticmethod
    async def delete_table(table_id: int) -> bool:
        """Elimina una mesa"""
        if not supabase:
            return False
        
        response = supabase.table("tables").delete().eq("id", table_id).execute()
        return bool(response.data)
    
    @staticmethod
    async def update_table_status(table_id: int, status: TableStatus) -> Optional[dict]:
        """Actualiza el estado de una mesa"""
        if not supabase:
            return None
        
        response = supabase.table("tables").update({
            "status": status.value
        }).eq("id", table_id).execute()
        
        return response.data[0] if response.data else None
    
    @staticmethod
    async def get_available_tables() -> List[dict]:
        """Obtiene mesas disponibles"""
        if not supabase:
            return []
        
        response = supabase.table("tables").select("*").eq(
            "status", TableStatus.AVAILABLE.value
        ).order("number").execute()
        
        return response.data or []
    
    @staticmethod
    async def get_occupied_tables() -> List[dict]:
        """Obtiene mesas ocupadas con su pedido activo"""
        if not supabase:
            return []
        
        tables = supabase.table("tables").select("*").eq(
            "status", TableStatus.OCCUPIED.value
        ).order("number").execute()
        
        result = []
        for table in (tables.data or []):
            # Buscar pedido activo de la mesa
            order = supabase.table("orders").select("*").eq(
                "table_number", table["number"]
            ).neq("status", "completed").neq("status", "cancelled").order(
                "created_at", desc=True
            ).limit(1).execute()
            
            table_data = {**table}
            if order.data:
                table_data["current_order"] = order.data[0]
            result.append(table_data)
        
        return result
    
    @staticmethod
    async def get_tables_summary() -> dict:
        """Resumen del estado de las mesas"""
        if not supabase:
            return {}
        
        tables = await TableService.get_tables()
        
        return {
            "total": len(tables),
            "available": len([t for t in tables if t["status"] == "available"]),
            "occupied": len([t for t in tables if t["status"] == "occupied"]),
            "reserved": len([t for t in tables if t["status"] == "reserved"]),
            "cleaning": len([t for t in tables if t["status"] == "cleaning"]),
            "tables": tables
        }


table_service = TableService()
