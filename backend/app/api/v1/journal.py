"""Trade Journal API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.entities import TradeJournalEntry, utcnow
from app.schemas.entities import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryRead,
    PaginatedResponse,
)

router = APIRouter(prefix="/journal", tags=["Trade Journal"])


@router.get("", response_model=PaginatedResponse[JournalEntryRead], summary="List Journal Entries")
def list_journal_entries(
    symbol: Optional[str] = Query(None, description="Optional symbol filter"),
    trade_id: Optional[int] = Query(None, description="Filter by related paper trade ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[JournalEntryRead]:
    """Retrieve paginated trade journal notes and lessons learned."""
    query = db.query(TradeJournalEntry)
    if symbol:
        query = query.filter(func.upper(TradeJournalEntry.symbol) == symbol.strip().upper())
    if trade_id is not None:
        query = query.filter(TradeJournalEntry.trade_id == trade_id)

    total = query.count()
    items = query.order_by(TradeJournalEntry.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=JournalEntryRead, status_code=status.HTTP_201_CREATED, summary="Create Journal Entry")
def create_journal_entry(
    payload: JournalEntryCreate,
    db: Session = Depends(get_db),
) -> JournalEntryRead:
    """Create a new trade reflection or session journal entry."""
    entry = TradeJournalEntry(
        trade_id=payload.trade_id,
        symbol=payload.symbol.strip().upper() if payload.symbol else None,
        title=payload.title.strip(),
        notes=payload.notes.strip(),
        lessons_learned=payload.lessons_learned.strip() if payload.lessons_learned else None,
        tags=payload.tags.strip() if payload.tags else "",
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{entry_id}", response_model=JournalEntryRead, summary="Get Journal Entry by ID")
def get_journal_entry(
    entry_id: int,
    db: Session = Depends(get_db),
) -> JournalEntryRead:
    """Get single journal entry by ID."""
    entry = db.query(TradeJournalEntry).filter(TradeJournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry with ID {entry_id} not found.",
        )
    return entry


@router.put("/{entry_id}", response_model=JournalEntryRead, summary="Update Journal Entry")
def update_journal_entry(
    entry_id: int,
    payload: JournalEntryUpdate,
    db: Session = Depends(get_db),
) -> JournalEntryRead:
    """Update journal notes, title, or lessons learned."""
    entry = db.query(TradeJournalEntry).filter(TradeJournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry with ID {entry_id} not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(entry, field, val)

    entry.updated_at = utcnow()
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Journal Entry")
def delete_journal_entry(
    entry_id: int,
    db: Session = Depends(get_db),
):
    """Delete a journal entry by ID."""
    entry = db.query(TradeJournalEntry).filter(TradeJournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry with ID {entry_id} not found.",
        )
    db.delete(entry)
    db.commit()
    return None
