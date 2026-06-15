from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.monthly_inventory_record import MonthlyInventoryRecord
from app.models.product import Product
from app.models.stock_movement import StockMovement
from app.schemas.monthly_inventory import (
    MonthlyInventoryRecordResponse,
    MonthlyInventoryRecordUpdate,
    MonthlyResetResponse,
    MonthlyUploadCommitRequest,
    MonthlyUploadCommitResponse,
    MonthlyUploadPreviewResponse,
    MonthlyUploadPreviewRow,
)
from app.services.mvp_inventory import calculate_product_metrics_map
from app.services.product_identity import parse_product_identity


SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REQUIRED_COLUMNS = {
    "회사명",
    "상품코드",
    "상품명",
    "바코드",
    "구분",
    "현재고",
    "금월 마감재고",
    "전월 마감재고",
    "마감재고 증감",
    "입고",
    "창고 내 입고",
    "반품 입고",
    "출고",
    "반출",
    "회송",
    "재고조정 입고",
    "재고조정 반출",
    "증감",
}
MONTHLY_OUTBOUND_MEMO_PREFIX = "MONTHLY_UPLOAD_OUTBOUND"
MONTHLY_ADJUST_MEMO_PREFIX = "MONTHLY_UPLOAD_ADJUST"


@dataclass
class ParsedUploadRow:
    row_number: int
    company_name: str | None
    product_code: str | None
    legacy_code: str | None
    name: str
    barcode: str | None
    item_type: str | None
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


def build_monthly_upload_preview(
    db: Session,
    file_name: str,
    year: int,
    month: int,
    payload: bytes,
) -> MonthlyUploadPreviewResponse:
    parsed_rows = _parse_monthly_upload_bytes(payload)
    metrics_map = calculate_product_metrics_map(db)
    existing_records = {
        record.product_id: record
        for record in db.scalars(
            select(MonthlyInventoryRecord).where(
                MonthlyInventoryRecord.year == year,
                MonthlyInventoryRecord.month == month,
            )
        ).all()
    }

    rows: list[MonthlyUploadPreviewRow] = []
    matched_rows = 0
    unmatched_rows = 0

    for row in parsed_rows:
        product = _match_product(db, row)
        metrics = metrics_map.get(product.id) if product else None
        existing_record = existing_records.get(product.id) if product else None
        matched = product is not None
        if matched:
            matched_rows += 1
        else:
            unmatched_rows += 1

        rows.append(
            MonthlyUploadPreviewRow(
                row_number=row.row_number,
                product_id=product.id if product else None,
                product_code=row.product_code,
                legacy_code=row.legacy_code,
                name=row.name,
                barcode=row.barcode,
                company_name=row.company_name,
                item_type=row.item_type,
                matched=matched,
                system_current_stock=metrics.current_stock if metrics else 0,
                current_stock_diff=row.file_current_stock - (metrics.current_stock if metrics else 0),
                file_current_stock=row.file_current_stock,
                closing_stock_current_month=row.closing_stock_current_month,
                closing_stock_previous_month=row.closing_stock_previous_month,
                stock_change=row.stock_change,
                inbound_quantity=row.inbound_quantity,
                warehouse_inbound_quantity=row.warehouse_inbound_quantity,
                return_inbound_quantity=row.return_inbound_quantity,
                outbound_quantity=row.outbound_quantity,
                carryout_quantity=row.carryout_quantity,
                return_outbound_quantity=row.return_outbound_quantity,
                adjustment_inbound_quantity=row.adjustment_inbound_quantity,
                adjustment_outbound_quantity=row.adjustment_outbound_quantity,
                net_change=row.net_change,
                existing_record_id=existing_record.id if existing_record else None,
                existing_record_diff=_record_differs(existing_record, row),
                selected=matched,
                apply_stock_adjustment=False,
                note=existing_record.note if existing_record else None,
            )
        )

    return MonthlyUploadPreviewResponse(
        file_name=file_name,
        year=year,
        month=month,
        total_rows=len(rows),
        matched_rows=matched_rows,
        unmatched_rows=unmatched_rows,
        rows=rows,
    )


