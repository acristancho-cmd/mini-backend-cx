"""
Servicio App Store: Estrategia Híbrida.
- iTunes Lookup API: rating y total de votos (rápido, fiable)
- iTunes Customer Reviews RSS API: comentarios (sin dependencias externas)
"""
import json
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen
from urllib.error import URLError, HTTPError


def get_itunes_rating(app_id: int, country: str = "co") -> tuple[float, int]:
    """
    Puerta rápida: iTunes Lookup API.
    Retorna (rating_exacto, numero_ratings).
    Usa URL localizada por país para evitar errores (ej: Fintual en mx).
    Usa urllib (stdlib) para evitar conflictos con urllib3/httpx.
    """
    url = f"https://itunes.apple.com/{country}/lookup?id={app_id}"
    with urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    results = data.get("results", [])
    if not results:
        return 0.0, 0
    app = results[0]
    # Algunas apps devuelven null para rating/count - manejar None
    rating_val = app.get("averageUserRating")
    count_val = app.get("userRatingCount")
    rating = float(rating_val) if rating_val is not None else 0.0
    count = int(count_val) if count_val is not None else 0
    return rating, count


def _parse_rss_review_entry(entry: dict) -> dict | None:
    """Extrae review de una entrada del RSS JSON. Retorna dict con date, review, userName."""
    try:
        updated = entry.get("updated")
        if isinstance(updated, dict):
            dt_str = updated.get("label", "")
        elif isinstance(updated, str):
            dt_str = updated
        else:
            return None
        if not dt_str:
            return None

        content = entry.get("content")
        if isinstance(content, dict):
            review_text = content.get("label", "")
        else:
            review_text = str(content) if content else ""

        author = entry.get("author") or {}
        name_obj = author.get("name") if isinstance(author, dict) else None
        author_name = name_obj.get("label", "") if isinstance(name_obj, dict) else str(name_obj or "")

        return {
            "date": dt_str,
            "review": review_text or "",
            "userName": author_name,
        }
    except Exception:
        return None


def get_appstore_reviews_itunes_rss(app_id: int, country: str = "co") -> list[dict]:
    """
    Obtiene reviews usando iTunes Customer Reviews RSS API (sin dependencias).
    URL: itunes.apple.com/{country}/rss/customerreviews/page={n}/id={id}/sortby=mostrecent/json
    Hasta 10 páginas, 50 reviews/página. Corte inteligente: para al pasar 30 días.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    all_reviews: list[dict] = []

    for page in range(1, 11):
        url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
        try:
            with urlopen(url, timeout=30) as resp:
                data = json.loads(resp.read().decode())
        except (URLError, HTTPError, json.JSONDecodeError):
            break

        feed = data.get("feed", {})
        entries = feed.get("entry", [])
        if not isinstance(entries, list):
            entries = [entries] if entries else []

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            # Primera entrada suele ser info de la app, no review
            if "content" not in entry and "rating" not in entry:
                continue
            r = _parse_rss_review_entry(entry)
            if r is None:
                continue
            dt_str = r.get("date", "")
            try:
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt < cutoff:
                return all_reviews
            all_reviews.append(r)

        if len(entries) < 50:
            break

    return all_reviews


def get_appstore_reviews_last_month(app_id: int, country: str = "co") -> list[dict]:
    """
    Obtiene reviews del último mes.
    Usa iTunes Customer Reviews RSS API (stdlib, sin dependencias externas).
    Corte inteligente: orden por más recientes, detener al pasar 30 días.
    """
    return get_appstore_reviews_itunes_rss(app_id, country)


def get_appstore_trii_rating_only(app_id: int, country: str = "co") -> dict:
    """Retorna solo rating_global y total_votos de Trii en App Store."""
    rating, total_votos = get_itunes_rating(app_id, country)
    return {"rating_global": rating, "total_votos": total_votos}


def get_appstore_trii_comments_only(app_id: int, country: str = "co") -> list[dict]:
    """Retorna solo comentarios del último mes (misma lógica que trii)."""
    rating, total_votos = get_itunes_rating(app_id, country)
    try:
        raw_reviews = get_appstore_reviews_last_month(app_id, country)
    except Exception:
        return []
    out = []
    for r in raw_reviews:
        date_val = r.get("date")
        if isinstance(date_val, datetime):
            dt = date_val
        elif isinstance(date_val, str):
            dt = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
        else:
            dt = None
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        out.append({
            "Rating_Global": rating,
            "Total_Votos": total_votos,
            "Fecha_Review": dt.isoformat() if dt else None,
            "Comentario": r.get("review", ""),
            "Usuario": r.get("userName"),
            "store": "appstore",
        })
    return out


def get_appstore_ratings_batch(apps: list[dict]) -> list[dict]:
    """Obtiene solo ratings de una lista de apps App Store. apps: [{"app_id": int, "country": str, "app_name": str}]"""
    results = []
    for item in apps:
        app_id = item.get("app_id")
        country = item.get("country", "co")
        app_name = item.get("app_name", str(app_id))
        if app_id is None:
            results.append({"app_name": app_name, "app_id": str(app_id), "error": "app_id requerido", "store": "appstore"})
            continue
        try:
            rating, total = get_itunes_rating(int(app_id), country)
            results.append({
                "app_name": app_name,
                "app_id": str(app_id),
                "rating_global": round(rating, 2),
                "total_votos": total,
                "store": "appstore",
            })
        except Exception as e:
            results.append({
                "app_name": app_name,
                "app_id": str(app_id),
                "error": str(e),
                "store": "appstore",
            })
    return results
