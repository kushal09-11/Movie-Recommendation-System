from __future__ import annotations

import logging
from typing import Iterable

from supabase import Client

from app.db.supabase import get_supabase_client
from app.services.recommender import RecommenderService

logger = logging.getLogger(__name__)


def _chunks(rows: list[dict], size: int) -> Iterable[list[dict]]:
    for index in range(0, len(rows), size):
        yield rows[index : index + size]


def sync_dataset_to_supabase(
    recommender: RecommenderService,
    client: Client | None = None,
    batch_size: int = 500,
    include_ratings: bool = False,
    movies_table: str = "movie_lens_movies",
) -> dict[str, int]:
    client = client or get_supabase_client(required=True)
    movies, ratings = recommender.load_data()

    movie_rows = [
        {"id": int(row.id), "title": str(row.title), "genres": str(row.genres)}
        for row in movies.itertuples(index=False)
    ]

    movie_count = 0
    for batch in _chunks(movie_rows, batch_size):
        client.table(movies_table).upsert(batch, on_conflict="id").execute()
        movie_count += len(batch)

    rating_count = 0
    if include_ratings:
        rating_rows = [
            {
                "user_id": str(row.user_id),
                "movie_id": int(row.movie_id),
                "rating": float(row.rating),
            }
            for row in ratings.itertuples(index=False)
        ]
        for batch in _chunks(rating_rows, batch_size):
            client.table("ratings").upsert(batch, on_conflict="user_id,movie_id").execute()
            rating_count += len(batch)

    logger.info("Synced %s movies and %s ratings.", movie_count, rating_count)
    return {"movies": movie_count, "ratings": rating_count}
