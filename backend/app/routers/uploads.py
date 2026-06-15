from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.upload import (
    UploadBatchListResponse,
    UploadCommitRequest,
    UploadPreviewResponse,
)
from app.services.inventory_upload_parser import (
    commit_monthly_inventory,
    list_upload_batches,
    parse_monthly_inventory_preview,
)

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("/inventory-preview", response_model=UploadPreviewResponse)
async def inventory_preview(
    file: UploadFile = File(...),
    year: int | None = Form(default=None),
    month: int | None = Form(default=None),
    db: Session = Depends(get_db),
) -> UploadPreviewResponse:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="xlsx 파일만 업로드할 수 있습니다.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="업로드된 파일이 비어 있습니다.")

    try:
        return parse_monthly_inventory_preview(
            db=db,
            file_name=file.filename,
            content=content,
            year=year,
            month=month,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/inventory-commit")
def inventory_commit(
    payload: UploadCommitRequest,
    db: Session = Depends(get_db),
):
    try:
        batch = commit_monthly_inventory(db=db, payload=payload)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "batch_id": batch.id,
        "status": batch.status.value,
        "year": batch.year,
        "month": batch.month,
        "file_name": batch.file_name,
    }


@router.get("", response_model=UploadBatchListResponse)
def get_upload_batches(db: Session = Depends(get_db)) -> UploadBatchListResponse:
    return list_upload_batches(db)
