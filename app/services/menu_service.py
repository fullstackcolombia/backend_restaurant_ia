from typing import List, Optional
from app.database import supabase
from app.models import Category, MenuItem


class MenuService:
    """Servicio para gestionar el menú del restaurante"""
    
    @staticmethod
    async def get_categories() -> List[dict]:
        """Obtiene todas las categorías"""
        if not supabase:
            return []
        response = supabase.table("categories").select("*").execute()
        return response.data
    
    @staticmethod
    async def get_category(category_id: int) -> Optional[dict]:
        """Obtiene una categoría por ID"""
        if not supabase:
            return None
        response = supabase.table("categories").select("*").eq("id", category_id).single().execute()
        return response.data
    
    @staticmethod
    async def create_category(data: dict) -> Optional[dict]:
        """Crea una nueva categoría"""
        if not supabase:
            return None
        response = supabase.table("categories").insert(data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    async def update_category(category_id: int, data: dict) -> Optional[dict]:
        """Actualiza una categoría"""
        if not supabase:
            return None
        # Verificar que existe
        existing = supabase.table("categories").select("id").eq("id", category_id).execute()
        if not existing.data:
            return None
        update_data = {k: v for k, v in data.items() if v is not None and k not in ['id', 'created_at']}
        response = supabase.table("categories").update(update_data).eq("id", category_id).execute()
        if response.data:
            return response.data[0]
        return await MenuService.get_category(category_id)
    
    @staticmethod
    async def delete_category(category_id: int) -> bool:
        """Elimina una categoría"""
        if not supabase:
            return False
        response = supabase.table("categories").delete().eq("id", category_id).execute()
        return bool(response.data)
    
    @staticmethod
    async def get_menu_items(category_id: Optional[int] = None, include_unavailable: bool = False) -> List[dict]:
        """Obtiene items del menú, opcionalmente filtrados por categoría"""
        if not supabase:
            return []
        query = supabase.table("menu_items").select("*, categories(name)")
        if category_id:
            query = query.eq("category_id", category_id)
        if not include_unavailable:
            query = query.eq("available", True)
        response = query.execute()
        return response.data
    
    @staticmethod
    async def get_all_menu_items() -> List[dict]:
        """Obtiene todos los items del menú (incluyendo no disponibles) para admin"""
        if not supabase:
            return []
        response = supabase.table("menu_items").select("*, categories(name)").order("name").execute()
        return response.data
    
    @staticmethod
    async def get_menu_item(item_id: int) -> Optional[dict]:
        """Obtiene un item del menú por ID"""
        if not supabase:
            return None
        response = supabase.table("menu_items").select("*, categories(name)").eq("id", item_id).single().execute()
        return response.data
    
    @staticmethod
    async def create_menu_item(data: dict) -> Optional[dict]:
        """Crea un nuevo item del menú"""
        if not supabase:
            return None
        response = supabase.table("menu_items").insert(data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    async def update_menu_item(item_id: int, data: dict) -> Optional[dict]:
        """Actualiza un item del menú"""
        if not supabase:
            return None
        # Filtrar campos que no deben actualizarse
        update_data = {k: v for k, v in data.items() if k not in ['id', 'created_at', 'categories']}
        # Realizar update y retornar el resultado
        response = supabase.table("menu_items").update(update_data).eq("id", item_id).execute()
        # Si hay data, retornarlo; si no, intentar obtener el item
        if response.data:
            return response.data[0]
        # Verificar si el item existe
        item = await MenuService.get_menu_item(item_id)
        return item
    
    @staticmethod
    async def delete_menu_item(item_id: int) -> bool:
        """Elimina un item del menú"""
        if not supabase:
            return False
        response = supabase.table("menu_items").delete().eq("id", item_id).execute()
        return bool(response.data)
    
    @staticmethod
    async def search_menu_items(query: str) -> List[dict]:
        """Busca items en el menú por nombre o descripción"""
        if not supabase:
            return []
        response = supabase.table("menu_items").select("*, categories(name)").ilike("name", f"%{query}%").eq("available", True).execute()
        return response.data
    
    @staticmethod
    async def get_full_menu() -> dict:
        """Obtiene el menú completo organizado por categorías"""
        if not supabase:
            return {"categories": []}
        
        categories = await MenuService.get_categories()
        menu = {"categories": []}
        
        for category in categories:
            items = await MenuService.get_menu_items(category["id"])
            menu["categories"].append({
                **category,
                "items": items
            })
        
        return menu


menu_service = MenuService()
