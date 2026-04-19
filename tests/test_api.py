from types import SimpleNamespace
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.repositories import RatingRepository
from app.dependencies import get_rating_repository, get_recommender
from app.main import app
from app.routes import admin as admin_routes
from app.routes import auth as auth_routes
from app.services.recommender import RecommenderService


@pytest.fixture()
def runtime_dir():
    path = Path("tests") / "_runtime" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture()
def recommender(runtime_dir):
    movies_csv = runtime_dir / "movies.csv"
    ratings_csv = runtime_dir / "ratings.csv"

    movies_csv.write_text(
        "movieId,title,genres\n"
        "1,Toy Story (1995),Adventure|Animation|Children\n"
        "2,Jumanji (1995),Adventure|Children|Fantasy\n"
        "3,Heat (1995),Action|Crime|Thriller\n"
        "4,Sabrina (1995),Comedy|Romance\n"
        "5,GoldenEye (1995),Action|Adventure|Thriller\n"
        "6,Babe (1995),Children|Drama\n"
        "7,Clueless (1995),Comedy|Romance\n",
        encoding="utf-8",
    )
    ratings_csv.write_text(
        "userId,movieId,rating,timestamp\n"
        "1,1,5.0,100\n"
        "1,2,4.0,101\n"
        "2,1,4.5,102\n"
        "2,2,4.0,103\n"
        "2,6,4.5,104\n"
        "3,3,5.0,105\n"
        "3,5,4.0,106\n"
        "4,1,5.0,107\n"
        "4,6,4.5,108\n"
        "5,4,4.0,109\n"
        "5,7,4.5,110\n",
        encoding="utf-8",
    )

    service = RecommenderService(
        data_dir=runtime_dir,
        model_dir=runtime_dir / "models",
        top_k_similar=5,
        min_similarity=0.01,
        auto_download=False,
        max_ratings=0,
    )
    service.load_or_train(force_train=True)
    return service


@pytest.fixture()
def rating_repository(runtime_dir):
    return RatingRepository(client=None, local_store_path=runtime_dir / "local_ratings.json")


@pytest.fixture()
def client(recommender, rating_repository):
    app.dependency_overrides[get_recommender] = lambda: recommender
    app.dependency_overrides[get_rating_repository] = lambda: rating_repository

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_health_endpoint_reports_model_ready(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["model_ready"] is True


def test_auth_signup_and_login_with_supabase_client_mock(client, monkeypatch):
    fake_user = SimpleNamespace(id="auth-user-id", email="person@example.com")
    fake_session = SimpleNamespace(access_token="access-token", refresh_token="refresh-token")
    fake_result = SimpleNamespace(user=fake_user, session=fake_session)

    class FakeAuth:
        def sign_up(self, payload):
            assert payload["email"] == "person@example.com"
            return fake_result

        def sign_in_with_password(self, payload):
            assert payload["password"] == "correct-password"
            return fake_result

    monkeypatch.setattr(
        auth_routes,
        "get_supabase_client",
        lambda required=True: SimpleNamespace(auth=FakeAuth()),
    )

    signup = client.post(
        "/auth/signup",
        json={"email": "person@example.com", "password": "correct-password"},
    )
    login = client.post(
        "/auth/login",
        json={"email": "person@example.com", "password": "correct-password"},
    )

    assert signup.status_code == 201
    assert signup.json()["access_token"] == "access-token"
    assert login.status_code == 200
    assert login.json()["user_id"] == "auth-user-id"


def test_auth_validation_rejects_bad_email_and_short_password(client):
    response = client.post("/auth/login", json={"email": "bad", "password": "123"})

    assert response.status_code == 422


def test_movies_list_search_genre_and_pagination(client):
    response = client.get("/movies?limit=2&offset=0&search=toy&genre=animation")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "title": "Toy Story (1995)",
            "genres": "Adventure|Animation|Children",
        }
    ]


def test_movie_detail_and_not_found(client):
    found = client.get("/movies/1")
    missing = client.get("/movies/999999")

    assert found.status_code == 200
    assert found.json()["title"] == "Toy Story (1995)"
    assert missing.status_code == 404


