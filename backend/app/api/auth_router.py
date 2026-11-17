from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.service import AuthService
from app.auth.schemas import LoginRequest, LoginResponse, UserResponse
from app.auth.deps import get_current_user
from app.auth.models import AppUser
from app.core.errors import AuthenticationError, RateLimitError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request,
    payload: LoginRequest,
    db: Session = Depends(get_db)
):
    try:
        service = AuthService(db)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        token, user = service.login(payload.email, payload.password, ip_address, user_agent)

        return LoginResponse(
            access_token=token,
            token_type="Bearer",
            user_id=user.id,
            email=user.email,
            is_colleague=user.is_colleague,
        )
    except RateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
def logout(
    credentials: str = Depends(lambda req: req.headers.get("authorization", "").replace("Bearer ", "")),
    db: Session = Depends(get_db)
):
    service = AuthService(db)
    service.logout(credentials)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: AppUser = Depends(get_current_user)
):
    return UserResponse.model_validate(current_user)
