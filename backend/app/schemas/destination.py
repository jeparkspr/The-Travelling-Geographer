from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from app.schemas.media import MediaRead


class LinkCreate(BaseModel):
    url: str
    title: Optional[str] = None
    sort_order: int = 0


class LinkUpdate(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    sort_order: Optional[int] = None


class LinkRead(BaseModel):
    id: str
    destination_id: str
    url: str
    title: Optional[str] = None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class DestinationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "researching"
    country: str
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: float
    longitude: float
    address: Optional[str] = None
    rating: Optional[int] = None
    cost_estimate: Optional[Decimal] = None
    cost_actual: Optional[Decimal] = None
    priority: Optional[str] = None
    best_season: Optional[List[str]] = None
    tags: List[str] = []
    custom_field_values: dict = {}
    date_researched: Optional[datetime] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    visited_start_date: Optional[date] = None
    visited_end_date: Optional[date] = None


class DestinationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    rating: Optional[int] = None
    cost_estimate: Optional[Decimal] = None
    cost_actual: Optional[Decimal] = None
    priority: Optional[str] = None
    cover_media_id: Optional[str] = None
    best_season: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    custom_field_values: Optional[dict] = None
    date_researched: Optional[datetime] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    visited_start_date: Optional[date] = None
    visited_end_date: Optional[date] = None


class DestinationRead(BaseModel):
    id: str
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    permission_tier: Optional[str] = None
    name: str
    description: Optional[str] = None
    status: str
    country: str
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: float
    longitude: float
    address: Optional[str] = None
    rating: Optional[int] = None
    cost_estimate: Optional[Decimal] = None
    cost_actual: Optional[Decimal] = None
    priority: Optional[str] = None
    best_season: Optional[List[str]] = None
    tags: List[str]
    custom_field_values: dict
    date_added: datetime
    date_researched: Optional[datetime] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    visited_start_date: Optional[date] = None
    visited_end_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    cover_media_id: Optional[str] = None
    links: List[LinkRead] = []
    media: List[MediaRead] = []
    media_count: int = 0
    journal_entry_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DestinationListRead(BaseModel):
    id: str
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    permission_tier: Optional[str] = None
    name: str
    status: str
    country: str
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: float
    longitude: float
    rating: Optional[int] = None
    priority: Optional[str] = None
    best_season: Optional[List[str]] = None
    tags: List[str]
    date_added: datetime
    updated_at: datetime
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    cover_media_id: Optional[str] = None
    media_count: int = 0
    journal_entry_count: int = 0
    thumbnail_url: Optional[str] = None
    shared_with_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DestinationClip(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
