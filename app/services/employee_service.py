from typing import List, Optional
from app.database import supabase
from app.models.schemas import EmployeeRole, EmployeeCreate


class EmployeeService:
    """Servicio para gestionar empleados"""
    
    @staticmethod
    async def get_employees(role: Optional[EmployeeRole] = None, active_only: bool = False) -> List[dict]:
        """Obtiene empleados (incluye inactivos para admin)"""
        if not supabase:
            return []
        
        query = supabase.table("employees").select("id, name, email, role, pin, active, created_at")
        
        if role:
            query = query.eq("role", role.value)
        if active_only:
            query = query.eq("active", True)
        
        response = query.order("name").execute()
        return response.data or []
    
    @staticmethod
    async def get_employee(employee_id: int) -> Optional[dict]:
        """Obtiene un empleado por ID"""
        if not supabase:
            return None
        
        response = supabase.table("employees").select(
            "id, name, email, role, pin, active, created_at"
        ).eq("id", employee_id).single().execute()
        
        return response.data
    
    @staticmethod
    async def login_by_pin(pin: str) -> Optional[dict]:
        """Login por PIN"""
        if not supabase:
            return None
        
        response = supabase.table("employees").select(
            "id, name, email, role, active"
        ).eq("pin", pin).eq("active", True).single().execute()
        
        return response.data
    
    @staticmethod
    async def create_employee(employee_data) -> Optional[dict]:
        """Crea un nuevo empleado"""
        if not supabase:
            return None
        
        # Manejar tanto dict como EmployeeCreate
        if hasattr(employee_data, 'dict'):
            data = {
                "name": employee_data.name,
                "email": getattr(employee_data, 'email', None),
                "pin": employee_data.pin,
                "role": employee_data.role.value if hasattr(employee_data.role, 'value') else employee_data.role,
                "active": True
            }
        else:
            data = {
                "name": employee_data.get("name"),
                "email": employee_data.get("email"),
                "pin": employee_data.get("pin"),
                "role": employee_data.get("role"),
                "active": employee_data.get("active", True)
            }
        
        response = supabase.table("employees").insert(data).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    @staticmethod
    async def update_employee(employee_id: int, update_data: dict) -> Optional[dict]:
        """Actualiza un empleado"""
        if not supabase:
            return None
        # Verificar que existe
        existing = supabase.table("employees").select("id").eq("id", employee_id).execute()
        if not existing.data:
            return None
        clean_data = {k: v for k, v in update_data.items() if v is not None and k not in ['id', 'created_at']}
        response = supabase.table("employees").update(clean_data).eq("id", employee_id).execute()
        if response.data:
            return response.data[0]
        return await EmployeeService.get_employee(employee_id)
    
    @staticmethod
    async def delete_employee(employee_id: int) -> bool:
        """Elimina un empleado"""
        if not supabase:
            return False
        
        response = supabase.table("employees").delete().eq("id", employee_id).execute()
        return bool(response.data)
    
    @staticmethod
    async def deactivate_employee(employee_id: int) -> bool:
        """Desactiva un empleado"""
        if not supabase:
            return False
        
        response = supabase.table("employees").update({
            "active": False
        }).eq("id", employee_id).execute()
        
        return bool(response.data)


employee_service = EmployeeService()
