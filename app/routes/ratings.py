from fastapi import APIRouter, Depends, HTTPException, status

from app.db.repositories import RatingRepository
from app.dependencies import get_rating_repository, get_recommender
from app.models.schemas import RatingCreate, RatingOut
from app.services.auth_guard import assert_user_can_access, get_optional_bearer_token
from app.services.recommender import RecommenderService

router = APIRouter(tags=["Ratings"])


@router.post("/rate", response_model=RatingOut, status_code=status.HTTP_201_CREATED)
def add_or_update_rating(
    payload: RatingCreate,
    bearer_token: str | None = Depends(get_optional_bearer_token),
    ratings: RatingRepository = Depends(get_rating_repository),
    recommender: RecommenderService = Depends(get_recommender),
):
    try:
        access_token = assert_user_can_access(
            payload.user_id,
            bearer_token,
            enforce=ratings.using_supabase,
        )
        if recommender.get_movie(payload.movie_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found.")
        return ratings.upsert_rating(
            payload.user_id,
            payload.movie_id,
            payload.rating,
            access_token=access_token,
        )
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to save rating: {exc}",
        ) from exc


@router.get("/ratings/{user_id}", response_model=list[RatingOut])
def get_ratings(
    user_id: str,
    bearer_token: str | None = Depends(get_optional_bearer_token),
    ratings: RatingRepository = Depends(get_rating_repository),
):
    try:
        access_token = assert_user_can_access(user_id, bearer_token, enforce=ratings.using_supabase)
        return ratings.get_user_ratings(user_id, access_token=access_token)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to fetch ratings: {exc}",
        ) from exc
