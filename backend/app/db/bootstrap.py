from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    if "products" not in inspector.get_table_names():
        return

    product_columns = {column["name"] for column in inspector.get_columns("products")}

    with engine.begin() as connection:
        if "legacy_code" not in product_columns:
            connection.execute(text("ALTER TABLE products ADD COLUMN legacy_code VARCHAR(80)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_products_legacy_code ON products (legacy_code)"))