def commit_monthly_upload(
    db: Session,
    payload: MonthlyUploadCommitRequest,
) -> MonthlyUploadCommitResponse:
    movement_date = payload.movement_date or date(
        payload.year,
        payload.month,
        monthrange(payload.year, payload.month)[1],
    )
    metrics_map = calculate_product_metrics_map(db)
    existing_records = {
        (record.product_id, record.year, record.month): record
        for record in db.scalars(
            select(MonthlyInventoryRecord).where(
                MonthlyInventoryRecord.year == payload.year,
                MonthlyInventoryRecord.month == payload.month,
            )
        ).all()
    }

    saved_rows = 0
    adjusted_rows = 0
    unmatched_rows = 0
    outbound_payloads: list[tuple[int, int]] = []
    adjustment_payloads: list[tuple[int, int]] = []

    for row in payload.rows:
        if not row.selected:
            continue
        if not row.product_id:
            unmatched_rows += 1
            continue

        record = existing_records.get((row.product_id, payload.year, payload.month))
        if record is None:
            record = MonthlyInventoryRecord(
                product_id=row.product_id,
                year=payload.year,
                month=payload.month,
            )
            db.add(record)

        _apply_record_row(record, row, payload.file_name)
        saved_rows += 1
        outbound_payloads.append((row.product_id, row.outbound_quantity))

        if row.apply_stock_adjustment:
            current_stock = metrics_map.get(row.product_id).current_stock if row.product_id in metrics_map else 0
            adjustment_quantity = row.file_current_stock - current_stock
            if adjustment_quantity != 0:
                adjustment_payloads.append((row.product_id, adjustment_quantity))
                adjusted_rows += 1

    _replace_monthly_generated_movements(
        db=db,
        year=payload.year,
        month=payload.month,
        movement_date=movement_date,
        file_name=payload.file_name,
        outbound_payloads=outbound_payloads,
        adjustment_payloads=adjustment_payloads,
    )
    db.commit()
    return MonthlyUploadCommitResponse(
        total_rows=len(payload.rows),
        saved_rows=saved_rows,
        adjusted_rows=adjusted_rows,
        unmatched_rows=unmatched_rows,
    )


def list_monthly_records(
    db: Session,
    year: int,
    month: int,
    query: str | None = None,
) -> list[MonthlyInventoryRecordResponse]:
    records = list(
        db.scalars(
            select(MonthlyInventoryRecord)
            .where(
                MonthlyInventoryRecord.year == year,
                MonthlyInventoryRecord.month == month,
            )
            .order_by(MonthlyInventoryRecord.product_id)
        ).all()
    )
    query_text = (query or "").strip().lower()
    items: list[MonthlyInventoryRecordResponse] = []
    for record in records:
        product = record.product
        searchable = " ".join(filter(None, [product.name, product.product_code, product.legacy_code, product.barcode])) if product else ""
        if query_text and query_text not in searchable.lower():
            continue
        items.append(_to_record_response(record))
    return items


def update_monthly_record(
    db: Session,
    record_id: int,
    payload: MonthlyInventoryRecordUpdate,
) -> MonthlyInventoryRecordResponse:
    record = db.get(MonthlyInventoryRecord, record_id)
    if not record:
        raise ValueError("월별 데이터를 찾을 수 없습니다.")
    for field, value in payload.model_dump().items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return _to_record_response(record)


