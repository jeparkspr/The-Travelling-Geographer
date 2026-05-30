from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class JournalEntryCreate(BaseModel):
    title: str
    body: Optional[str] = None
    entry_date: Optional[date] = None
    rating: Optional[int] = None


class JournalEntryUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    entry_date: Optional[date] = None
    rating: Optional[int] = None


class JournalEntryRead(BaseModel):
    id: str
    destination_id: str
    title: str
    body: Optional[str] = None
    entry_date: Optional[date] = None
    rating: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    media: list = []

    model_config = ConfigDict(from_attributes=True)


class JournalEntryWithDestination(JournalEntryRead):
    destination_name: str
    destination_status: str
