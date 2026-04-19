from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.db.supabase import get_supabase_client
from app.models.schemas import AuthRequest, AuthResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


def _value(obj: Any, key: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _extract_auth_response(result: Any, message: str) -> AuthResponse:
    user = getattr(result, "user", None)
    session = getattr(result, "session", None)

    return AuthResponse(
        user_id=_value(user, "id"),
        email=_value(user, "email"),
        access_token=_value(session, "access_token"),
        refresh_token=_value(session, "refresh_token"),
        message=message,
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: AuthRequest):
    try:
        client = get_supabase_client(required=True)
        result = client.auth.sign_up({"email": payload.email, "password": payload.password})
        return _extract_auth_response(result, "Signup successful. Confirm email if required.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signup failed: {exc}",
        ) from exc


@router.post("/login", response_model=AuthResponse)
def login(payload: AuthRequest):
    try:
        client = get_supabase_client(required=True)
        result = client.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
        return _extract_auth_response(result, "Login successful.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {exc}",
        ) from exc
