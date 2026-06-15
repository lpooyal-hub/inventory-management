from datetime import date, datetime

from pydantic import BaseModel, model_validator

from app.models.stock_movement import MovementType


class StockMovementCreate(BaseModel):
    product_id: int
    movement_date: date
    movement_type: MovementType
    quantity: int
    memo: str | None = None

    @model_validator(mode="after")
    def validate_quantity(self) -> "StockMovementCreate":
        if self.movement_type == MovementType.ADJUST:
            if self.quantity < 0:
                raise ValueError("실재고 조정은 맞출 현재고 수량을 0 이상으로 입력해주세요.")
            return self

        if self.quantity <= 0:
            raise ValueError("입고/출고 수량은 1 이상이어야 합니다.")
        return self


class StockMovementResponse(BaseModel):
    id: int
    product_id: int
    movement_date: date
    movement_type: str
    quantity: int
    memo: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
