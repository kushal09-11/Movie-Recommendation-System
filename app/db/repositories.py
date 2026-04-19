import json
from pathlib import Path
from threading import Lock
from typing import Any

from supabase import Client

from app.db.supabase import get_supabase_client_for_user


class LocalRatingStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()

    def upsert(self, user_id: str, movie_id: int, rating: float) -> dict[str, Any]:
        with self._lock:
            rows = self._read()
            rows = [
                row
                for row in rows
                if not (str(row["user_id"]) == str(user_id) and int(row["movie_id"]) == int(movie_id))
            ]
            record = {"user_id": str(user_id), "movie_id": int(movie_id), "rating": float(rating)}
            rows.append(record)
            self._write(rows)
            return record

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [row for row in self._read() if str(row["user_id"]) == str(user_id)]

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []

    def _write(self, rows: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(rows, file, indent=2)


class RatingRepository:
    def __init__(self, client: Client | None, local_store_path: Path):
        self.client = client
        self.local_store = LocalRatingStore(local_store_path)

    @property
    def using_supabase(self) -> bool:
        return self.client is not None

    def upsert_rating(
        self,
        user_id: str,
        movie_id: int,
        rating: float,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        payload = {"user_id": str(user_id), "movie_id": int(movie_id), "rating": float(rating)}
        if self.client is None:
            return self.local_store.upsert(user_id, movie_id, rating)

        client = get_supabase_client_for_user(access_token) if access_token else self.client
        result = (
            client.table("ratings")
            .upsert(payload, on_conflict="user_id,movie_id")
            .execute()
        )
        data = result.data or []
        return self._normalize_rating_record(data[0] if data else payload)

    def get_user_ratings(
        self,
        user_id: str,
        access_token: str | None = None,
    ) -> list[dict[str, Any]]:
        if self.client is None:
            return self.local_store.list_for_user(user_id)

        client = get_supabase_client_for_user(access_token) if access_token else self.client
        result = (
            client.table("ratings")
            .select("user_id,movie_id,rating")
            .eq("user_id", str(user_id))
            .execute()
        )
        return [self._normalize_rating_record(row) for row in result.data or []]

    @staticmethod
    def _normalize_rating_record(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "user_id": str(row["user_id"]),
            "movie_id": int(row["movie_id"]),
            "rating": float(row["rating"]),
        }
