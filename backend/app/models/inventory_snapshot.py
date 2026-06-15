from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "year",
            "month",
            "upload_batch_id",
            name="uq_inventory_snapshot_product_month_batch",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    current_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    closing_stock_current_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    closing_stock_previous_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stock_change: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    inbound_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warehouse_inbound_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    return_inbound_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    outbound_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    carryout_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    return_outbound_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    adjustment_inbound_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    adjustment_outbound_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    net_change: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    upload_batch_id: Mapped[int] = mapped_column(
        ForeignKey("upload_batches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product = relationship("Product", back_populates="snapshots")
    upload_batch = relationship("UploadBatch", back_populates="snapshots")
