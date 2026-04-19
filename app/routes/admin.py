from hmac import compare_digest

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.config import get_settings
from app.dependencies import get_recommender
from app.models.schemas import AdminActionResponse, ModelStatusResponse
from app.services.recommender import RecommenderService
from app.services.sync_dataset import sync_dataset_to_supabase

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    configured_token = get_settings().admin_api_token
    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_API_TOKEN is not configured.",
        )
    if not x_admin_token or not compare_digest(x_admin_token, configured_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid x-admin-token header is required.",
        )


@router.get("/model-status", response_model=ModelStatusResponse)
def model_status(
    _: None = Depends(require_admin_token),
    recommender: RecommenderService = Depends(get_recommender),
):
    try:
        return recommender.model_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to read model status: {exc}",
        ) from exc


@router.post("/retrain", response_model=AdminActionResponse)
def retrain_model(
    _: None = Depends(require_admin_token),
    recommender: RecommenderService = Depends(get_recommender),
):
    try:
        recommender.load_or_train(force_train=True)
        return {
            "message": "Recommendation model retrained successfully.",
            "details": recommender.model_status(),
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to retrain model: {exc}",
        ) from exc


@router.post("/sync-dataset", response_model=AdminActionResponse)
def sync_dataset(
    include_ratings: bool = Query(default=False),
    batch_size: int = Query(default=500, ge=1, le=5000),
    _: None = Depends(require_admin_token),
    recommender: RecommenderService = Depends(get_recommender),
):
    try:
        result = sync_dataset_to_supabase(
            recommender,
            batch_size=batch_size,
            include_ratings=include_ratings,
        )
        return {
            "message": "Dataset synced to Supabase.",
            "details": result,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to sync dataset: {exc}",
        ) from exc