def reset_monthly_records(
    db: Session,
    year: int,
    month: int,
) -> MonthlyResetResponse:
    records = list(
        db.scalars(
            select(MonthlyInventoryRecord).where(
                MonthlyInventoryRecord.year == year,
                MonthlyInventoryRecord.month == month,
            )
        ).all()
    )
    deleted_records = len(records)
    for record in records:
        db.delete(record)

    movements = list(
        db.scalars(select(StockMovement).where(StockMovement.movement_date >= date(year, month, 1))).all()
    )
    deleted_movements = 0
    month_token = f"{year}-{month:02d}"
    for movement in movements:
        if movement.movement_date.year != year or movement.movement_date.month != month:
            continue
        memo = movement.memo or ""
        if memo.startswith(f"{MONTHLY_OUTBOUND_MEMO_PREFIX}:{month_token}") or memo.startswith(
            f"{MONTHLY_ADJUST_MEMO_PREFIX}:{month_token}"
        ):
            db.delete(movement)
            deleted_movements += 1

    db.commit()
    return MonthlyResetResponse(
        year=year,
        month=month,
        deleted_records=deleted_records,
        deleted_movements=deleted_movements,
    )


def _to_record_response(record: MonthlyInventoryRecord) -> MonthlyInventoryRecordResponse:
    product = record.product
    return MonthlyInventoryRecordResponse(
        id=record.id,
        product_id=record.product_id,
        product_code=product.product_code if product else None,
        legacy_code=product.legacy_code if product else None,
        name=product.name if product else "",
        barcode=product.barcode if product else None,
        year=record.year,
        month=record.month,
        file_name=record.file_name,
        company_name=record.company_name,
        item_type=record.item_type,
        file_current_stock=record.file_current_stock,
        closing_stock_current_month=record.closing_stock_current_month,
        closing_stock_previous_month=record.closing_stock_previous_month,
        stock_change=record.stock_change,
        inbound_quantity=record.inbound_quantity,
        warehouse_inbound_quantity=record.warehouse_inbound_quantity,
        return_inbound_quantity=record.return_inbound_quantity,
        outbound_quantity=record.outbound_quantity,
        carryout_quantity=record.carryout_quantity,
        return_outbound_quantity=record.return_outbound_quantity,
        adjustment_inbound_quantity=record.adjustment_inbound_quantity,
        adjustment_outbound_quantity=record.adjustment_outbound_quantity,
        net_change=record.net_change,
        note=record.note,
        updated_at=record.updated_at,
    )


def _record_differs(record: MonthlyInventoryRecord | None, row: ParsedUploadRow) -> bool:
    if record is None:
        return False
    comparable_pairs = [
        (record.file_current_stock, row.file_current_stock),
        (record.closing_stock_current_month, row.closing_stock_current_month),
        (record.closing_stock_previous_month, row.closing_stock_previous_month),
        (record.stock_change, row.stock_change),
        (record.inbound_quantity, row.inbound_quantity),
        (record.warehouse_inbound_quantity, row.warehouse_inbound_quantity),
        (record.return_inbound_quantity, row.return_inbound_quantity),
        (record.outbound_quantity, row.outbound_quantity),
        (record.carryout_quantity, row.carryout_quantity),
        (record.return_outbound_quantity, row.return_outbound_quantity),
        (record.adjustment_inbound_quantity, row.adjustment_inbound_quantity),
        (record.adjustment_outbound_quantity, row.adjustment_outbound_quantity),
        (record.net_change, row.net_change),
    ]
    return any(left != right for left, right in comparable_pairs)


def _apply_record_row(record: MonthlyInventoryRecord, row: MonthlyUploadPreviewRow, file_name: str) -> None:
    record.file_name = file_name
    record.company_name = row.company_name
    record.item_type = row.item_type
    record.file_current_stock = row.file_current_stock
    record.closing_stock_current_month = row.closing_stock_current_month
    record.closing_stock_previous_month = row.closing_stock_previous_month
    record.stock_change = row.stock_change
    record.inbound_quantity = row.inbound_quantity
    record.warehouse_inbound_quantity = row.warehouse_inbound_quantity
    record.return_inbound_quantity = row.return_inbound_quantity
    record.outbound_quantity = row.outbound_quantity
    record.carryout_quantity = row.carryout_quantity
    record.return_outbound_quantity = row.return_outbound_quantity
    record.adjustment_inbound_quantity = row.adjustment_inbound_quantity
    record.adjustment_outbound_quantity = row.adjustment_outbound_quantity
    record.net_change = row.net_change
    record.note = row.note


