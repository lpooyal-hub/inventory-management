from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_identity import parse_product_identity

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductResponse])
def list_products(
    query: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ProductResponse]:
    products = list(db.scalars(select(Product).order_by(Product.name)).all())
    query_text = (query or "").strip().lower()
    if not query_text:
        return products
    return [
        product
        for product in products
        if query_text
        in " ".join(filter(None, [product.name, product.product_code, product.legacy_code, product.barcode])).lower()
    ]


@router.post("", response_model=ProductResponse)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> ProductResponse:
    parsed = parse_product_identity(
        product_code=payload.product_code,
        legacy_code=payload.legacy_code,
        name=payload.name,
    )
    if not parsed.name:
        raise HTTPException(status_code=400, detail="제품명은 비어 있을 수 없습니다.")

    _validate_duplicate_product_code(db, parsed.product_code)

    product = Product(
        product_code=parsed.product_code,
        legacy_code=parsed.legacy_code,
        name=parsed.name,
        barcode=payload.barcode,
        memo=payload.memo,
    )
    db.add(product)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="중복된 신코드가 있습니다.") from exc
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
) -> ProductResponse:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")

    parsed = parse_product_identity(
        product_code=payload.product_code,
        legacy_code=payload.legacy_code,
        name=payload.name,
    )
    if not parsed.name:
        raise HTTPException(status_code=400, detail="제품명은 비어 있을 수 없습니다.")

    _validate_duplicate_product_code(db, parsed.product_code, exclude_id=product_id)

    product.product_code = parsed.product_code
    product.legacy_code = parsed.legacy_code
    product.name = parsed.name
    product.barcode = payload.barcode
    product.memo = payload.memo

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="제품 수정 중 중복된 신코드가 있습니다.") from exc
    db.refresh(product)
    return product


def _validate_duplicate_product_code(db: Session, product_code: str | None, exclude_id: int | None = None) -> None:
    if not product_code:
        return
    duplicate_product = db.scalar(select(Product).where(Product.product_code == product_code))
    if duplicate_product and duplicate_product.id != exclude_id:
        raise HTTPException(status_code=409, detail="중복된 신코드가 있습니다.")
