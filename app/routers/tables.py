from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from app.models.schemas import TableStatus, TableUpdate
from app.services.table_service import table_service

router = APIRouter(prefix="/tables", tags=["Tables"])


class TableCreate(BaseModel):
    number: int
    capacity: int = 4
    status: str = "available"


@router.get("/")
async def get_all_tables():
    """Obtiene todas las mesas"""
    return await table_service.get_tables()


@router.get("/summary")
async def get_tables_summary():
    """Obtiene resumen del estado de las mesas"""
    return await table_service.get_tables_summary()


@router.get("/available")
async def get_available_tables():
    """Obtiene mesas disponibles"""
    return await table_service.get_available_tables()


@router.get("/occupied")
async def get_occupied_tables():
    """Obtiene mesas ocupadas con pedidos activos"""
    return await table_service.get_occupied_tables()


@router.get("/{table_id}")
async def get_table(table_id: int):
    """Obtiene una mesa por ID"""
    table = await table_service.get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return table


@router.get("/number/{number}")
async def get_table_by_number(number: int):
    """Obtiene una mesa por número"""
    table = await table_service.get_table_by_number(number)
    if not table:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return table


@router.post("/")
async def create_table(data: TableCreate):
    """Crea una nueva mesa"""
    result = await table_service.create_table(data.dict())
    if not result:
        raise HTTPException(status_code=400, detail="Error creando mesa")
    return result


@router.put("/{table_id}")
async def update_table(table_id: int, data: TableCreate):
    """Actualiza una mesa"""
    result = await table_service.update_table(table_id, data.dict())
    if not result:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return result


@router.delete("/{table_id}")
async def delete_table(table_id: int):
    """Elimina una mesa"""
    success = await table_service.delete_table(table_id)
    if not success:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return {"message": "Mesa eliminada"}


@router.patch("/{table_id}/status")
async def update_table_status(table_id: int, status: TableStatus):
    """Actualiza el estado de una mesa"""
    table = await table_service.update_table_status(table_id, status)
    if not table:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return table
