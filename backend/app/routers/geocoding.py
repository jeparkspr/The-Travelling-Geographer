from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Query

from app.services.geocoding import geocode, reverse_geocode

router = APIRouter(prefix="/geocode", tags=["geocoding"])


@router.get("")
async def geocode_query(
    q: str = Query(..., description="Address or location query"),
) -> List[Dict[str, Any]]:
    """Geocode an address or location query. Returns a list of results."""
    return await geocode(q)


@router.get("/reverse")
async def reverse_geocode_query(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
) -> Optional[Dict[str, Any]]:
    """Reverse geocode coordinates."""
    return await reverse_geocode(lat, lon)
