"""
Mini Backend CX-service - TRII & Ratings
Endpoints GET para rating y comentarios de App Store y Play Store.
Todo hardcodeado: Trii + competidores.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import TRII_CONFIG, PLAYSTORE_COMPETITORS, APPSTORE_COMPETITORS
from services.playstore import get_playstore_ratings_batch, get_playstore_trii_rating_only, get_playstore_trii_comments_only
from services.appstore import get_appstore_ratings_batch, get_appstore_trii_rating_only, get_appstore_trii_comments_only

app = FastAPI(
    title="CX-service",
    description="Rating y comentarios de App Store y Play Store para TRII",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"service": "CX-service", "status": "ok"}


# ---------------------------------------------------------------------------
# Endpoint 1: TRII - solo rating y total_votos (sin comentarios)
# ---------------------------------------------------------------------------
@app.get("/trii")
def get_trii():
    """
    Retorna rating y total de votos de la app Trii.
    Play Store + App Store. Sin comentarios.
    """
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
def get_trii_comments():
    """
    Retorna solo comentarios del último mes de la app Trii.
    Misma lógica que antes (corte a 30 días). Play Store + App Store.
    """
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
# Endpoint 3: Ratings Play Store - competidores hardcodeados
# ---------------------------------------------------------------------------
@app.get("/ratings/playstore")
def get_playstore_ratings():
    """
    Retorna solo ratings (rating_global, total_votos) de competidores en Play Store.
    Lista hardcodeada: Flink, Hapi, tyba, Fintual, Zesty, Racional.
    """
    return get_playstore_ratings_batch(PLAYSTORE_COMPETITORS, lang="es", country="co")


# ---------------------------------------------------------------------------
# Endpoint 4: Ratings App Store - competidores hardcodeados
# ---------------------------------------------------------------------------
@app.get("/ratings/appstore")
def get_appstore_ratings():
    """
    Retorna solo ratings (rating_global, total_votos) de competidores en App Store.
    Lista hardcodeada: Flink, Hapi, tyba, Fintual (México).
    """
    return get_appstore_ratings_batch(APPSTORE_COMPETITORS)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
