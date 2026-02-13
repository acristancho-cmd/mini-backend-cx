"""
Configuración: Trii, competidores (Play/App Store) y BVC.
"""
from pydantic import BaseModel


class TriiConfig(BaseModel):
    """IDs de la app Trii en ambas tiendas."""

    # Play Store: package_name
    # URL: https://play.google.com/store/apps/details?id=com.triico.app&hl=es_CO
    play_store_package: str = "com.triico.app"

    # App Store: app_id numérico y país (ratings varían por país)
    # URL: https://apps.apple.com/co/app/trii/id1513826307
    app_store_id: int = 1513826307
    app_store_country: str = "co"


TRII_CONFIG = TriiConfig()


# ---------------------------------------------------------------------------
# Competidores hardcodeados - Play Store (Colombia es_CO)
# ---------------------------------------------------------------------------
PLAYSTORE_COMPETITORS = [
    {"package_name": "com.miflink.android_app", "app_name": "Flink"},
    {"package_name": "com.hapicorp.imhapi", "app_name": "Hapi"},
    {"package_name": "com.tyba.app", "app_name": "tyba"},
    {"package_name": "cl.fintual.fintualapp", "app_name": "Fintual"},
    {"package_name": "com.treid", "app_name": "Zesty"},
    {"package_name": "cl.racional.app", "app_name": "Racional"},
]


# ---------------------------------------------------------------------------
# Competidores hardcodeados - App Store (México mx)
# ---------------------------------------------------------------------------
APPSTORE_COMPETITORS = [
    {"app_id": 1303438003, "country": "mx", "app_name": "Flink"},
    {"app_id": 1532828502, "country": "mx", "app_name": "Hapi"},
    {"app_id": 1460681130, "country": "mx", "app_name": "tyba"},
    {"app_id": 1485050953, "country": "mx", "app_name": "Fintual"},
]


# ---------------------------------------------------------------------------
# BVC (Bolsa de Valores de Colombia) - API protegida por JWT
# ---------------------------------------------------------------------------
BVC_BASE_URL = "https://www.bvc.com.co"
BVC_API_URL = "https://rest.bvc.com.co"
