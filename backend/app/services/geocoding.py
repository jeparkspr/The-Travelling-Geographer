import httpx
from typing import Optional, Dict, Any

from app.config import settings


async def geocode(query: str) -> list[Dict[str, Any]]:
    """
    Geocode an address query using Nominatim API.

    Args:
        query: Address or location query string

    Returns:
        List of dicts with lat, lon, display_name, country, region, city
    """
    try:
        async with httpx.AsyncClient() as client:
            params = {
                "q": query,
                "format": "json",
                "limit": 5,
                "addressdetails": 1,
                "accept-language": "en",
            }
            headers = {
                "User-Agent": f"{settings.APP_NAME}/1.0"
            }
            response = await client.get(
                f"{settings.NOMINATIM_URL}/search",
                params=params,
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()

            results = response.json()
            if not results:
                return []

            return [
                {
                    "lat": float(r.get("lat", 0)),
                    "lon": float(r.get("lon", 0)),
                    "display_name": r.get("display_name", ""),
                    "country": r.get("address", {}).get("country", ""),
                    "region": r.get("address", {}).get("state", r.get("address", {}).get("province", "")),
                    "city": r.get("address", {}).get("city", r.get("address", {}).get("town", "")),
                }
                for r in results
            ]
    except Exception as e:
        print(f"Geocoding error for '{query}': {e}")
        return []


async def reverse_geocode(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Reverse geocode latitude/longitude using Nominatim API.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Dict with lat, lon, display_name, country, region, city or None on failure
    """
    try:
        async with httpx.AsyncClient() as client:
            params = {
                "lat": lat,
                "lon": lon,
                "format": "json",
                "zoom": 18,
                "addressdetails": 1,
                "accept-language": "en",
            }
            headers = {
                "User-Agent": f"{settings.APP_NAME}/1.0"
            }
            response = await client.get(
                f"{settings.NOMINATIM_URL}/reverse",
                params=params,
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()

            result = response.json()
            address = result.get("address", {})

            return {
                "lat": lat,
                "lon": lon,
                "display_name": result.get("display_name", ""),
                "country": address.get("country", ""),
                "region": address.get("state", address.get("province", "")),
                "city": address.get("city", address.get("town", "")),
            }
    except Exception as e:
        print(f"Reverse geocoding error for ({lat}, {lon}): {e}")
        return None
