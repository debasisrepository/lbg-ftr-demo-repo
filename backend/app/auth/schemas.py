from pydantic import BaseModel, EmailStr, ConfigDict


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user_id: int
    email: str
    is_colleague: bool


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_active: bool
    is_colleague: bool
    customer_reference: str | None = None
    brand: str | None = None
