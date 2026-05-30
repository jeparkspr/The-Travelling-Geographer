from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, union_all, text, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.destination import Destination
from app.models.user import User
from app.models.journal import JournalEntry
from app.services.auth import get_current_user
from app.services.permissions import build_accessible_destinations_query

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def full_text_search(
    q: str = Query(..., description="Search query"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Full-text search across destinations and journal entries. Scoped to accessible destinations."""
    if not q:
        return []

    access_filter = build_accessible_destinations_query(current_user)
    results = []

    # Search destinations
    search_vector = func.to_tsvector("english", func.concat_ws(" ", Destination.name, Destination.description))
    search_query = func.plainto_tsquery("english", q)
    relevance = func.ts_rank(search_vector, search_query)

    dest_result = await db.execute(
        select(
            Destination.id,
            Destination.name,
            Destination.status,
            Destination.country,
            Destination.city,
            relevance.label("relevance"),
            text("'destination' as result_type"),
        )
        .where(and_(search_vector.match(search_query), access_filter))
        .order_by(relevance.desc())
        .limit(20)
    )

    for row in dest_result:
        results.append({
            "id": row.id,
            "title": row.name,
            "type": "destination",
            "status": row.status,
            "location": f"{row.city}, {row.country}" if row.city else row.country,
            "relevance": float(row.relevance),
        })

    # Search journal entries (only in accessible destinations)
    journal_search_vector = func.to_tsvector("english", func.concat_ws(" ", JournalEntry.title, JournalEntry.body))
    journal_relevance = func.ts_rank(journal_search_vector, search_query)

    journal_result = await db.execute(
        select(
            JournalEntry.id,
            JournalEntry.title,
            JournalEntry.destination_id,
            Destination.name.label("destination_name"),
            journal_relevance.label("relevance"),
            text("'journal' as result_type"),
        )
        .join(Destination, JournalEntry.destination_id == Destination.id)
        .where(and_(journal_search_vector.match(search_query), access_filter))
        .order_by(journal_relevance.desc())
        .limit(20)
    )

    for row in journal_result:
        results.append({
            "id": row.id,
            "title": row.title,
            "type": "journal_entry",
            "destination": row.destination_name,
            "destination_id": row.destination_id,
            "relevance": float(row.relevance),
        })

    # Sort by relevance
    results.sort(key=lambda x: x["relevance"], reverse=True)

    return results[:50]
