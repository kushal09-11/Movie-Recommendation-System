from functools import lru_cache

from app.config import get_settings
from app.db.repositories import RatingRepository
from app.db.supabase import get_supabase_client
from app.services.recommender import RecommenderService


@lru_cache
def get_recommender() -> RecommenderService:
    settings = get_settings()
    return RecommenderService(
        data_dir=settings.movielens_data_dir,
        model_dir=settings.model_dir,
        top_k_similar=settings.recommender_top_k_similar,
        min_similarity=settings.recommender_min_similarity,
        auto_download=settings.recommender_auto_download,
        max_ratings=settings.recommender_max_ratings,
    )


@lru_cache
def get_rating_repository() -> RatingRepository:
    settings = get_settings()
    return RatingRepository(
        client=get_supabase_client(required=False),
        local_store_path=settings.local_rating_store,
    )
