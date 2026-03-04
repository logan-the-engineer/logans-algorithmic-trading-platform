from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)

def require_auth(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> None:
    """Very small auth stub. Replace with real JWT validation."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Missing bearer token"}},
        )
