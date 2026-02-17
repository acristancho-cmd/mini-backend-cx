"""
Servicio Play Store usando google-play-scraper.
Corte inteligente: orden por más recientes y detener al pasar 30 días.
"""
from datetime import datetime, timedelta, timezone

from google_play_scraper import Sort, app as gplay_app, reviews as gplay_reviews


def get_reviews_last_month(package_name: str, lang: str = "es", country: str = "co") -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    result_reviews: list[dict] = []
    continuation_token = None
    while True:
        result, continuation_token = gplay_reviews(
            package_name, lang=lang, country=country, sort=Sort.NEWEST, count=200, continuation_token=continuation_token,
        )
        for r in result:
            at = r.get("at")
            if at is None:
                continue
            if at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
            if at < cutoff:
                return result_reviews
            result_reviews.append(r)
        if not continuation_token:
            break
    return result_reviews


def get_app_rating(package_name: str, lang: str = "es", country: str = "co") -> tuple[float, int]:
    data = gplay_app(package_name, lang=lang, country=country)
    score_val = data.get("score")
    ratings_val = data.get("ratings")
    score = float(score_val) if score_val is not None else 0.0
    ratings = int(ratings_val) if ratings_val is not None else 0
    return score, ratings


def get_playstore_trii_rating_only(package_name: str) -> dict:
    score, total_votos = get_app_rating(package_name)
    return {"rating_global": score, "total_votos": total_votos}


def get_playstore_trii_comments_only(package_name: str) -> list[dict]:
    score, total_votos = get_app_rating(package_name)
    raw_reviews = get_reviews_last_month(package_name)
    out = []
    for r in raw_reviews:
        at = r.get("at")
        if at and at.tzinfo is None:
            at = at.replace(tzinfo=timezone.utc)
        out.append({
            "Rating_Global": score,
            "Total_Votos": total_votos,
            "Fecha_Review": at.isoformat() if at else None,
            "Comentario": r.get("content", ""),
            "Usuario": r.get("userName"),
            "store": "playstore",
        })
    return out


def get_playstore_ratings_batch(apps: list[dict], lang: str = "es", country: str = "co") -> list[dict]:
    results = []
    for item in apps:
        pkg = item.get("package_name", "")
        app_name = item.get("app_name", pkg)
        try:
            score, total = get_app_rating(pkg, lang=lang, country=country)
            results.append({"app_name": app_name, "app_id": pkg, "rating_global": round(score, 2), "total_votos": total, "store": "playstore"})
        except Exception as e:
            results.append({"app_name": app_name, "app_id": pkg, "error": str(e), "store": "playstore"})
    return results
