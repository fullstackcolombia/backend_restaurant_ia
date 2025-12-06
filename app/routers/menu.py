from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.services.menu_service import menu_service

router = APIRouter(prefix="/menu", tags=["Menu"])


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category_id: Optional[int] = None
    available: bool = True
    image_url: Optional[str] = None


@router.get("/")
async def get_full_menu():
    """Obtiene el menú completo organizado por categorías"""
    return await menu_service.get_full_menu()


@router.get("/categories")
async def get_categories():
    """Obtiene todas las categorías"""
    return await menu_service.get_categories()


@router.get("/categories/{category_id}")
async def get_category(category_id: int):
    """Obtiene una categoría por ID"""
    category = await menu_service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


@router.post("/categories")
async def create_category(data: CategoryCreate):
    """Crea una nueva categoría"""
    result = await menu_service.create_category(data.dict())
    if not result:
        raise HTTPException(status_code=400, detail="Error creando categoría")
    return result


@router.put("/categories/{category_id}")
async def update_category(category_id: int, data: CategoryCreate):
    """Actualiza una categoría"""
    result = await menu_service.update_category(category_id, data.dict(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return result


@router.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    """Elimina una categoría"""
    success = await menu_service.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return {"message": "Categoría eliminada"}


@router.get("/items")
async def get_menu_items(category_id: Optional[int] = None):
    """Obtiene todos los items del menú para admin"""
    return await menu_service.get_all_menu_items()


@router.get("/items/{item_id}")
async def get_menu_item(item_id: int):
    """Obtiene un item del menú por ID"""
    item = await menu_service.get_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return item


@router.post("/items")
async def create_menu_item(data: MenuItemCreate):
    """Crea un nuevo item del menú"""
    result = await menu_service.create_menu_item(data.dict())
    if not result:
        raise HTTPException(status_code=400, detail="Error creando item")
    return result


@router.put("/items/{item_id}")
async def update_menu_item(item_id: int, data: MenuItemCreate):
    """Actualiza un item del menú"""
    result = await menu_service.update_menu_item(item_id, data.dict())
    if not result:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return result


@router.delete("/items/{item_id}")
async def delete_menu_item(item_id: int):
    """Elimina un item del menú"""
    success = await menu_service.delete_menu_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return {"message": "Item eliminado"}


@router.get("/search")
async def search_menu(q: str):
    """Busca items en el menú"""
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="La búsqueda debe tener al menos 2 caracteres")
    return await menu_service.search_menu_items(q)
