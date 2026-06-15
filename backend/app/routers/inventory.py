from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.inventory import InventoryListResponse, InventoryMonthlyResponse
from app.services.inventory_upload_parser import get_current_inventory, get_monthly_inventory

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("", response_model=InventoryListResponse)
def inventory_list(
    search: str | None = Query(default=None),
    low_stock_only: bool = Query(default=False),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> InventoryListResponse:
    return get_current_inventory(
        db=db,
        search=search,
        low_stock_only=low_stock_only,
        year=year,
        month=month,
    )


@router.get("/monthly", response_model=InventoryMonthlyResponse)
def inventory_monthly(
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
) -> InventoryMonthlyResponse:
    return get_monthly_inventory(db, year=year, month=month)
