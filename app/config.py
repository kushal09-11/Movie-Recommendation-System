from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_key: str | None = Field(default=None, alias="SUPABASE_KEY")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    admin_api_token: str | None = Field(default=None, alias="ADMIN_API_TOKEN")

    movielens_data_dir: Path = Field(default=Path("./data"), alias="MOVIELENS_DATA_DIR")
    model_dir: Path = Field(default=Path("./models"), alias="MODEL_DIR")
    local_rating_store: Path = Field(
        default=Path("./data/local_ratings.json"),
        alias="LOCAL_RATING_STORE",
    )

    recommender_top_k_similar: int = Field(default=80, alias="RECOMMENDER_TOP_K_SIMILAR")
    recommender_min_similarity: float = Field(default=0.05, alias="RECOMMENDER_MIN_SIMILARITY")
    recommender_auto_download: bool = Field(default=True, alias="RECOMMENDER_AUTO_DOWNLOAD")
    recommender_max_ratings: int = Field(default=1_000_000, alias="RECOMMENDER_MAX_RATINGS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
