"""CIAM adapter for identity and access management."""
from sqlalchemy.orm import Session
from app.repositories.auth_repository import AuthRepository
from app.common.security import verify_password


class CIAMAdapter:
    """Adapter for external CIAM / Identity & Access system."""

    def __init__(self, db: Session):
        """Initialize CIAM adapter with database session."""
        self.db = db
        self.auth_repo = AuthRepository(db)

    async def authenticate_user(self, username: str, password: str) -> dict | None:
        """
        Authenticate user credentials against external CIAM.
        
        Returns user data if successful, None if authentication fails.
        This implementation uses the local database as the CIAM backend.
        """
        # Query the CIAM system (implemented as local database)
        user = self.auth_repo.get_user_by_username(username)
        
        if not user:
            return None
        
        # Verify password against stored hash
        if not verify_password(password, user.hashed_password):
            return None
        
        # Return user data on successful authentication
        return {
            "user_id": user.id,
            "username": user.username,
            "external_identity_id": user.external_identity_id,
            "status": user.status
        }

    async def validate_session(self, external_session_token: str) -> dict | None:
        """
        Validate an external session token.
        
        Returns session data if valid, None otherwise.
        This implementation validates against the local auth session store.
        """
        from app.common.security import hash_token
        
        # Hash the token to match stored format
        token_hash = hash_token(external_session_token)
        
        # Query CIAM session store (implemented as local database)
        session = self.auth_repo.get_session_by_token_hash(token_hash)
        
        if not session:
            return None
        
        # Check if session is still valid
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        if session.expires_at < now:
            return None
        
        # Return session data
        return {
            "session_id": session.id,
            "user_identity_id": session.user_identity_id,
            "active_profile_id": session.active_profile_id,
            "issued_at": session.issued_at.isoformat(),
            "expires_at": session.expires_at.isoformat()
        }
