from __future__ import annotations

import logging
import pickle
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
from scipy.sparse import coo_matrix, csr_matrix, save_npz, load_npz
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

MOVIELENS_SMALL_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"


@dataclass
class ModelArtifacts:
    movies: pd.DataFrame
    ratings: pd.DataFrame
    movie_ids: np.ndarray
    movie_id_to_index: dict[int, int]
    popular_movie_ids: list[int]
    trending_movie_ids: list[int]


class RecommenderService:
    def __init__(
        self,
        data_dir: Path,
        model_dir: Path,
        top_k_similar: int = 80,
        min_similarity: float = 0.05,
        auto_download: bool = True,
        max_ratings: int = 1_000_000,
    ):
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.top_k_similar = top_k_similar
        self.min_similarity = min_similarity
        self.auto_download = auto_download
        self.max_ratings = max_ratings

        self.artifacts_path = self.model_dir / "recommender_artifacts.pkl"
        self.similarity_path = self.model_dir / "item_similarity.npz"

        self.artifacts: ModelArtifacts | None = None
        self.item_similarity: csr_matrix | None = None

    @property
    def is_ready(self) -> bool:
        return self.artifacts is not None and self.item_similarity is not None

    @property
    def movie_count(self) -> int:
        if self.artifacts is None:
            return 0
        return len(self.artifacts.movies)

    @property
    def ratings_count(self) -> int:
        if self.artifacts is None:
            return 0
        return len(self.artifacts.ratings)

    def model_status(self) -> dict[str, Any]:
        return {
            "model_ready": self.is_ready,
            "movie_count": self.movie_count,
            "ratings_count": self.ratings_count,
            "model_dir": str(self.model_dir),
            "artifacts_cached": self.artifacts_path.exists(),
            "similarity_cached": self.similarity_path.exists(),
            "min_similarity": self.min_similarity,
            "top_k_similar": self.top_k_similar,
        }

    def load_or_train(self, force_train: bool = False) -> None:
        self.model_dir.mkdir(parents=True, exist_ok=True)

        if not force_train and self.artifacts_path.exists() and self.similarity_path.exists():
            try:
                with self.artifacts_path.open("rb") as file:
                    self.artifacts = pickle.load(file)
                self.item_similarity = load_npz(self.similarity_path).tocsr()
                return
            except Exception:
                logger.exception("Cached recommender model is invalid. Rebuilding.")

        self.train_model()

    def load_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        movies_path, ratings_path = self._resolve_dataset_paths()
        movie_columns = {"movieId", "movie_id", "id", "title", "Title", "genres", "Genres"}
        rating_columns = {
            "userId",
            "user_id",
            "movieId",
            "movie_id",
            "rating",
            "Rating",
            "timestamp",
            "Timestamp",
        }
        nrows = self.max_ratings if self.max_ratings and self.max_ratings > 0 else None

        movies = pd.read_csv(movies_path, usecols=lambda column: column in movie_columns)
        ratings = pd.read_csv(
            ratings_path,
            usecols=lambda column: column in rating_columns,
            nrows=nrows,
        )

        movies = self._normalize_movie_columns(movies)
        ratings = self._normalize_rating_columns(ratings)

        movies = movies.dropna(subset=["id", "title"]).copy()
        movies["id"] = movies["id"].astype(int)
        movies["title"] = movies["title"].fillna("Untitled")
        movies["genres"] = movies["genres"].fillna("(no genres listed)")
        movies = movies.drop_duplicates(subset=["id"]).sort_values("id").reset_index(drop=True)

        ratings = ratings.dropna(subset=["user_id", "movie_id", "rating"]).copy()
        ratings["user_id"] = ratings["user_id"].astype(str)
        ratings["movie_id"] = ratings["movie_id"].astype(int)
        ratings["rating"] = ratings["rating"].astype(float).clip(0.5, 5.0)
        ratings = ratings[ratings["movie_id"].isin(set(movies["id"]))]
        ratings = ratings.drop_duplicates(subset=["user_id", "movie_id"], keep="last")
        ratings = ratings.reset_index(drop=True)

        if movies.empty or ratings.empty:
            raise RuntimeError("MovieLens data is empty after preprocessing.")

        return movies, ratings

    def train_model(self) -> None:
        movies, ratings = self.load_data()

        movie_ids = movies["id"].to_numpy(dtype=np.int64)
        movie_id_to_index = {int(movie_id): index for index, movie_id in enumerate(movie_ids)}

        user_codes, _ = pd.factorize(ratings["user_id"], sort=True)
        item_indices = ratings["movie_id"].map(movie_id_to_index).to_numpy(dtype=np.int64)
        values = ratings["rating"].to_numpy(dtype=np.float32)

        item_user_matrix = coo_matrix(
            (values, (item_indices, user_codes)),
            shape=(len(movie_ids), int(user_codes.max()) + 1),
            dtype=np.float32,
        ).tocsr()

        similarity = self._compute_sparse_similarity(item_user_matrix)

        popular_movie_ids = self._popular_movies(ratings, min_count=5)
        trending_movie_ids = self._trending_movies(ratings)

        self.artifacts = ModelArtifacts(
            movies=movies,
            ratings=ratings,
            movie_ids=movie_ids,
            movie_id_to_index=movie_id_to_index,
            popular_movie_ids=popular_movie_ids,
            trending_movie_ids=trending_movie_ids,
        )
        self.item_similarity = similarity

        with self.artifacts_path.open("wb") as file:
            pickle.dump(self.artifacts, file)
        save_npz(self.similarity_path, self.item_similarity)

    def get_recommendations(
        self,
        user_id: str,
        top_n: int = 10,
        external_ratings: list[dict[str, Any]] | None = None,
    ) -> tuple[list[dict[str, Any]], str]:
        self._ensure_ready()

        assert self.artifacts is not None
        assert self.item_similarity is not None

        explicit_ratings = self._ratings_from_external(external_ratings)
        if explicit_ratings:
            user_ratings = explicit_ratings
            source = "personalized_external_ratings"
        else:
            user_rows = self.artifacts.ratings[self.artifacts.ratings["user_id"] == str(user_id)]
            user_ratings = {
                int(row.movie_id): float(row.rating)
                for row in user_rows.itertuples(index=False)
            }
            source = "personalized_movielens_ratings"

        if not user_ratings:
            return self._fallback(top_n, already_rated=set(), source="trending")

        rated_movie_ids = set(user_ratings)
        scored = np.zeros(len(self.artifacts.movie_ids), dtype=np.float32)
        weights = np.zeros(len(self.artifacts.movie_ids), dtype=np.float32)

        for movie_id, rating in user_ratings.items():
            movie_index = self.artifacts.movie_id_to_index.get(int(movie_id))
            if movie_index is None:
                continue
            similarities = self.item_similarity.getrow(movie_index)
            if similarities.nnz == 0:
                continue
            sim_indices = similarities.indices
            sim_values = similarities.data
            useful = sim_values >= self.min_similarity
            sim_indices = sim_indices[useful]
            sim_values = sim_values[useful]
            if sim_values.size == 0:
                continue
            adjusted_rating = float(rating) - 3.0
            scored[sim_indices] += adjusted_rating * sim_values
            weights[sim_indices] += np.abs(sim_values)

        valid = weights > 0
        if not np.any(valid):
            return self._fallback(top_n, already_rated=rated_movie_ids, source="popular")

        scores = np.full(len(scored), -np.inf, dtype=np.float32)
        scores[valid] = scored[valid] / weights[valid]

        for movie_id in rated_movie_ids:
            movie_index = self.artifacts.movie_id_to_index.get(int(movie_id))
            if movie_index is not None:
                scores[movie_index] = -np.inf

        ranked_indices = np.argsort(scores)[::-1]
        rows = []
        seen = set()
        for index in ranked_indices:
            score = float(scores[index])
            if not np.isfinite(score):
                continue
            movie_id = int(self.artifacts.movie_ids[index])
            if movie_id in seen:
                continue
            movie = self.get_movie(movie_id)
            if movie is None:
                continue
            rows.append({**movie, "score": round(score + 3.0, 4)})
            seen.add(movie_id)
            if len(rows) >= top_n:
                break

        if not rows:
            return self._fallback(top_n, already_rated=rated_movie_ids, source="popular")

        return rows, source

    def list_movies(
        self,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        genre: str | None = None,
    ) -> list[dict[str, Any]]:
        self._ensure_ready()
        assert self.artifacts is not None

        frame = self.artifacts.movies
        if search:
            frame = frame[frame["title"].str.contains(search, case=False, na=False)]
        if genre:
            frame = frame[frame["genres"].str.contains(genre, case=False, na=False)]

        rows = frame.iloc[offset : offset + limit]
        return [
            {"id": int(row.id), "title": str(row.title), "genres": str(row.genres)}
            for row in rows.itertuples(index=False)
        ]

    def get_movie(self, movie_id: int) -> dict[str, Any] | None:
        self._ensure_ready()
        assert self.artifacts is not None

        rows = self.artifacts.movies[self.artifacts.movies["id"] == int(movie_id)]
        if rows.empty:
            return None
        row = rows.iloc[0]
        return {"id": int(row["id"]), "title": str(row["title"]), "genres": str(row["genres"])}

    def _resolve_dataset_paths(self) -> tuple[Path, Path]:
        candidate_dirs = [
            self.data_dir,
            Path("./data"),
            Path.home() / "Downloads" / "archive (1)",
            Path.home() / "Downloads" / "ml-latest-small",
        ]

        for directory in candidate_dirs:
            movies_path = self._first_existing(directory, ["movies.csv", "movie.csv"])
            ratings_path = self._first_existing(directory, ["ratings.csv", "rating.csv"])
            if movies_path and ratings_path:
                return movies_path, ratings_path

        if self.auto_download:
            self._download_movielens_small()
            movies_path = self._first_existing(self.data_dir, ["movies.csv", "movie.csv"])
            ratings_path = self._first_existing(self.data_dir, ["ratings.csv", "rating.csv"])
            if movies_path and ratings_path:
                return movies_path, ratings_path

        raise RuntimeError(
            "MovieLens dataset not found. Add movies.csv and ratings.csv to data/ "
            "or set MOVIELENS_DATA_DIR."
        )

    def _download_movielens_small(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        archive_path = self.data_dir / "ml-latest-small.zip"
        response = requests.get(MOVIELENS_SMALL_URL, timeout=60)
        response.raise_for_status()
        archive_path.write_bytes(response.content)

        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.namelist():
                filename = Path(member).name
                if filename in {"movies.csv", "ratings.csv"}:
                    target = self.data_dir / filename
                    target.write_bytes(archive.read(member))

    def _compute_sparse_similarity(self, item_user_matrix: csr_matrix) -> csr_matrix:
        rows = []
        cols = []
        data = []
        chunk_size = 256

        for start in range(0, item_user_matrix.shape[0], chunk_size):
            stop = min(start + chunk_size, item_user_matrix.shape[0])
            chunk_similarity = cosine_similarity(
                item_user_matrix[start:stop],
                item_user_matrix,
                dense_output=False,
            ).tocsr()

            for local_row_index in range(chunk_similarity.shape[0]):
                row_index = start + local_row_index
                row = chunk_similarity.getrow(local_row_index)
                if row.nnz == 0:
                    continue

                indices = row.indices
                values = row.data
                mask = (indices != row_index) & (values >= self.min_similarity)
                indices = indices[mask]
                values = values[mask]
                if values.size == 0:
                    continue
                if values.size > self.top_k_similar:
                    top_positions = np.argpartition(values, -self.top_k_similar)[-self.top_k_similar :]
                    indices = indices[top_positions]
                    values = values[top_positions]
                rows.extend([row_index] * len(indices))
                cols.extend(indices.tolist())
                data.extend(values.astype(np.float32).tolist())

        return csr_matrix(
            (np.array(data, dtype=np.float32), (rows, cols)),
            shape=(item_user_matrix.shape[0], item_user_matrix.shape[0]),
            dtype=np.float32,
        )

    def _popular_movies(self, ratings: pd.DataFrame, min_count: int = 5) -> list[int]:
        grouped = (
            ratings.groupby("movie_id")
            .agg(count=("rating", "size"), mean_rating=("rating", "mean"))
            .reset_index()
        )
        eligible = grouped[grouped["count"] >= min_count]
        if eligible.empty:
            eligible = grouped
        eligible = eligible.sort_values(["mean_rating", "count"], ascending=[False, False])
        return [int(movie_id) for movie_id in eligible["movie_id"].head(500)]

    def _trending_movies(self, ratings: pd.DataFrame) -> list[int]:
        if "timestamp" in ratings.columns:
            recent = ratings.sort_values("timestamp", ascending=False).head(max(1000, len(ratings) // 10))
        else:
            recent = ratings.tail(max(1000, len(ratings) // 10))
        return self._popular_movies(recent, min_count=2)

    def _fallback(
        self,
        top_n: int,
        already_rated: set[int],
        source: str,
    ) -> tuple[list[dict[str, Any]], str]:
        assert self.artifacts is not None
        ordered_ids = self.artifacts.trending_movie_ids if source == "trending" else self.artifacts.popular_movie_ids

        rows = []
        seen = set()
        for movie_id in ordered_ids:
            if movie_id in already_rated or movie_id in seen:
                continue
            movie = self.get_movie(movie_id)
            if movie is None:
                continue
            rows.append({**movie, "score": None})
            seen.add(movie_id)
            if len(rows) >= top_n:
                break
        return rows, source

    def _ratings_from_external(self, rows: list[dict[str, Any]] | None) -> dict[int, float]:
        ratings: dict[int, float] = {}
        for row in rows or []:
            try:
                ratings[int(row["movie_id"])] = float(row["rating"])
            except (KeyError, TypeError, ValueError):
                continue
        return ratings

    def _ensure_ready(self) -> None:
        if not self.is_ready:
            self.load_or_train()
        if not self.is_ready:
            raise RuntimeError("Recommendation model is not ready.")

    @staticmethod
    def _first_existing(directory: Path, names: list[str]) -> Path | None:
        for name in names:
            path = Path(directory) / name
            if path.exists():
                return path
        return None

    @staticmethod
    def _normalize_movie_columns(movies: pd.DataFrame) -> pd.DataFrame:
        renamed = movies.rename(
            columns={
                "movieId": "id",
                "movie_id": "id",
                "Title": "title",
                "Genres": "genres",
            }
        )
        required = {"id", "title", "genres"}
        missing = required - set(renamed.columns)
        if missing:
            raise RuntimeError(f"Movies CSV is missing required columns: {sorted(missing)}")
        return renamed[["id", "title", "genres"]]

    @staticmethod
    def _normalize_rating_columns(ratings: pd.DataFrame) -> pd.DataFrame:
        renamed = ratings.rename(
            columns={
                "userId": "user_id",
                "movieId": "movie_id",
                "Rating": "rating",
                "Timestamp": "timestamp",
            }
        )
        columns = ["user_id", "movie_id", "rating"]
        missing = set(columns) - set(renamed.columns)
        if missing:
            raise RuntimeError(f"Ratings CSV is missing required columns: {sorted(missing)}")
        if "timestamp" in renamed.columns:
            columns.append("timestamp")
        return renamed[columns]


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    from app.dependencies import get_recommender

    return get_recommender().load_data()


def train_model() -> None:
    from app.dependencies import get_recommender

    get_recommender().train_model()


def get_recommendations(user_id: str, top_n: int = 10) -> list[dict[str, Any]]:
    from app.dependencies import get_recommender

    rows, _ = get_recommender().get_recommendations(user_id=user_id, top_n=top_n)
    return rows
