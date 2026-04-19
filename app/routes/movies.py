from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_recommender
from app.models.schemas import MovieOut
from app.services.recommender import RecommenderService

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("", response_model=list[MovieOut])
def list_movies(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, min_length=1),
    genre: str | None = Query(default=None, min_length=1),
    recommender: RecommenderService = Depends(get_recommender),
):
    try:
        return recommender.list_movies(limit=limit, offset=offset, search=search, genre=genre)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to list movies: {exc}",
        ) from exc


@router.get("/{movie_id}", response_model=MovieOut)
def get_movie(movie_id: int, recommender: RecommenderService = Depends(get_recommender)):
    try:
        movie = recommender.get_movie(movie_id)
        if movie is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found.")
        return movie
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to fetch movie: {exc}",
        ) from exc
