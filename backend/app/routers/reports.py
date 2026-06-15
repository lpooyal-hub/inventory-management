from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reports import MonthlyOutboundResponse, MonthlyTrendResponse, ShortageResponse
from app.services.mvp_inventory import (
    build_monthly_outbound_report,
    build_monthly_outbound_trend,
    build_shortage_report,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/monthly-outbound", response_model=MonthlyOutboundResponse)
def monthly_outbound(
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
) -> MonthlyOutboundResponse:
    return build_monthly_outbound_report(db, year=year, month=month)


@router.get("/monthly-outbound-trend", response_model=MonthlyTrendResponse)
def monthly_outbound_trend(
    year: int,
    month: int,
    months: int = 12,
    db: Session = Depends(get_db),
) -> MonthlyTrendResponse:
    return build_monthly_outbound_trend(db, year=year, month=month, months=months)


@router.get("/shortage", response_model=ShortageResponse)
def shortage_report(db: Session = Depends(get_db)) -> ShortageResponse:
    return build_shortage_report(db)
