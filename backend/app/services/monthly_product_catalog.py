from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import xml.etree.ElementTree as ET

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.services.product_identity import parse_product_identity


SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REQUIRED_COLUMNS = {
    "회사명",
    "상품코드",
    "상품명",
    "바코드",
    "구분",
}


@dataclass
class MonthlyCatalogRow:
    row_number: int
    company_name: str | None
    product_code: str | None
    legacy_code: str | None
    name: str
    barcode: str | None
    item_type: str | None
    current_stock: int
    raw_name: str


@dataclass
class ProductImportSummary:
    total_rows: int
    import_target_rows: int
    created_count: int
    updated_count: int
    skipped_zero_stock_legacy_rows: int


def parse_monthly_catalog_xlsx(file_path: str | Path) -> list[MonthlyCatalogRow]:
    workbook_path = Path(file_path)
    with ZipFile(workbook_path) as workbook:
        shared_strings = _read_shared_strings(workbook)
        worksheet_name = _first_worksheet_name(workbook)
        root = ET.fromstring(workbook.read(worksheet_name))
        rows = root.find(f"{{{SPREADSHEET_NS}}}sheetData")
        if rows is None:
            return []

        parsed_rows = list(rows)
        if not parsed_rows:
            return []

        header_cells = _row_to_mapping(parsed_rows[0], shared_strings)
        header_map = {value.strip(): column for column, value in header_cells.items() if value.strip()}
        missing_columns = sorted(REQUIRED_COLUMNS - set(header_map))
        if missing_columns:
            missing = ", ".join(missing_columns)
            raise ValueError(f"필수 컬럼이 없습니다: {missing}")

        items: list[MonthlyCatalogRow] = []
        for row in parsed_rows[1:]:
            values = _row_to_mapping(row, shared_strings)
            product_code = _clean_value(values.get(header_map["상품코드"]))
            raw_name = _clean_value(values.get(header_map["상품명"])) or ""
            barcode = _clean_value(values.get(header_map["바코드"]))
            company_name = _clean_value(values.get(header_map["회사명"]))
            item_type = _clean_value(values.get(header_map["구분"]))
            current_stock = _parse_int(values.get("G"))

            if not product_code and not raw_name:
                continue

            parsed = parse_product_identity(product_code=product_code, legacy_code=None, name=raw_name)
            items.append(
                MonthlyCatalogRow(
                    row_number=int(row.attrib.get("r", "0") or 0),
                    company_name=company_name,
                    product_code=parsed.product_code,
                    legacy_code=parsed.legacy_code,
                    name=parsed.name,
                    barcode=barcode,
                    item_type=item_type,
                    current_stock=current_stock,
                    raw_name=raw_name,
                )
            )

    return items


def upsert_products_from_monthly_catalog(
    db: Session,
    rows: list[MonthlyCatalogRow],
) -> ProductImportSummary:
    created_count = 0
    updated_count = 0
    ambiguous_legacy_codes = {
        legacy_code
        for legacy_code, count in Counter(row.legacy_code for row in rows if row.legacy_code).items()
        if count > 1
    }

    for row in rows:
        product = _find_existing_product(db, row, ambiguous_legacy_codes)
        if product is None:
            product = Product(
                product_code=row.product_code,
                legacy_code=row.legacy_code,
                name=row.name,
                barcode=row.barcode,
            )
            db.add(product)
            created_count += 1
            db.flush()
            continue

        product.product_code = row.product_code or product.product_code
        product.legacy_code = row.legacy_code or product.legacy_code
        product.name = row.name or product.name
        if row.barcode:
            product.barcode = row.barcode
        updated_count += 1
        db.flush()

    db.commit()
    return ProductImportSummary(
        total_rows=len(rows),
        import_target_rows=len(rows),
        created_count=created_count,
        updated_count=updated_count,
        skipped_zero_stock_legacy_rows=0,
    )


def _find_existing_product(
    db: Session,
    row: MonthlyCatalogRow,
    ambiguous_legacy_codes: set[str],
) -> Product | None:
    if row.product_code:
        exact_product = db.scalar(select(Product).where(Product.product_code == row.product_code))
        if exact_product:
            return exact_product

    if row.barcode:
        exact_barcode_product = db.scalar(select(Product).where(Product.barcode == row.barcode))
        if exact_barcode_product:
            return exact_barcode_product

    filters = []
    use_legacy_match = bool(row.legacy_code and row.legacy_code not in ambiguous_legacy_codes)
    if use_legacy_match:
        filters.append(Product.legacy_code == row.legacy_code)
        filters.append(Product.product_code == row.legacy_code)
    if row.name and not row.product_code:
        filters.append(Product.name == row.name)

    if not filters:
        return None

    candidates = list(db.scalars(select(Product).where(or_(*filters))).all())
    if not candidates:
        return None

    def score(product: Product) -> tuple[int, int]:
        points = 0
        if row.product_code and product.product_code == row.product_code:
            points += 100
        if use_legacy_match and product.legacy_code == row.legacy_code:
            points += 80
        if use_legacy_match and product.product_code == row.legacy_code:
            points += 70
        if row.barcode and product.barcode == row.barcode:
            points += 60
        if row.name and product.name == row.name:
            points += 40
        return (points, product.id)

    candidates.sort(key=score, reverse=True)
    return candidates[0]


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
