from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, EmailStr


# ---------- Auth request / response ----------

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    display_name: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class LoginResponse(BaseModel):
    success: bool
    detail: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------- Setup wizard ----------

class SetupStatus(BaseModel):
    is_setup_complete: bool
    has_users: bool


class SetupRequest(BaseModel):
    email: str
    display_name: str
    password: str


# ---------- User CRUD (admin) ----------

class UserCreate(BaseModel):
    email: str
    display_name: str
    password: str
    role_names: List[str] = ["User"]
    is_active: bool = True
    is_approved: bool = True


class UserUpdate(BaseModel):
    email: Optional[str] = None
    display_name: Optional[str] = None
    password: Optional[str] = None
    role_names: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_approved: Optional[bool] = None


class RoleRead(BaseModel):
    id: str
    name: str
    default_tier: str
    is_system: bool
    can_manage_users: bool
    can_manage_settings: bool

    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    id: str
    email: str
    display_name: str
    is_active: bool
    is_approved: bool
    totp_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    roles: List[RoleRead] = []

    model_config = ConfigDict(from_attributes=True)


class CurrentUser(BaseModel):
    """Lightweight payload returned with /auth/me."""
    id: str
    email: str
    display_name: str
    is_active: bool
    roles: List[str] = []
    permissions: dict = {}  # e.g. {"can_manage_users": true, ...}
