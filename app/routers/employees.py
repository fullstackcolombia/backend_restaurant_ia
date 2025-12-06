from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from app.models.schemas import EmployeeRole, EmployeeCreate, EmployeeLogin
from app.services.employee_service import employee_service

router = APIRouter(prefix="/employees", tags=["Employees"])


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    pin: Optional[str] = None
    email: Optional[str] = None
    active: Optional[bool] = None


@router.get("/")
async def get_employees(role: Optional[EmployeeRole] = None):
    """Obtiene lista de empleados (incluye inactivos para admin)"""
    return await employee_service.get_employees(role, active_only=False)


@router.get("/{employee_id}")
async def get_employee(employee_id: int):
    """Obtiene un empleado por ID"""
    employee = await employee_service.get_employee(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return employee


@router.post("/login")
async def login(credentials: EmployeeLogin):
    """Login de empleado por PIN"""
    employee = await employee_service.login_by_pin(credentials.pin)
    if not employee:
        raise HTTPException(status_code=401, detail="PIN inválido")
    return employee


@router.post("/")
async def create_employee(employee: dict):
    """Crea un nuevo empleado"""
    result = await employee_service.create_employee(employee)
    if not result:
        raise HTTPException(status_code=400, detail="Error creando empleado")
    return result


@router.put("/{employee_id}")
async def update_employee(employee_id: int, data: EmployeeUpdate):
    """Actualiza un empleado"""
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    result = await employee_service.update_employee(employee_id, update_data)
    if not result:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return result


@router.delete("/{employee_id}")
async def delete_employee(employee_id: int):
    """Elimina un empleado"""
    success = await employee_service.delete_employee(employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return {"message": "Empleado eliminado"}


@router.patch("/{employee_id}/deactivate")
async def deactivate_employee(employee_id: int):
    """Desactiva un empleado"""
    success = await employee_service.deactivate_employee(employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return {"message": "Empleado desactivado"}
