"""
BVC: API, cache Supabase y job diario.
"""
from services.bvc.cache import get_bvc_from_db  # noqa: F401

__all__ = ["get_bvc_from_db"]
