import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class UploadStatus(str, enum.Enum):
    previewed = "previewed"
    committed = "committed"
    failed = "failed"
    rolled_back = "rolled_back"


class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(80), default="monthly_inventory", nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    status: Mapped[UploadStatus] = mapped_column(
        Enum(UploadStatus), default=UploadStatus.previewed, nullable=False, index=True
    )
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    matched_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unmatched_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    snapshots = relationship("InventorySnapshot", back_populates="upload_batch")
    movements = relationship("StockMovement", back_populates="upload_batch")
    errors = relationship("UploadError", back_populates="upload_batch", cascade="all, delete-orphan")


class UploadError(Base):
    __tablename__ = "upload_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    upload_batch_id: Mapped[int] = mapped_column(
        ForeignKey("upload_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    upload_batch = relationship("UploadBatch", back_populates="errors")
