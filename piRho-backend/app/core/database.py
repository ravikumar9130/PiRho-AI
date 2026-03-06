"""Supabase database client and connection management."""
from functools import lru_cache
from supabase import create_client, Client

from app.config import get_settings


settings = get_settings()


@lru_cache()
def get_supabase_client() -> Client:
    """Get cached Supabase client instance."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def get_db() -> Client:
    """Dependency for database access."""
    return get_supabase_client()

