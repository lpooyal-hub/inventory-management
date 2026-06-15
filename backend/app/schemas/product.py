from datetime import datetime

from pydantic import BaseModel


class ProductCreate(BaseModel):
    product_code: str | None = None
    legacy_code: str | None = None
    name: str
    barcode: str | None = None
    memo: str | None = None


class ProductUpdate(BaseModel):
    product_code: str | None = None
    legacy_code: str | None = None
    name: str
    barcode: str | None = None
    memo: str | None = None


class ProductResponse(BaseModel):
    id: int
    product_code: str | None = None
    legacy_code: str | None = None
    name: str
    barcode: str | None = None
    memo: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
