from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from app.db.bootstrap import ensure_schema
from app.db.session import SessionLocal, engine
from app.services.monthly_product_catalog import (
    parse_monthly_catalog_xlsx,
    upsert_products_from_monthly_catalog,
)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python backend/scripts/import_products_from_monthly_xlsx.py <xlsx_path>")
        return 1

    workbook_path = Path(sys.argv[1]).expanduser().resolve()
    if not workbook_path.exists():
        print(f"file not found: {workbook_path}")
        return 1

    ensure_schema(engine)
    rows = parse_monthly_catalog_xlsx(workbook_path)

    session = SessionLocal()
    try:
        summary = upsert_products_from_monthly_catalog(session, rows)
    finally:
        session.close()

    print(f"rows={summary.total_rows}")
    print(f"import_target_rows={summary.import_target_rows}")
    print(f"skipped_zero_stock_legacy_rows={summary.skipped_zero_stock_legacy_rows}")
    print(f"created={summary.created_count}")
    print(f"updated={summary.updated_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
