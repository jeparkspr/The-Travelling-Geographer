from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.custom_field import CustomFieldDefinition
from app.models.destination import Destination
from app.schemas.custom_field import CustomFieldCreate, CustomFieldUpdate, CustomFieldRead

router = APIRouter(prefix="/custom-fields", tags=["custom_fields"])


@router.get("", response_model=List[CustomFieldRead])
async def list_custom_fields(
    db: AsyncSession = Depends(get_db),
) -> List[CustomFieldRead]:
    """List all custom field definitions."""
    result = await db.execute(
        select(CustomFieldDefinition).order_by(CustomFieldDefinition.sort_order)
    )
    fields = result.scalars().all()
    return [CustomFieldRead.model_validate(f) for f in fields]


@router.post("", response_model=CustomFieldRead, status_code=status.HTTP_201_CREATED)
async def create_custom_field(
    field_data: CustomFieldCreate,
    db: AsyncSession = Depends(get_db),
) -> CustomFieldRead:
    """Create a new custom field definition."""
    # Check if field_key already exists
    result = await db.execute(
        select(CustomFieldDefinition).where(
            CustomFieldDefinition.field_key == field_data.field_key
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field key already exists"
        )

    field = CustomFieldDefinition(
        field_name=field_data.field_name,
        field_key=field_data.field_key,
        field_type=field_data.field_type,
        options=field_data.options,
        sort_order=field_data.sort_order,
    )

    db.add(field)
    await db.commit()
    await db.refresh(field)

    return CustomFieldRead.model_validate(field)


@router.put("/{field_id}", response_model=CustomFieldRead)
async def update_custom_field(
    field_id: str,
    field_data: CustomFieldUpdate,
    db: AsyncSession = Depends(get_db),
) -> CustomFieldRead:
    """Update a custom field definition."""
    result = await db.execute(
        select(CustomFieldDefinition).where(CustomFieldDefinition.id == field_id)
    )
    field = result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    update_data = field_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(field, key, value)

    await db.commit()
    await db.refresh(field)

    return CustomFieldRead.model_validate(field)


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_field(
    field_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom field definition and clean up values from destinations."""
    result = await db.execute(
        select(CustomFieldDefinition).where(CustomFieldDefinition.id == field_id)
    )
    field = result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    # Get all destinations with this field
    result = await db.execute(select(Destination))
    destinations = result.scalars().all()

    # Remove the field key from custom_field_values
    for dest in destinations:
        if field.field_key in dest.custom_field_values:
            del dest.custom_field_values[field.field_key]
            dest.custom_field_values = dest.custom_field_values  # Trigger update

    await db.delete(field)
    await db.commit()
