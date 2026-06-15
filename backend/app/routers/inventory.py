from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reports import InventorySummaryResponse
from app.services.mvp_inventory import build_inventory_summary

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/summary", response_model=InventorySummaryResponse)
def inventory_summary(db: Session = Depends(get_db)) -> InventorySummaryResponse:
    return build_inventory_summary(db)