def _replace_monthly_generated_movements(
    db: Session,
    year: int,
    month: int,
    movement_date: date,
    file_name: str,
    outbound_payloads: list[tuple[int, int]],
    adjustment_payloads: list[tuple[int, int]],
) -> None:
    month_token = f"{year}-{month:02d}"
    existing_movements = list(
        db.scalars(select(StockMovement).where(StockMovement.movement_date >= date(year, month, 1))).all()
    )
    for movement in existing_movements:
        if movement.movement_date.year != year or movement.movement_date.month != month:
            continue
        memo = movement.memo or ""
        if memo.startswith(f"{MONTHLY_OUTBOUND_MEMO_PREFIX}:{month_token}") or memo.startswith(
            f"{MONTHLY_ADJUST_MEMO_PREFIX}:{month_token}"
        ):
            db.delete(movement)

    for product_id, quantity in outbound_payloads:
        if quantity <= 0:
            continue
        db.add(
            StockMovement(
                product_id=product_id,
                movement_date=movement_date,
                movement_type="OUT",
                quantity=quantity,
                memo=f"{MONTHLY_OUTBOUND_MEMO_PREFIX}:{month_token}:{file_name}",
            )
        )

    for product_id, quantity in adjustment_payloads:
        if quantity == 0:
            continue
        db.add(
            StockMovement(
                product_id=product_id,
                movement_date=movement_date,
                movement_type="ADJUST",
                quantity=quantity,
                memo=f"{MONTHLY_ADJUST_MEMO_PREFIX}:{month_token}:{file_name}",
            )
        )


def _parse_monthly_upload_bytes(payload: bytes) -> list[ParsedUploadRow]:
    with ZipFile(BytesIO(payload)) as workbook:
        shared_strings = _read_shared_strings(workbook)
        worksheet_name = _first_worksheet_name(workbook)
        root = ET.fromstring(workbook.read(worksheet_name))
        rows = root.find(f"{{{SPREADSHEET_NS}}}sheetData")
        if rows is None:
            return []
        parsed_rows = list(rows)
        if not parsed_rows:
            return []
        header_map = _build_header_map(parsed_rows[0], shared_strings)
        missing_columns = sorted(REQUIRED_COLUMNS - set(header_map))
        if missing_columns:
            raise ValueError(f"필수 컬럼이 없습니다: {', '.join(missing_columns)}")

        items: list[ParsedUploadRow] = []
        for row in parsed_rows[1:]:
            values = _row_to_mapping(row, shared_strings)
            parsed = parse_product_identity(
                product_code=_clean_value(values.get(header_map["상품코드"])),
                legacy_code=None,
                name=_clean_value(values.get(header_map["상품명"])) or "",
            )
            if not parsed.product_code and not parsed.name:
                continue
            items.append(
                ParsedUploadRow(
                    row_number=int(row.attrib.get("r", "0") or 0),
                    company_name=_clean_value(values.get(header_map["회사명"])),
                    product_code=parsed.product_code,
                    legacy_code=parsed.legacy_code,
                    name=parsed.name,
                    barcode=_clean_value(values.get(header_map["바코드"])),
                    item_type=_clean_value(values.get(header_map["구분"])),
                    file_current_stock=_parse_int(values.get(header_map["현재고"])),
                    closing_stock_current_month=_parse_int(values.get(header_map["금월 마감재고"])),
                    closing_stock_previous_month=_parse_int(values.get(header_map["전월 마감재고"])),
                    stock_change=_parse_int(values.get(header_map["마감재고 증감"])),
                    inbound_quantity=_parse_int(values.get(header_map["입고"])),
                    warehouse_inbound_quantity=_parse_int(values.get(header_map["창고 내 입고"])),
                    return_inbound_quantity=_parse_int(values.get(header_map["반품 입고"])),
                    outbound_quantity=_parse_int(values.get(header_map["출고"])),
                    carryout_quantity=_parse_int(values.get(header_map["반출"])),
                    return_outbound_quantity=_parse_int(values.get(header_map["회송"])),
                    adjustment_inbound_quantity=_parse_int(values.get(header_map["재고조정 입고"])),
                    adjustment_outbound_quantity=_parse_int(values.get(header_map["재고조정 반출"])),
                    net_change=_parse_int(values.get(header_map["증감"])),
                )
            )
        return items


