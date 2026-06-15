from pydantic import BaseModel, Field


class UploadPreviewProduct(BaseModel):
    id: int | None = None
    product_code: str | None = None
    external_code: str | None = None
    barcode: str | None = None
    name: str | None = None


class UploadPreviewRow(BaseModel):
    row_number: int
    company_name: str | None = None
    product_code: str | None = None
    supplier: str | None = None
    external_code: str | None = None
    product_name: str
    barcode: str | None = None
    item_type: str | None = None
    current_stock: int = 0
    closing_stock_current_month: int = 0
    closing_stock_previous_month: int = 0
    stock_change: int = 0
    inbound_quantity: int = 0
    warehouse_inbound_quantity: int = 0
    return_inbound_quantity: int = 0
    outbound_quantity: int = 0
    carryout_quantity: int = 0
    return_outbound_quantity: int = 0
    adjustment_inbound_quantity: int = 0
    adjustment_outbound_quantity: int = 0
    net_change: int = 0
    matched: bool
    match_method: str | None = None
    matched_product: UploadPreviewProduct | None = None
    is_duplicate: bool = False
    duplicate_reason: str | None = None
    raw_data: dict


class UploadPreviewError(BaseModel):
    row_number: int
    error_message: str
    raw_data: dict = Field(default_factory=dict)


class UploadPreviewSummary(BaseModel):
    file_name: str
    year: int
    month: int
    source: str
    total_rows: int
    preview_rows: int
    matched_rows: int
    unmatched_rows: int
    duplicate_rows: int
    error_rows: int
    missing_columns: list[str]
    existing_committed_batches: int
    should_confirm_replace: bool


class UploadPreviewResponse(BaseModel):
    summary: UploadPreviewSummary
    rows: list[UploadPreviewRow]
    errors: list[UploadPreviewError]


class UploadCommitRequest(BaseModel):
    file_name: str
    year: int
    month: int
    source: str = "monthly_inventory"
    replace_existing: bool = False
    rows: list[UploadPreviewRow]
    errors: list[UploadPreviewError] = Field(default_factory=list)


class UploadBatchItem(BaseModel):
    id: int
    file_name: str
    year: int
    month: int
    source: str
    uploaded_at: str
    status: str
    total_rows: int
    matched_rows: int
    unmatched_rows: int
    error_rows: int


class UploadBatchListResponse(BaseModel):
    items: list[UploadBatchItem]
