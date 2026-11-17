"""FastAPI dependencies for request context."""
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.errors import AuthorizationError
from app.core.security import decode_jwt
from app.core.unit_of_work import UnitOfWork
from app.database import get_db
from app.repositories.auth_repository import AuthRepository


@dataclass
class Principal:
    """Authenticated principal information."""
    user_id: UUID
    scope: str
    customer_party_id: str | None
    colleague_reference: str | None
    brand: str
    session_id: UUID
    channel: str


def get_uow(db: Annotated[Session, Depends(get_db)]) -> UnitOfWork:
    """Get unit of work for current request."""
    return UnitOfWork(db)


def get_principal(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> Principal:
    """Get current authenticated principal from JWT token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        claims = decode_jwt(token)
        
        # Get session from database
        repo = AuthRepository(db)
        session = repo.session_by_id(UUID(claims["sid"]))
        
        if not session or session.revoked_at:
            raise AuthorizationError("Session invalid or revoked")
        
        # Get user
        from app.models.auth import UserAccount
        user = db.get(UserAccount, UUID(claims["sub"]))
        if not user:
            raise AuthorizationError("User not found")
        
        return Principal(
            user_id=user.id,
            scope=user.scope,
            customer_party_id=user.customer_party_id,
            colleague_reference=user.colleague_reference,
            brand=user.brand,
            session_id=session.id,
            channel=session.origin_channel
        )
    except (KeyError, ValueError, AuthorizationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


def require_scope(required_scope: str):
    """Dependency to enforce scope requirement."""
    
    def _check_scope(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.scope != required_scope:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required scope: {required_scope}"
            )
        return principal
    
    return _check_scope
