"""
Scrapers: App Store y Play Store (ratings y comentarios).
"""
from services.scrapers.appstore import (
    get_appstore_ratings_batch,
    get_appstore_trii_comments_only,
    get_appstore_trii_rating_only,
)
from services.scrapers.playstore import (
    get_playstore_ratings_batch,
    get_playstore_trii_comments_only,
    get_playstore_trii_rating_only,
)

__all__ = [
    "get_appstore_ratings_batch",
    "get_appstore_trii_comments_only",
    "get_appstore_trii_rating_only",
    "get_playstore_ratings_batch",
    "get_playstore_trii_comments_only",
    "get_playstore_trii_rating_only",
]
