"""
Router BVC: datos de Renta Variable (mercado local y global).

- GET /mercado-local, GET /mercado-global: leen desde Supabase (cache).
  Sin fecha = última fecha disponible; con fecha = filtro por día (historial 7 días).
- POST /fetch-and-save: obtiene datos de la API BVC para hoy y los guarda en Supabase.
  Pensado para ser llamado por Lovable (Edge Function + pg_cron) L-V 4:00 PM Colombia.
- POST /cleanup: borra registros con más de 7 días. Pensado para pg_cron 3:00 AM Colombia.
"""
from fastapi import APIRouter, Query

from services.bvc import get_bvc_from_db

router = APIRouter(prefix="/bvc", tags=["BVC"])


def _response_from_cache(market: str, fecha: str | None) -> dict:
    """Lee de Supabase; devuelve { data, trade_date? } o { data: [], error }."""
    data, trade_date = get_bvc_from_db(market, fecha=fecha)
    if data is not None:
        out = {"data": data}
        if trade_date:
            out["trade_date"] = trade_date
        return out
    return {
        "data": [],
        "error": "No hay datos para esta fecha. Consulte una fecha con datos (historial 7 días) o ejecute POST /bvc/fetch-and-save.",
    }


@router.get("/mercado-local")
def mercado_local(
    fecha: str | None = Query(None, description="Fecha YYYY-MM-DD. Sin valor = última fecha disponible (historial 7 días)."),
) -> dict:
    """Mercado local (solo EQTY con actividad). Datos desde cache Supabase."""
    return _response_from_cache("mercado_local", fecha)


@router.get("/mercado-global")
def mercado_global(
    fecha: str | None = Query(None, description="Fecha YYYY-MM-DD. Sin valor = última fecha disponible."),
) -> dict:
    """Mercado Global Colombiano (MGC). Datos desde cache Supabase."""
    return _response_from_cache("mercado_global", fecha)


@router.post("/fetch-and-save")
def fetch_and_save() -> dict:
    """
    Obtiene datos de la API BVC (mercado local y global para hoy) y los guarda en Supabase.
    Llamar desde Lovable (Edge Function) según pg_cron L-V 4:00 PM Colombia.
    """
    from services.bvc.job import run_bvc_fetch_and_save
    run_bvc_fetch_and_save()
    return {"ok": True, "message": "BVC fetch y guardado ejecutado (mercado_local + mercado_global)."}


@router.post("/cleanup")
def cleanup() -> dict:
    """
    Borra en Supabase los registros de bvc_market_cache con más de 7 días.
    Llamar desde Lovable según pg_cron 3:00 AM Colombia.
    """
    from services.bvc.job import run_bvc_cleanup
    run_bvc_cleanup(days=7)
    return {"ok": True, "message": "Cleanup ejecutado (registros > 7 días eliminados)."}