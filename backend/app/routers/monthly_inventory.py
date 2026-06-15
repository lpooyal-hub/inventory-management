from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.monthly_inventory import (
    MonthlyInventoryListResponse,
    MonthlyResetResponse,
    MonthlyInventoryRecordResponse,
    MonthlyInventoryRecordUpdate,
    MonthlyUploadCommitRequest,
    MonthlyUploadCommitResponse,
    MonthlyUploadPreviewResponse,
)
from app.services.monthly_upload import (
    build_monthly_upload_preview,
    commit_monthly_upload,
    list_monthly_records,
    reset_monthly_records,
    update_monthly_record,
)

router = APIRouter(tags=["monthly-inventory"])


@router.post("/api/uploads/monthly-preview", response_model=MonthlyUploadPreviewResponse)
async def monthly_preview(
    year: int = Query(...),
    month: int = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> MonthlyUploadPreviewResponse:
    payload = await file.read()
    try:
        return build_monthly_upload_preview(db, file.filename or "upload.xlsx", year, month, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/uploads/monthly-commit", response_model=MonthlyUploadCommitResponse)
def monthly_commit(
    payload: MonthlyUploadCommitRequest,
    db: Session = Depends(get_db),
) -> MonthlyUploadCommitResponse:
    return commit_monthly_upload(db, payload)


@router.get("/api/monthly-records", response_model=MonthlyInventoryListResponse)
def monthly_records(
    year: int = Query(...),
    month: int = Query(...),
    query: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> MonthlyInventoryListResponse:
    return MonthlyInventoryListResponse(items=list_monthly_records(db, year, month, query))


@router.put("/api/monthly-records/{record_id}", response_model=MonthlyInventoryRecordResponse)
def monthly_record_update(
    record_id: int,
    payload: MonthlyInventoryRecordUpdate,
    db: Session = Depends(get_db),
) -> MonthlyInventoryRecordResponse:
    try:
        return update_monthly_record(db, record_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/api/monthly-records", response_model=MonthlyResetResponse)
def monthly_records_reset(
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
) -> MonthlyResetResponse:
    return reset_monthly_records(db, year, month)
