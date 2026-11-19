from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.common.security import decode_access_token, hash_token
from app.models.auth import UserIdentity, AuthSession
from app.common.enums import SessionState


security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db)
) -> UserIdentity:
    """
    Dependency to get the current authenticated user.
    
    Validates JWT token and checks session state.
    Raises 401 if token invalid or session revoked.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    
    # Decode JWT
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = int(payload.get("sub"))
    
    # Verify user exists
    user = db.query(UserIdentity).filter(UserIdentity.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify session is still active
    token_hash = hash_token(token)
    session = db.query(AuthSession).filter(
        AuthSession.token_hash == token_hash,
        AuthSession.session_state == SessionState.ACTIVE.value
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or revoked",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


def get_current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db)
) -> AuthSession:
    """
    Dependency to get the current auth session.
    
    Returns the active session for the authenticated user.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    token_hash = hash_token(token)
    
    session = db.query(AuthSession).filter(
        AuthSession.token_hash == token_hash,
        AuthSession.session_state == SessionState.ACTIVE.value
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return session
