from pydantic import BaseModel


class InventorySummaryItem(BaseModel):
    product_id: int
    product_code: str | None = None
    legacy_code: str | None = None
    name: str
    barcode: str | None = None
    current_stock: int
    current_month_outbound: int
    average_monthly_outbound_last_3_months: float
    remaining_expected_outbound_this_month: float
    projected_stock_after_expected_outbound: float
    shortage_status: str
    production_order_required: bool


class InventorySummaryResponse(BaseModel):
    items: list[InventorySummaryItem]


class MonthlyOutboundItem(BaseModel):
    product_id: int
    product_code: str | None = None
    legacy_code: str | None = None
    name: str
    outbound_quantity: int


class MonthlyOutboundResponse(BaseModel):
    year: int
    month: int
    items: list[MonthlyOutboundItem]


class MonthlyTrendMonth(BaseModel):
    year: int
    month: int
    label: str
    total_outbound_quantity: int


class MonthlyTrendProductRow(BaseModel):
    product_id: int
    product_code: str | None = None
    legacy_code: str | None = None
    name: str
    monthly_quantities: list[int]
    total_outbound_quantity: int
    average_outbound_quantity: float


class MonthlyTrendResponse(BaseModel):
    anchor_year: int
    anchor_month: int
    months: list[MonthlyTrendMonth]
    items: list[MonthlyTrendProductRow]


class ShortageItem(BaseModel):
    product_id: int
    product_code: str | None = None
    legacy_code: str | None = None
    name: str
    current_stock: int
    current_month_outbound: int
    average_monthly_outbound_last_3_months: float
    remaining_expected_outbound_this_month: float
    projected_stock_after_expected_outbound: float
    shortage_status: str
    production_order_required: bool


class ShortageResponse(BaseModel):
    items: list[ShortageItem]
