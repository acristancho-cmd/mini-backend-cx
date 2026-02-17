"""
CX-service: rating, comentarios (App/Play Store) y mercado BVC.
Solo endpoints GET; datos en vivo por llamada.
Job diario: 10:40 AM Colombia guarda BVC en Supabase; 3 AM limpia cache > 7 días.
"""
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import TRII_CONFIG, PLAYSTORE_COMPETITORS, APPSTORE_COMPETITORS, CRON_SECRET
from routers.bvc import router as bvc_router
from services.scrapers.appstore import (
    get_appstore_ratings_batch,
    get_appstore_trii_rating_only,
    get_appstore_trii_comments_only,
)
from services.scrapers.playstore import (
    get_playstore_ratings_batch,
    get_playstore_trii_rating_only,
    get_playstore_trii_comments_only,
)

app = FastAPI(
    title="CX-service",
    description="Rating y comentarios App/Play Store (TRII y competidores) y datos mercado BVC.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bvc_router)

# Scheduler: 10:40 AM y 3 AM hora Colombia (America/Bogota)
_scheduler = BackgroundScheduler(timezone="America/Bogota")


def _job_bvc_fetch():
    print("[bvc_scheduler] Ejecutando job BVC (fetch + guardar en Supabase)...")
    from services.bvc.job import run_bvc_fetch_and_save
    run_bvc_fetch_and_save()
    print("[bvc_scheduler] Job BVC terminado.")


def _job_bvc_cleanup():
    print("[bvc_scheduler] Ejecutando cleanup BVC (>7 días)...")
    from services.bvc.job import run_bvc_cleanup
    run_bvc_cleanup(days=7)
    print("[bvc_scheduler] Cleanup BVC terminado.")


@app.on_event("startup")
def start_scheduler():
    # Todos los días 10:40 AM Colombia: obtener BVC y guardar en Supabase
    _scheduler.add_job(_job_bvc_fetch, CronTrigger(hour=10, minute=40))
    # Todos los días 3:00 AM Colombia: borrar cache con más de 7 días
    _scheduler.add_job(_job_bvc_cleanup, CronTrigger(hour=3, minute=0))
    _scheduler.start()
    print("[bvc_scheduler] Scheduler iniciado. BVC fetch: 10:40 AM, cleanup: 3:00 AM (America/Bogota).")


@app.on_event("shutdown")
def shutdown_scheduler():
    _scheduler.shutdown(wait=False)


@app.get("/")
def root() -> dict:
    """Health check."""
    return {"service": "CX-service", "status": "ok"}


# ---------------------------------------------------------------------------
# Vercel Cron: solo se llama desde Vercel a las 10:09 AM Colombia (15:09 UTC).
# En Vercel el proceso no está siempre activo, así que el scheduler no corre; este endpoint sí.
# ---------------------------------------------------------------------------
@app.get("/api/cron/bvc-fetch")
def cron_bvc_fetch(authorization: str | None = Header(None)) -> dict:
    """Ejecuta el job BVC (fetch + guardar en Supabase). Vercel Cron 10:40 AM Colombia (15:40 UTC)."""
    if not CRON_SECRET or authorization != "Bearer " + CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    from services.bvc.job import run_bvc_fetch_and_save
    run_bvc_fetch_and_save()
    return {"ok": True, "message": "BVC fetch ejecutado"}


@app.get("/api/cron/bvc-cleanup")
def cron_bvc_cleanup(authorization: str | None = Header(None)) -> dict:
    """Borra cache BVC con más de 7 días. Vercel Cron 3:00 AM Colombia (08:00 UTC)."""
    if not CRON_SECRET or authorization != "Bearer " + CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    from services.bvc.job import run_bvc_cleanup
    run_bvc_cleanup(days=7)
    return {"ok": True, "message": "BVC cleanup ejecutado"}


# ---------------------------------------------------------------------------
# Endpoint 1: TRII - solo rating y total_votos (sin comentarios)
# ---------------------------------------------------------------------------
@app.get("/trii")
def get_trii() -> dict:
    """Rating y total de votos de la app Trii (Play Store + App Store)."""
    try:
        playstore_data = get_playstore_trii_rating_only(TRII_CONFIG.play_store_package)
        playstore_data["rating_global"] = round(playstore_data["rating_global"], 2)
    except Exception as e:
        playstore_data = {"error": str(e), "rating_global": None, "total_votos": None}

    try:
        appstore_data = get_appstore_trii_rating_only(
            TRII_CONFIG.app_store_id,
            TRII_CONFIG.app_store_country,
        )
        appstore_data["rating_global"] = round(appstore_data["rating_global"], 2)
    except Exception as e:
        appstore_data = {"error": str(e), "rating_global": None, "total_votos": None}

    return {"playstore": playstore_data, "appstore": appstore_data}


# ---------------------------------------------------------------------------
# Endpoint 2: TRII - solo comentarios del último mes
# ---------------------------------------------------------------------------
@app.get("/trii-comments")
def get_trii_comments() -> dict:
    """Comentarios del último mes de la app Trii (Play Store + App Store, corte 30 días)."""
    try:
        playstore_comments = get_playstore_trii_comments_only(TRII_CONFIG.play_store_package)
    except Exception as e:
        playstore_comments = []

    try:
        appstore_comments = get_appstore_trii_comments_only(
            TRII_CONFIG.app_store_id,
            TRII_CONFIG.app_store_country,
        )
    except Exception as e:
        appstore_comments = []

    return {"playstore": playstore_comments, "appstore": appstore_comments}


# ---------------------------------------------------------------------------
# Ratings competidores
# ---------------------------------------------------------------------------
@app.get("/ratings/playstore")
def get_playstore_ratings() -> list:
    """Ratings de competidores en Play Store (lista hardcodeada)."""
    return get_playstore_ratings_batch(PLAYSTORE_COMPETITORS, lang="es", country="co")


@app.get("/ratings/appstore")
def get_appstore_ratings() -> list:
    """Ratings de competidores en App Store (lista hardcodeada)."""
    return get_appstore_ratings_batch(APPSTORE_COMPETITORS)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
