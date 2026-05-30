from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------- Destination Sharing ----------

class DestinationShareCreate(BaseModel):
    """Share a destination with another user."""
    user_id: str
    permission_tier: str = "view"  # view | contribute | edit | manage


class DestinationShareRead(BaseModel):
    id: str
    destination_id: str
    shared_with_id: str
    shared_with_name: str
    shared_with_email: str
    permission_tier: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Board Sharing ----------

class BoardShareCreate(BaseModel):
    """Share all of a user's destinations with another user."""
    user_id: str
    permission_tier: str = "view"


class BoardShareRead(BaseModel):
    id: str
    owner_id: str
    owner_name: str
    shared_with_id: str
    shared_with_name: str
    shared_with_email: str
    permission_tier: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- User lookup (for share picker) ----------

class ShareableUser(BaseModel):
    """Lightweight user info for the share picker dropdown."""
    id: str
    email: str
    display_name: str

    model_config = ConfigDict(from_attributes=True)
