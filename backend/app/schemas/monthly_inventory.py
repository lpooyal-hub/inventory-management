from datetime import date, datetime

from pydantic import BaseModel


class MonthlyInventoryRecordResponse(BaseModel):
    id: int
    product_id: int
    product_code: str | None = None
    legacy_code: str | None = None
    name: str
    barcode: str | None = None
    year: int
    month: int
    file_name: str | None = None
    company_name: str | None = None
    item_type: str | None = None
    file_current_stock: int
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
    note: str | None = None
    updated_at: datetime


class MonthlyInventoryRecordUpdate(BaseModel):
    file_current_stock: int
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
    note: str | None = None


class MonthlyUploadPreviewRow(BaseModel):
    row_number: int
    product_id: int | None = None
    product_code: str | None = None
    legacy_code: str | None = None
    name: str
    barcode: str | None = None
    company_name: str | None = None
    item_type: str | None = None
    matched: bool
    system_current_stock: int = 0
    current_stock_diff: int = 0
    file_current_stock: int
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
    existing_record_id: int | None = None
    existing_record_diff: bool = False
    selected: bool = True
    apply_stock_adjustment: bool = False
    note: str | None = None


class MonthlyUploadPreviewResponse(BaseModel):
    file_name: str
    year: int
    month: int
    total_rows: int
    matched_rows: int
    unmatched_rows: int
    rows: list[MonthlyUploadPreviewRow]


class MonthlyUploadCommitRequest(BaseModel):
    file_name: str
    year: int
    month: int
    movement_date: date | None = None
    rows: list[MonthlyUploadPreviewRow]


class MonthlyUploadCommitResponse(BaseModel):
    total_rows: int
    saved_rows: int
    adjusted_rows: int
    unmatched_rows: int


class MonthlyInventoryListResponse(BaseModel):
    items: list[MonthlyInventoryRecordResponse]


class MonthlyResetResponse(BaseModel):
    year: int
    month: int
    deleted_records: int
    deleted_movements: int
