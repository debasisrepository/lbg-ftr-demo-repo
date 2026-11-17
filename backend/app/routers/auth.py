"""Auth router."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.errors import AuthorizationError
from app.database import get_db
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse, RefreshResponse
from app.services.auth_service import AuthService

router = APIRouter()


def get_auth_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    """Get auth service."""
    repo = AuthRepository(db)
    return AuthService(repo)


@router.post("/login", response_model=LoginResponse, status_code=200)
def login(request: LoginRequest, service: Annotated[AuthService, Depends(get_auth_service)], db: Annotated[Session, Depends(get_db)]):
    """Login endpoint."""
    try:
        response = service.login(request.username, request.password, request.channel)
        db.commit()
        return response
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=RefreshResponse, status_code=200)
def refresh(session_id: str, service: Annotated[AuthService, Depends(get_auth_service)], db: Annotated[Session, Depends(get_db)]):
    """Refresh token endpoint."""
    try:
        response = service.refresh(uuid.UUID(session_id))
        db.commit()
        return response
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/logout", status_code=204)
def logout(session_id: str, service: Annotated[AuthService, Depends(get_auth_service)], db: Annotated[Session, Depends(get_db)]):
    """Logout endpoint."""
    try:
        service.logout(uuid.UUID(session_id))
        db.commit()
    except AuthorizationError:
        pass  # Silent failure for logout
    return None


@router.get("/me", response_model=MeResponse, status_code=200)
def get_me(session_id: str, service: Annotated[AuthService, Depends(get_auth_service)], db: Annotated[Session, Depends(get_db)]):
    """Get current user endpoint."""
    try:
        response = service.get_me(uuid.UUID(session_id))
        db.commit()
        return response
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
