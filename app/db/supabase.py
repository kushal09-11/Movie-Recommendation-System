from functools import lru_cache

from fastapi import HTTPException, status
from supabase import Client, create_client

from app.config import get_settings


def _build_supabase_client(required: bool, access_token: str | None = None) -> Client | None:
    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_key:
        if required:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY.",
            )
        return None

    try:
        client = create_client(settings.supabase_url, settings.supabase_key)
        if access_token:
            client.postgrest.auth(access_token)
        return client
    except HTTPException:
        raise
    except Exception as exc:
        if required:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Supabase client could not be initialized: {exc}",
            ) from exc
        return None


@lru_cache
def get_supabase_client(required: bool = True) -> Client | None:
    return _build_supabase_client(required=required)


def get_supabase_client_for_user(access_token: str) -> Client:
    client = _build_supabase_client(required=True, access_token=access_token)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not configured.",
        )
    return client
