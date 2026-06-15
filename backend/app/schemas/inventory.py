from pydantic import BaseModel


class InventoryListItem(BaseModel):
    product_id: int
    product_code: str | None = None
    external_code: str | None = None
    barcode: str | None = None
    name: str
    category: str | None = None
    current_stock: int
    closing_stock_current_month: int
    closing_stock_previous_month: int
    inbound_quantity: int
    outbound_quantity: int
    net_change: int
    snapshot_year: int
    snapshot_month: int
    is_low_stock: bool
    latest_upload_batch_id: int


class InventoryListResponse(BaseModel):
    items: list[InventoryListItem]


class InventoryMonthlyItem(BaseModel):
    product_id: int
    product_code: str | None = None
    external_code: str | None = None
    barcode: str | None = None
    name: str
    current_stock: int
    closing_stock_current_month: int
    closing_stock_previous_month: int
    stock_change: int
    inbound_quantity: int
    warehouse_inbound_quantity: int
    return_inbound_quantity: int
    outbound_quantity: int
    carryout_quantity: int
    return_outbound_quantity: int
    adjustment_inbound_quantity: int
    adjustment_outbound_quantity: int
    net_change: int
    upload_batch_id: int


class InventoryMonthlyResponse(BaseModel):
    year: int
    month: int
    items: list[InventoryMonthlyItem]