def _match_product(db: Session, row: ParsedUploadRow) -> Product | None:
    if row.product_code:
        exact_product = db.scalar(select(Product).where(Product.product_code == row.product_code))
        if exact_product:
            return exact_product

    if row.barcode:
        exact_barcode_product = db.scalar(select(Product).where(Product.barcode == row.barcode))
        if exact_barcode_product:
            return exact_barcode_product

    filters = []
    if row.legacy_code:
        filters.append(Product.legacy_code == row.legacy_code)
        filters.append(Product.product_code == row.legacy_code)
    if row.name and not row.product_code:
        filters.append(Product.name == row.name)
    if not filters:
        return None
    products = list(db.scalars(select(Product).where(or_(*filters))).all())
    if not products:
        return None

    def score(product: Product) -> tuple[int, int]:
        points = 0
        if row.product_code and product.product_code == row.product_code:
            points += 100
        if row.barcode and product.barcode == row.barcode:
            points += 80
        if row.legacy_code and product.legacy_code == row.legacy_code:
            points += 70
        if row.legacy_code and product.product_code == row.legacy_code:
            points += 60
        if row.name and product.name == row.name:
            points += 40
        return (points, product.id)

    products.sort(key=score, reverse=True)
    return products[0]


def _build_header_map(row: ET.Element, shared_strings: list[str]) -> dict[str, str]:
    raw_headers = _row_to_mapping(row, shared_strings)
    return {value.strip(): column for column, value in raw_headers.items() if value.strip()}


def _first_worksheet_name(workbook: ZipFile) -> str:
    worksheet_names = sorted(
        name
        for name in workbook.namelist()
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
    )
    if not worksheet_names:
        raise ValueError("워크시트를 찾을 수 없습니다.")
    return worksheet_names[0]


def _read_shared_strings(workbook: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return []
    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    return [
        "".join((text_node.text or "") for text_node in item.iterfind(f".//{{{SPREADSHEET_NS}}}t"))
        for item in root.findall(f"{{{SPREADSHEET_NS}}}si")
    ]


def _row_to_mapping(row: ET.Element, shared_strings: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for cell in row.findall(f"{{{SPREADSHEET_NS}}}c"):
        column = "".join(character for character in cell.attrib.get("r", "") if character.isalpha())
        values[column] = _cell_value(cell, shared_strings)
    return values


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    value_node = cell.find(f"{{{SPREADSHEET_NS}}}v")
    if value_node is None:
        inline_string = cell.find(f"{{{SPREADSHEET_NS}}}is")
        if inline_string is None:
            return ""
        return "".join((text_node.text or "") for text_node in inline_string.iterfind(f".//{{{SPREADSHEET_NS}}}t"))
    raw_value = value_node.text or ""
    if cell_type == "s":
        return shared_strings[int(raw_value)]
    return raw_value


def _clean_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _parse_int(value: str | None) -> int:
    cleaned = _clean_value(value)
    if not cleaned:
        return 0
    try:
        return int(float(cleaned.replace(",", "")))
    except ValueError:
        return 0
