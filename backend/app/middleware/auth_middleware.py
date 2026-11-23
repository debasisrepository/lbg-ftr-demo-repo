"""
Authentication middleware providing get_current_user dependency.
Requirement: FR-AUTH-006
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer_profile_ref import CustomerProfileRef
from app.services.auth_service import AuthService

# HTTP Bearer token scheme
security = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)]
) -> CustomerProfileRef:
    """
    Dependency to get the current authenticated user from bearer token.
    
    Usage:
        @router.get("/protected")
        def protected_route(current_user: Annotated[CustomerProfileRef, Depends(get_current_user)]):
            return {"user_id": current_user.id}
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        db: Database session
    
    Returns:
        CustomerProfileRef for the authenticated user
    
    Raises:
        HTTPException: 401 if authentication fails
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_service = AuthService(db)
    
    try:
        return auth_service.get_current_user(credentials.credentials)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
