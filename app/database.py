from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()

def get_supabase_client() -> Client:
    """Obtiene el cliente de Supabase"""
    return create_client(settings.supabase_url, settings.supabase_key)


supabase: Client = get_supabase_client() if settings.supabase_url else None
