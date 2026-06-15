# Inventory Management

Excel inventory status migration target for a small-business web inventory system.

## Planned Structure

```text
inventory-management/
  backend/
    app/
      core/
        config.py
      db/
        base.py
        session.py
      models/
        inventory_snapshot.py
        product.py
        stock_movement.py
        upload.py
        material.py
      main.py
    requirements.txt
  frontend/
    src/
      components/
      layouts/
      pages/
      services/
      types/
```

## Excel Notes

- `2026` sheet: product inventory with product name, code, current stock, inbound quantity, total outbound quantity, and daily outbound columns.
- `입고체크` sheet: inbound check list with product name, order date, inbound date, quantity, and memo-like notes.
- `부자재 재고현황` sheets: material inventory with item name, type, current stock, standard stock, vendor, unit price, and memo.
- `제품생산 체크리스트` sheet: production/order check list with product name, order status/date, order quantity, and memo.
- `월별 입출고 통계(합계) 리스트` sheet: external monthly inventory statistics. Header is row 1 and contains the required upload columns.

The application model stores stock as movements instead of directly editing product stock.

## Proposed Import Columns

### Product Inventory

| Excel column | Suggested field | Note |
| --- | --- | --- |
| 품명 (규격/색상) | product.name | Required |
| 코드 | product.code | Optional and changeable |
| 실재고 | calculated/current stock preview | Used to create initial adjustment if confirmed |
| 입고 | inbound movement quantity | Optional |
| 총출하량 | outbound total preview | Optional |
| 1~31 | daily outbound quantity | Parsed as outbound movements when a valid month is detected |

### Material Inventory

| Excel column | Suggested field | Note |
| --- | --- | --- |
| 품명 (규격/색상) | material.name | Required; merged/blank rows inherit previous name during parsing |
| 종류 | material.material_type | Container, cap, box, pump, etc. |
| 현재고 | material.current_stock | Directly managed for materials |
| 기준재고 | material.safety_stock | Shortage threshold |
| 발주처 | material.vendor | Optional |
| 가격(VAT미포함) | material.unit_price | Optional |
| 비고 | material.memo | Optional |

## Import Flow

1. Upload `.xlsx`.
2. Detect sheet and column layout.
3. Store parsed rows in `excel_import_rows` for preview.
4. Validate duplicates before saving.
5. User confirms selected rows.
6. Persist products, stock movements, and materials.

Product codes are business identifiers and may change. The stable internal key is `products.id`, and code changes are recorded in `product_code_histories`.

## Monthly Upload Columns

Required columns in the external monthly upload file:

| Excel column | Suggested field |
| --- | --- |
| 회사명 | preview.company_name |
| 상품코드 | products.product_code |
| 공급사 | preview.supplier |
| 상품명 | products.external_code + products.name |
| 바코드 | products.barcode |
| 구분 | preview.item_type |
| 현재고 | inventory_snapshots.current_stock |
| 금월 마감재고 | inventory_snapshots.closing_stock_current_month |
| 전월 마감재고 | inventory_snapshots.closing_stock_previous_month |
| 마감재고 증감 | inventory_snapshots.stock_change |
| 입고 | inventory_snapshots.inbound_quantity |
| 창고 내 입고 | inventory_snapshots.warehouse_inbound_quantity |
| 반품 입고 | inventory_snapshots.return_inbound_quantity |
| 출고 | inventory_snapshots.outbound_quantity |
| 반출 | inventory_snapshots.carryout_quantity |
| 회송 | inventory_snapshots.return_outbound_quantity |
| 재고조정 입고 | inventory_snapshots.adjustment_inbound_quantity |
| 재고조정 반출 | inventory_snapshots.adjustment_outbound_quantity |
| 증감 | inventory_snapshots.net_change |

`상품명` can include an external code prefix, for example `DEEP200 / 딥 리페어링 헤어 마스크(200ml)`. The parser should split this into:

- `external_code`: `DEEP200`
- `name`: `딥 리페어링 헤어 마스크(200ml)`

## Matching Policy

1. Match by `product_code`.
2. Match by `barcode`.
3. Match by normalized/fuzzy product name.

Unmatched rows stay in preview and can be committed as new products after user confirmation.

## Duplicate And Rollback Policy

- Upload preview never writes inventory data.
- Commit creates an `upload_batches` row and stores all derived `inventory_snapshots` and `stock_movements` with `upload_batch_id`.
- If the same `year/month/source` already has a committed upload, the frontend must ask whether to replace it.
- Replacement should mark the old batch as `rolled_back` and remove or supersede its snapshots/movements in one transaction.
- Raw invalid rows are stored in `upload_errors.raw_data` as JSON when commit fails or validation detects row-level errors.
