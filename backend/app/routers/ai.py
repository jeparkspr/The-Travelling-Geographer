import json
import re
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.app_settings import AppSetting, DEFAULT_AI_PROMPT

router = APIRouter(prefix="/ai", tags=["ai"])

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
AVAILABLE_MODELS = ["gemini-2.5-flash", "gemini-flash-latest"]


# ---- Schemas ----------------------------------------------------------------

class AISettingsRead(BaseModel):
    gemini_api_key_set: bool
    ai_prompt_template: str
    gemini_model: str


class AISettingsUpdate(BaseModel):
    gemini_api_key: Optional[str] = None
    ai_prompt_template: Optional[str] = None
    gemini_model: Optional[str] = None


class AIPopulateRequest(BaseModel):
    latitude: float
    longitude: float
    location_name: Optional[str] = None
    country: Optional[str] = None


class AIPopulateResponse(BaseModel):
    name: str
    country: str
    region: Optional[str] = None
    city: Optional[str] = None
    description: str
    tags: list[str] = []
    best_season: list[str] = []


class AITestResponse(BaseModel):
    success: bool
    message: str


# ---- Helper: get/set setting ------------------------------------------------

async def get_setting(db: AsyncSession, key: str) -> Optional[str]:
    result = await db.execute(
        select(AppSetting).where(AppSetting.key == key)
    )
    setting = result.scalar_one_or_none()
    return setting.value if setting else None


