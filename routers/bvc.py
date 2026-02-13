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
    use_browser: bool = Query(False, description="Fuerza Playwright (navegador headless)"),
) -> dict:
    """Datos de Renta Variable mercado local (EQTY, REPO, TTV). API primero; Playwright si falla."""
    return _bvc_response(
        lambda: bvc_service.get_mercado_local(use_browser=use_browser),
        debug,
    )


@router.get("/mercado-global")
def mercado_global(
    debug: bool = Query(False, description="Incluye detalle del error cuando falla"),
    use_browser: bool = Query(False, description="Fuerza Playwright (navegador headless)"),
) -> dict:
    """Datos Mercado Global Colombiano (MGC). API primero; Playwright si falla."""
    return _bvc_response(
        lambda: bvc_service.get_mercado_global(use_browser=use_browser),
        debug,
    )
