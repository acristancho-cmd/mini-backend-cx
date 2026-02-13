"""
Router BVC: datos de Renta Variable (mercado local y global).
"""
from fastapi import APIRouter, Query

from services import bvc as bvc_service

router = APIRouter(prefix="/bvc", tags=["BVC"])


def _bvc_response(get_data, debug: bool) -> dict:
    """Respuesta unificada para endpoints BVC."""
    try:
        data = get_data()
        if data is not None:
            return {"data": data}
        msg = "No se pudo obtener la data (handshake o API fallida)"
        out: dict = {"error": msg, "data": []}
    except Exception as e:
        out = {"error": str(e), "data": []}
    if debug:
        out["debug"] = getattr(bvc_service, "_last_bvc_error", None)
    return out


@router.get("/mercado-local")
def mercado_local(
    debug: bool = Query(False, description="Incluye detalle del error cuando falla"),
) -> dict:
    """Datos de Renta Variable mercado local (EQTY, REPO, TTV)."""
    return _bvc_response(bvc_service.get_mercado_local, debug)


@router.get("/mercado-global")
def mercado_global(
    debug: bool = Query(False, description="Incluye detalle del error cuando falla"),
) -> dict:
    """Datos Mercado Global Colombiano (MGC)."""
    return _bvc_response(bvc_service.get_mercado_global, debug)
