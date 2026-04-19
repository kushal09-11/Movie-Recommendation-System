from typing import Any

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.supabase import get_supabase_client

bearer_scheme = HTTPBearer(auto_error=False)


def _value(obj: Any, key: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def get_optional_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> str | None:
    if credentials is None:
        return None
    if credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid bearer token is required.",
        )
    return credentials.credentials


def assert_user_can_access(user_id: str, access_token: str | None, enforce: bool) -> str | None:
    if not enforce:
        return None

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization bearer token is required.",
        )

    try:
        client = get_supabase_client(required=True)
        result = client.auth.get_user(access_token)
        authenticated_user_id = _value(_value(result, "user"), "id")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Supabase token: {exc}",
        ) from exc

    if str(authenticated_user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user cannot access this user's ratings.",
        )

    return access_token
