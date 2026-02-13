"""
Servicio BVC: API JWT (handshake + rest.bvc.com.co).
Datos de Renta Variable (mercado local y global). Usa httpx (sin requests/urllib3).
"""
import time
import uuid
from typing import Any

import httpx
import pandas as pd

from config import BVC_API_URL, BVC_BASE_URL

COLS_NUMERICAS = ["lastPrice", "openPrice", "maximumPrice", "minimumPrice", "volume", "quantity"]

# Headers que imitan el navegador (Referer/Origin suelen ser obligatorios)
BVC_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bvc.com.co/mercado-local-en-linea",
    "Origin": "https://www.bvc.com.co",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}

# Timeouts: handshake rápido; API de datos puede tardar más
HANDSHAKE_TIMEOUT = 15.0
API_TIMEOUT = 45.0

# Último error HTTP (para ?debug=1 en el endpoint)
_last_bvc_error: dict | None = None


def _set_last_error(status_code: int | None, text: str | None) -> None:
    global _last_bvc_error
    if status_code is None:
        _last_bvc_error = None
        return
    _last_bvc_error = {"status_code": status_code, "body_preview": (text or "")[:500]}


def _process_tab_data(lista: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convierte lista de tab a dicts con columnas numéricas tipadas."""
    if not lista:
        return []
    df = pd.DataFrame(lista)
    for col in COLS_NUMERICAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.to_dict(orient="records")


class BVCApi:
    """
    Cliente para la API de la BVC.
    Usa una sola sesión (httpx.Client) para handshake y petición de datos,
    así las cookies se comparten entre www.bvc.com.co y rest.bvc.com.co.
    """

    def __init__(self, base_url: str = BVC_BASE_URL, api_url: str = BVC_API_URL):
        self.base_url = base_url
        self.api_url = api_url
        self.token: str | None = None

    def _get_handshake_token(self, client: httpx.Client) -> str | None:
        """Obtiene el token JWT vía handshake (usando el mismo client para cookies)."""
        try:
            timestamp = int(time.time() * 1000)
            random_uuid = str(uuid.uuid4())
            url = f"{self.base_url}/api/handshake"
            params = {"ts": timestamp, "r": random_uuid}

            response = client.get(url, params=params, timeout=HANDSHAKE_TIMEOUT)
            _set_last_error(response.status_code, response.text)
            response.raise_for_status()
            data = response.json()

            token = data.get("token")
            if not token:
                return None
            return token

        except httpx.HTTPError:
            return None

    def _get_mercado_rv(self, boards: list[str]) -> list[dict[str, Any]] | None:
        """
        Obtiene data de Renta Variable (rest.bvc.com.co/market-information/rv/lvl-2).
        boards: ["EQTY","REPO","TTV"] para mercado local, ["MGC"] para mercado global.
        """
        with httpx.Client(
            headers=BVC_HEADERS,
            timeout=API_TIMEOUT,
            follow_redirects=True,
        ) as client:
            # 1) Handshake (mismo client para guardar cookies)
            self.token = self._get_handshake_token(client)
            if not self.token:
                return None

            # 2) Cookie y headers para token
            client.cookies.set("token", self.token, domain=".bvc.com.co", path="/")
            url = f"{self.api_url}/market-information/rv/lvl-2"
            fecha_hoy = pd.Timestamp.now().strftime("%Y-%m-%d")
            params = [
                ("filters[marketDataRv][tradeDate]", fecha_hoy),
                *[("filters[marketDataRv][board]", b) for b in boards],
                ("sorter[]", "tradeValue"),
                ("sorter[]", "DESC"),
            ]
            headers = {
                **BVC_HEADERS,
                "Authorization": f"Bearer {self.token}",
                "token": self.token,  # AUTH-2 "Missing token" suele esperar este nombre
                "x-jwt-token": self.token,
            }

            try:
                response = client.get(url, params=params, headers=headers, timeout=API_TIMEOUT)
                _set_last_error(response.status_code, response.text)

                if response.status_code == 401:
                    self.token = self._get_handshake_token(client)
                    if not self.token:
                        return None
                    client.cookies.set("token", self.token, domain=".bvc.com.co", path="/")
                    headers = {
                        **BVC_HEADERS,
                        "Authorization": f"Bearer {self.token}",
                        "token": self.token,
                        "x-jwt-token": self.token,
                    }
                    response = client.get(url, params=params, headers=headers, timeout=API_TIMEOUT)
                    _set_last_error(response.status_code, response.text)

                response.raise_for_status()
                _set_last_error(None, None)
                json_data = response.json()
            except httpx.HTTPError:
                return None

        lista_acciones = json_data.get("data", {}).get("tab", [])
        return _process_tab_data(lista_acciones)

    def get_mercado_local(self) -> list[dict[str, Any]] | None:
        """Mercado local: EQTY, REPO, TTV."""
        return self._get_mercado_rv(["EQTY", "REPO", "TTV"])

    def get_mercado_global(self) -> list[dict[str, Any]] | None:
        """Mercado Global Colombiano (MGC)."""
        return self._get_mercado_rv(["MGC"])


def get_mercado_local() -> list[dict[str, Any]] | None:
    """Mercado local (EQTY, REPO, TTV). Solo API (httpx)."""
    return BVCApi().get_mercado_local()


def get_mercado_global() -> list[dict[str, Any]] | None:
    """Mercado Global Colombiano (MGC). Solo API (httpx)."""
    return BVCApi().get_mercado_global()
