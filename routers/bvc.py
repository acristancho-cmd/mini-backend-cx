"""
Router BVC: datos de Renta Variable (mercado local y global).
Lee desde Supabase (cache). Sin fecha = última fecha disponible; con fecha = filtro por día (historial 1 semana).
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
        "error": "No hay datos para esta fecha. Consulte una fecha con datos (historial 7 días) o espere al job de las 10:40 AM.",
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