async def set_setting(db: AsyncSession, key: str, value: str) -> None:
    result = await db.execute(
        select(AppSetting).where(AppSetting.key == key)
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        setting = AppSetting(key=key, value=value)
        db.add(setting)


# ---- Endpoints --------------------------------------------------------------

@router.get("/settings", response_model=AISettingsRead)
async def get_ai_settings(db: AsyncSession = Depends(get_db)):
    """Get AI settings (API key is masked)."""
    api_key = await get_setting(db, "gemini_api_key")
    prompt = await get_setting(db, "ai_prompt_template")
    model = await get_setting(db, "gemini_model")

    return AISettingsRead(
        gemini_api_key_set=bool(api_key and api_key.strip()),
        ai_prompt_template=prompt or DEFAULT_AI_PROMPT,
        gemini_model=model or DEFAULT_GEMINI_MODEL,
    )


@router.put("/settings")
async def update_ai_settings(
    data: AISettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update AI settings."""
    if data.gemini_api_key is not None:
        await set_setting(db, "gemini_api_key", data.gemini_api_key.strip())

    if data.ai_prompt_template is not None:
        await set_setting(db, "ai_prompt_template", data.ai_prompt_template.strip())

    if data.gemini_model is not None:
        model = data.gemini_model.strip()
        if model in AVAILABLE_MODELS:
            await set_setting(db, "gemini_model", model)

    await db.commit()
    return {"status": "ok"}


@router.post("/test-connection", response_model=AITestResponse)
async def test_gemini_connection(db: AsyncSession = Depends(get_db)):
    """Test the Gemini API connection with the stored key."""
    api_key = await get_setting(db, "gemini_api_key")
    if not api_key:
        return AITestResponse(success=False, message="No API key configured")

    model = await get_setting(db, "gemini_model") or DEFAULT_GEMINI_MODEL
    api_url = f"{GEMINI_API_BASE}/{model}:generateContent"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                api_url,
                headers={"X-goog-api-key": api_key},
                json={
                    "contents": [{"parts": [{"text": "Reply with: ok"}]}],
                },
            )
        if response.status_code == 200:
            return AITestResponse(success=True, message="Connection successful")
        elif response.status_code == 400:
            return AITestResponse(success=False, message="Invalid request — check API key")
        elif response.status_code == 403:
            return AITestResponse(success=False, message="API key is invalid or disabled")
        else:
            return AITestResponse(
                success=False,
                message=f"Gemini returned status {response.status_code}",
            )
    except httpx.TimeoutException:
        return AITestResponse(success=False, message="Connection timed out")
    except Exception as exc:
        return AITestResponse(success=False, message=str(exc))


@router.post("/populate", response_model=AIPopulateResponse)
async def ai_populate(
    req: AIPopulateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Call Gemini to populate destination fields from coordinates."""
    api_key = await get_setting(db, "gemini_api_key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gemini API key not configured. Set it in Settings > AI.",
        )

    # Determine which model to use
    model = await get_setting(db, "gemini_model") or DEFAULT_GEMINI_MODEL
    api_url = f"{GEMINI_API_BASE}/{model}:generateContent"

    # Build the prompt from the template
    prompt_template = await get_setting(db, "ai_prompt_template") or DEFAULT_AI_PROMPT
    prompt = prompt_template.format(
        location_name=req.location_name or "this location",
        country=req.country or "Unknown",
        latitude=req.latitude,
        longitude=req.longitude,
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                api_url,
                headers={"X-goog-api-key": api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 8192,
                    },
                },
            )

        if response.status_code != 200:
            detail = f"Gemini API error (HTTP {response.status_code})"
            try:
                err = response.json()
                detail = err.get("error", {}).get("message", detail)
            except Exception:
                detail += f": {response.text[:300]}"
            logger.error("Gemini API non-200: status=%s body=%s", response.status_code, response.text[:500])
            raise HTTPException(status_code=502, detail=detail)

        # Extract the text response
        data = response.json()
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        if not text:
            raise HTTPException(status_code=502, detail="Empty response from Gemini")

        # Check if the response was truncated
        finish_reason = (
            data.get("candidates", [{}])[0]
            .get("finishReason", "")
        )
        if finish_reason == "MAX_TOKENS":
            logger.warning("Gemini response truncated (MAX_TOKENS). Raw length: %d", len(text))
            raise HTTPException(
                status_code=502,
                detail="AI response was truncated. Please try again — this is usually intermittent.",
            )

        # Parse JSON from the response (handle markdown code blocks)
        json_text = text.strip()
        if json_text.startswith("```"):
            # Remove markdown code fences
            lines = json_text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            json_text = "\n".join(lines)

        # Fix unescaped newlines inside JSON string values —
        # Gemini often puts literal newlines in the description field
        # which breaks json.loads. Replace raw newlines inside strings
        # with escaped \\n.
        def _fix_json_newlines(s: str) -> str:
            """Escape literal newlines that appear inside JSON string values."""
            # Replace actual newline chars inside quoted strings
            # by processing char-by-char
            out = []
            in_string = False
            escape = False
            for ch in s:
                if escape:
                    out.append(ch)
                    escape = False
                    continue
                if ch == '\\':
                    out.append(ch)
                    escape = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    out.append(ch)
                    continue
                if in_string and ch == '\n':
                    out.append('\\n')
                    continue
                if in_string and ch == '\r':
                    continue  # drop carriage returns
                out.append(ch)
            return ''.join(out)

        json_text = _fix_json_newlines(json_text)

        try:
            result = json.loads(json_text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Gemini JSON response: %s", json_text[:1000])
            raise HTTPException(
                status_code=502,
                detail=f"Could not parse AI response as JSON: {str(exc)}. Raw (first 300 chars): {json_text[:300]}",
            )

        # Validate and sanitize
        tags = result.get("tags", [])[:3]  # Max 3 tags
        valid_seasons = {"spring", "summer", "fall", "winter"}
        best_season = [s.title() for s in result.get("best_season", []) if s.lower() in valid_seasons][:4]

        return AIPopulateResponse(
            name=result.get("name", req.location_name or ""),
            country=result.get("country", req.country or ""),
            region=result.get("region"),
            city=result.get("city"),
            description=result.get("description", ""),
            tags=tags,
            best_season=best_season,
        )

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not parse AI response as JSON: {str(exc)}",
        )
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Gemini API request timed out")
    except Exception as exc:
        logger.exception("AI populate failed unexpectedly")
        raise HTTPException(status_code=500, detail=f"AI populate failed: {str(exc)}")
