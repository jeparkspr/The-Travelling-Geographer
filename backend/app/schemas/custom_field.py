from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class CustomFieldCreate(BaseModel):
    field_name: str
    field_key: str
    field_type: str
    options: Optional[List[str]] = None
    sort_order: int = 0


class CustomFieldUpdate(BaseModel):
    field_name: Optional[str] = None
    field_key: Optional[str] = None
    field_type: Optional[str] = None
    options: Optional[List[str]] = None
    sort_order: Optional[int] = None


class CustomFieldRead(BaseModel):
    id: str
    field_name: str
    field_key: str
    field_type: str
    options: Optional[List[str]] = None
    sort_order: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
