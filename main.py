"""
CX-service: rating, comentarios (App/Play Store) y mercado BVC.
Solo endpoints GET; datos en vivo por llamada.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import TRII_CONFIG, PLAYSTORE_COMPETITORS, APPSTORE_COMPETITORS
from routers.bvc import router as bvc_router
from services.appstore import (
    get_appstore_ratings_batch,
    get_appstore_trii_rating_only,
    get_appstore_trii_comments_only,
)
from services.playstore import (
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


@app.get("/")
def root() -> dict:
    """Health check."""
    return {"service": "CX-service", "status": "ok"}


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
