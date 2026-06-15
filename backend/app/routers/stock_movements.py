from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product
from app.models.stock_movement import MovementType, StockMovement
from app.schemas.movement import StockMovementCreate, StockMovementResponse
from app.services.mvp_inventory import calculate_product_metrics_map

router = APIRouter(prefix="/api/stock-movements", tags=["stock-movements"])


@router.post("", response_model=StockMovementResponse)
def create_stock_movement(
    payload: StockMovementCreate, db: Session = Depends(get_db)
) -> StockMovementResponse:
    product = db.scalar(select(Product).where(Product.id == payload.product_id))
    if not product:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")

    quantity = payload.quantity
    if payload.movement_type == MovementType.ADJUST:
        current_stock = calculate_product_metrics_map(db).get(payload.product_id)
        current_quantity = current_stock.current_stock if current_stock else 0
        quantity = payload.quantity - current_quantity
        if quantity == 0:
            raise HTTPException(
                status_code=400,
                detail=f"이미 현재고가 {payload.quantity}개입니다.",
            )

    movement = StockMovement(
        product_id=payload.product_id,
        movement_date=payload.movement_date,
        movement_type=payload.movement_type.value,
        quantity=quantity,
        memo=payload.memo,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement
