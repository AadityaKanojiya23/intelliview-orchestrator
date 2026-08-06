from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from config import API_TOKEN
from orchestrator.auth import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login",
    auto_error=False,
)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    x_api_token: str | None = Header(default=None),
):
    """
    Authenticate using either:
    - JWT Bearer token
    - Legacy X-API-Token
    - Plain API token passed as Bearer
    """

    # JWT authentication
    if token:
        payload = verify_access_token(token)
        if payload is not None:
            return payload
        # Fall back to checking if the bearer token is actually the raw API token
        if token == API_TOKEN:
            return {"role": "admin"}
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Legacy API token authentication
    if x_api_token == API_TOKEN:
        return {"role": "admin"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication",
    )


def require_role(role: str):
    """
    Restrict access to users with a specific role.
    """

    def checker(user=Depends(get_current_user)):
        if user.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        return user

    return checker