def test_rating_insert_update_and_fetch(client):
    created = client.post(
        "/rate",
        json={"user_id": "new-user", "movie_id": 1, "rating": 4.5},
    )
    updated = client.post(
        "/rate",
        json={"user_id": "new-user", "movie_id": 1, "rating": 2.5},
    )
    ratings = client.get("/ratings/new-user")

    assert created.status_code == 201
    assert updated.status_code == 201
    assert ratings.status_code == 200
    assert ratings.json() == [{"user_id": "new-user", "movie_id": 1, "rating": 2.5}]


def test_rating_validation_and_missing_movie(client):
    bad_rating = client.post(
        "/rate",
        json={"user_id": "new-user", "movie_id": 1, "rating": 6.0},
    )
    missing_movie = client.post(
        "/rate",
        json={"user_id": "new-user", "movie_id": 999999, "rating": 4.0},
    )

    assert bad_rating.status_code == 422
    assert missing_movie.status_code == 404


def test_supabase_protected_rating_endpoint_requires_authorization(recommender):
    class ProtectedRatings:
        using_supabase = True

        def get_user_ratings(self, user_id, access_token=None):
            return []

    app.dependency_overrides[get_recommender] = lambda: recommender
    app.dependency_overrides[get_rating_repository] = lambda: ProtectedRatings()

    with TestClient(app) as test_client:
        response = test_client.get("/ratings/auth-user-id")

    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Authorization bearer token is required."


def test_recommendation_endpoint_returns_personalized_movies(client):
    response = client.get("/recommend/1?top_n=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "1"
    assert payload["count"] > 0
    assert payload["source"] == "personalized_movielens_ratings"
    assert all(movie["id"] not in {1, 2} for movie in payload["recommendations"])


def test_demo_recommendation_endpoint_uses_movielens_user_without_auth(client):
    response = client.get("/recommend/demo/1?top_n=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "1"
    assert payload["source"] == "personalized_movielens_ratings"
    assert payload["count"] > 0


def test_new_user_recommendations_fall_back_to_trending(client):
    response = client.get("/recommend/brand-new-user?top_n=5")

    assert response.status_code == 200
    assert response.json()["source"] == "trending"
    assert response.json()["count"] > 0


def test_recommendation_query_validation(client):
    response = client.get("/recommend/1?top_n=1000")

    assert response.status_code == 422


def test_admin_model_status_requires_token(client, monkeypatch):
    monkeypatch.setattr(
        admin_routes,
        "get_settings",
        lambda: SimpleNamespace(admin_api_token="admin-secret"),
    )

    response = client.get("/admin/model-status")

    assert response.status_code == 401


def test_admin_model_status_with_token(client, monkeypatch):
    monkeypatch.setattr(
        admin_routes,
        "get_settings",
        lambda: SimpleNamespace(admin_api_token="admin-secret"),
    )

    response = client.get("/admin/model-status", headers={"x-admin-token": "admin-secret"})

    assert response.status_code == 200
    assert response.json()["model_ready"] is True
    assert response.json()["movie_count"] == 7


def test_admin_sync_dataset_defaults_to_movies_only(client, monkeypatch):
    monkeypatch.setattr(
        admin_routes,
        "get_settings",
        lambda: SimpleNamespace(admin_api_token="admin-secret"),
    )

    def fake_sync_dataset_to_supabase(recommender, batch_size, include_ratings):
        assert batch_size == 100
        assert include_ratings is False
        return {"movies": recommender.movie_count, "ratings": 0}

    monkeypatch.setattr(
        admin_routes,
        "sync_dataset_to_supabase",
        fake_sync_dataset_to_supabase,
    )

    response = client.post(
        "/admin/sync-dataset?batch_size=100",
        headers={"x-admin-token": "admin-secret"},
    )

    assert response.status_code == 200
    assert response.json()["details"] == {"movies": 7, "ratings": 0}


def test_recommender_reports_bad_dataset_columns(runtime_dir):
    (runtime_dir / "movies.csv").write_text("bad,title,genres\n1,A,G\n", encoding="utf-8")
    (runtime_dir / "ratings.csv").write_text(
        "userId,movieId,rating\n1,1,5\n",
        encoding="utf-8",
    )
    service = RecommenderService(
        data_dir=runtime_dir,
        model_dir=runtime_dir / "models",
        auto_download=False,
    )

    with pytest.raises(RuntimeError, match="Movies CSV is missing required columns"):
        service.load_data()
