"""
Cache BVC en Supabase: guardar/leer por fecha y limpiar historial > 7 días.
"""
from __future__ import annotations

import math
from typing import Any

from config import BVC_CACHE_TABLE, SUPABASE_SERVICE_KEY, SUPABASE_URL


def _sanitize_for_json(obj: Any) -> Any:
    """Convierte NaN/Inf a None para que el JSON sea válido (Supabase)."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(x) for x in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def _get_client():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        print("[bvc_cache] create_client falló: %s %s" % (type(e).__name__, e))
        return None


def save_bvc_day(trade_date: str, market: str, data: list[dict[str, Any]]) -> bool:
    client = _get_client()
    if not client:
        print("[bvc_cache] Cliente Supabase no disponible. SUPABASE_URL set=%s, SUPABASE_SERVICE_KEY set=%s" % (bool(SUPABASE_URL), bool(SUPABASE_SERVICE_KEY)))
        return False
    try:
        data_clean = _sanitize_for_json(data)
        payload = {"trade_date": trade_date, "market": market, "data": data_clean}
        client.table(BVC_CACHE_TABLE).upsert(payload, on_conflict="trade_date,market").execute()
        print("[bvc_cache] guardado OK trade_date=%s market=%s rows=%s" % (trade_date, market, len(data)))
        return True
    except Exception as e:
        print("[bvc_cache] error guardando: %s %s" % (type(e).__name__, e))
        return False


def get_bvc_from_db(market: str, fecha: str | None = None) -> tuple[list[dict[str, Any]] | None, str | None]:
    client = _get_client()
    if not client:
        return None, None
    try:
        if fecha:
            r = client.table(BVC_CACHE_TABLE).select("data,trade_date").eq("market", market).eq("trade_date", fecha).limit(1).execute()
        else:
            r = client.table(BVC_CACHE_TABLE).select("data,trade_date").eq("market", market).order("trade_date", desc=True).limit(1).execute()
        if r.data and len(r.data) > 0 and r.data[0].get("data") is not None:
            row = r.data[0]
            return row["data"], row.get("trade_date")
        return None, None
    except Exception as e:
        print("[bvc_cache] error leyendo:", e)
        return None, None


def cleanup_older_than(days: int = 7) -> bool:
    client = _get_client()
    if not client:
        return False
    try:
        from datetime import date, timedelta
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        client.table(BVC_CACHE_TABLE).delete().lt("trade_date", cutoff).execute()
        print("[bvc_cache] cleanup: borrado trade_date < %s" % cutoff)
        return True
    except Exception as e:
        print("[bvc_cache] error cleanup:", e)
        return False
