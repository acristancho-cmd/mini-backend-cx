"""
API BVC: handshake + rest.bvc.com.co (mercado local y global).
"""
import base64
import time
import uuid
from typing import Any
from urllib.parse import urlencode

import httpx
import pandas as pd

from config import BVC_API_URL, BVC_BASE_URL

COLS_NUMERICAS = ["lastPrice", "openPrice", "maximumPrice", "minimumPrice", "volume", "quantity"]

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

HANDSHAKE_TIMEOUT = 15.0
API_TIMEOUT = 45.0

_last_bvc_error: dict | None = None


def _set_last_error(status_code: int | None, text: str | None) -> None:
    global _last_bvc_error
    if status_code is None:
        _last_bvc_error = None
        return
    _last_bvc_error = {"status_code": status_code, "body_preview": (text or "")[:500]}


def _process_tab_data(lista: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not lista:
        return []
    df = pd.DataFrame(lista)
    for col in COLS_NUMERICAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.to_dict(orient="records")


class BVCApi:
    def __init__(self, base_url: str = BVC_BASE_URL, api_url: str = BVC_API_URL):
        self.base_url = base_url
        self.api_url = api_url
        self.token: str | None = None

    def _get_handshake_token(self, client: httpx.Client) -> str | None:
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
                print("[bvc] handshake: respuesta sin token")
                return None
            print("[bvc] handshake: token OK")
            return token
        except httpx.HTTPError as e:
            print("[bvc] handshake error:", e)
            return None

    def _get_mercado_rv(self, boards: list[str], fecha: str | None = None) -> list[dict[str, Any]] | None:
        with httpx.Client(
            headers=BVC_HEADERS,
            timeout=API_TIMEOUT,
            follow_redirects=True,
        ) as client:
            self.token = self._get_handshake_token(client)
            if not self.token:
                print("[bvc] _get_mercado_rv: sin token, abortando")
                return None

            client.cookies.set("token", self.token, domain=".bvc.com.co", path="/")
            url = f"{self.api_url}/market-information/rv/lvl-2"
            trade_date = fecha if fecha else "2026-02-16"
            print("[bvc] _get_mercado_rv: fecha=%s boards=%s" % (trade_date, boards))
            params = [
                ("filters[marketDataRv][tradeDate]", trade_date),
                *[("filters[marketDataRv][board]", b) for b in boards],
                ("sorter[]", "tradeValue"),
                ("sorter[]", "DESC"),
            ]
            query_string = urlencode(params)
            k_header = base64.b64encode(query_string.encode()).decode()
            headers = {
                **BVC_HEADERS,
                "Authorization": f"Bearer {self.token}",
                "token": self.token,
                "x-jwt-token": self.token,
                "k": k_header,
            }

            try:
                response = client.get(url, params=params, headers=headers, timeout=API_TIMEOUT)
                _set_last_error(response.status_code, response.text)
                print("[bvc] API status=%s" % response.status_code)
                if response.status_code == 401:
                    self.token = self._get_handshake_token(client)
                    if not self.token:
                        return None
                    client.cookies.set("token", self.token, domain=".bvc.com.co", path="/")
                    headers = {**BVC_HEADERS, "Authorization": f"Bearer {self.token}", "token": self.token, "x-jwt-token": self.token, "k": k_header}
                    response = client.get(url, params=params, headers=headers, timeout=API_TIMEOUT)
                    _set_last_error(response.status_code, response.text)
                response.raise_for_status()
                _set_last_error(None, None)
                json_data = response.json()
            except httpx.HTTPError as e:
                print("[bvc] _get_mercado_rv error:", getattr(getattr(e, "response", None), "status_code", None), e)
                return None

        lista_acciones = json_data.get("data", {}).get("tab", [])
        print("[bvc] response OK, tab rows=%s" % len(lista_acciones))
        if lista_acciones:
            first = lista_acciones[0]
            print("[bvc] sample: volume=%s quantity=%s lastPrice=%s" % (first.get("volume"), first.get("quantity"), first.get("lastPrice")))
        return _process_tab_data(lista_acciones)

    def get_mercado_local(self, fecha: str | None = None) -> list[dict[str, Any]] | None:
        data = self._get_mercado_rv(["EQTY", "REPO", "TTV"], fecha=fecha)
        if data is None:
            print("[bvc] get_mercado_local: _get_mercado_rv devolvió None")
            return None
        print("[bvc] get_mercado_local: raw rows=%s" % len(data))
        eqty = [r for r in data if r.get("board") == "EQTY"]
        print("[bvc] get_mercado_local: EQTY rows=%s" % len(eqty))
        if eqty:
            with_vol = sum(1 for r in eqty if (r.get("volume") or 0) > 0)
            with_qty = sum(1 for r in eqty if (r.get("quantity") or 0) > 0)
            print("[bvc] get_mercado_local: con volume>0=%s, quantity>0=%s" % (with_vol, with_qty))
        out = [r for r in eqty if (r.get("volume") or 0) > 0 or (r.get("quantity") or 0) > 0]
        print("[bvc] get_mercado_local: resultado final rows=%s" % len(out))
        return out

    def get_mercado_global(self, fecha: str | None = None) -> list[dict[str, Any]] | None:
        data = self._get_mercado_rv(["MGC"], fecha=fecha)
        if data is None:
            return None
        return [r for r in data if (r.get("volume") or 0) > 0 or (r.get("quantity") or 0) > 0]
