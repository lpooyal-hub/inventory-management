from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class MonthlyInventoryRecord(Base):
    __tablename__ = "monthly_inventory_records"
    __table_args__ = (
        UniqueConstraint("product_id", "year", "month", name="uq_monthly_inventory_product_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    item_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_current_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    closing_stock_current_month: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    closing_stock_previous_month: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_change: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inbound_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warehouse_inbound_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    return_inbound_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    outbound_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    carryout_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    return_outbound_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    adjustment_inbound_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    adjustment_outbound_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    net_change: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    product = relationship("Product")
