from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_code: Mapped[str | None] = mapped_column(
        String(80), nullable=True, unique=True, index=True
    )
    external_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    barcode: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    movements = relationship(
        "StockMovement", back_populates="product", cascade="all, delete-orphan"
    )
    snapshots = relationship(
        "InventorySnapshot", back_populates="product", cascade="all, delete-orphan"
    )
    code_histories = relationship(
        "ProductCodeHistory", back_populates="product", cascade="all, delete-orphan"
    )


class ProductCodeHistory(Base):
    __tablename__ = "product_code_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    previous_product_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    new_product_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    changed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product = relationship("Product", back_populates="code_histories")
