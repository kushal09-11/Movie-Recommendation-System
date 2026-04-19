from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db.repositories import RatingRepository
from app.dependencies import get_rating_repository, get_recommender
from app.models.schemas import RecommendationResponse
from app.services.auth_guard import assert_user_can_access, get_optional_bearer_token
from app.services.recommender import RecommenderService

router = APIRouter(tags=["Recommendations"])


@router.get("/recommend/demo/{movielens_user_id}", response_model=RecommendationResponse)
def recommend_demo_movies(
    movielens_user_id: str,
    top_n: int = Query(default=10, ge=5, le=50),
    recommender: RecommenderService = Depends(get_recommender),
):
    try:
        recommendation_rows, source = recommender.get_recommendations(
            user_id=movielens_user_id,
            top_n=top_n,
            external_ratings=None,
        )
        return RecommendationResponse(
            user_id=movielens_user_id,
            count=len(recommendation_rows),
            source=source,
            recommendations=recommendation_rows,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to generate demo recommendations: {exc}",
        ) from exc


@router.get("/recommend/{user_id}", response_model=RecommendationResponse)
def recommend_movies(
    user_id: str,
    top_n: int = Query(default=10, ge=5, le=50),
    bearer_token: str | None = Depends(get_optional_bearer_token),
    ratings: RatingRepository = Depends(get_rating_repository),
    recommender: RecommenderService = Depends(get_recommender),
):
    try:
        access_token = assert_user_can_access(user_id, bearer_token, enforce=ratings.using_supabase)
        user_ratings = ratings.get_user_ratings(user_id, access_token=access_token)
        recommendation_rows, source = recommender.get_recommendations(
            user_id=user_id,
            top_n=top_n,
            external_ratings=user_ratings,
        )
        return RecommendationResponse(
            user_id=user_id,
            count=len(recommendation_rows),
            source=source,
            recommendations=recommendation_rows,
        )
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to generate recommendations: {exc}",
        ) from exc
