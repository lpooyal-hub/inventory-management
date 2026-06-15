from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.monthly_inventory_record import MonthlyInventoryRecord
from app.models.product import Product
from app.models.stock_movement import MovementType, StockMovement
from app.schemas.reports import (
    InventorySummaryItem,
    InventorySummaryResponse,
    MonthlyOutboundItem,
    MonthlyOutboundResponse,
    MonthlyTrendMonth,
    MonthlyTrendProductRow,
    MonthlyTrendResponse,
    ShortageItem,
    ShortageResponse,
)


@dataclass
class ProductMetrics:
    current_stock: int
    current_month_outbound: int
    average_monthly_outbound_last_3_months: float
    remaining_expected_outbound_this_month: float
    projected_stock_after_expected_outbound: float
    shortage_status: str
    production_order_required: bool


def build_inventory_summary(db: Session) -> InventorySummaryResponse:
    today = date.today()
    products = list(db.scalars(select(Product).order_by(Product.name)).all())
    metrics_map = calculate_product_metrics_map(db, today)
    items = [
        InventorySummaryItem(
            product_id=product.id,
            product_code=product.product_code,
            legacy_code=product.legacy_code,
            name=product.name,
            barcode=product.barcode,
            **metrics_map.get(product.id, ProductMetrics(0, 0, 0, 0, 0, "정상", False)).__dict__,
        )
        for product in products
    ]
    return InventorySummaryResponse(items=items)


def build_monthly_outbound_report(db: Session, year: int, month: int) -> MonthlyOutboundResponse:
    products = {product.id: product for product in db.scalars(select(Product)).all()}
    totals = defaultdict(int)
    for movement in db.scalars(select(StockMovement)).all():
        if _normalize_movement_type(movement.movement_type) != MovementType.OUT:
            continue
        if movement.movement_date.year == year and movement.movement_date.month == month:
            totals[movement.product_id] += movement.quantity
    items = [
        MonthlyOutboundItem(
            product_id=product_id,
            product_code=products[product_id].product_code if product_id in products else None,
            legacy_code=products[product_id].legacy_code if product_id in products else None,
            name=products[product_id].name if product_id in products else "",
            outbound_quantity=quantity,
        )
        for product_id, quantity in sorted(totals.items(), key=lambda item: products[item[0]].name if item[0] in products else "")
    ]
    return MonthlyOutboundResponse(year=year, month=month, items=items)


def build_monthly_outbound_trend(
    db: Session,
    year: int,
    month: int,
    months: int = 12,
) -> MonthlyTrendResponse:
    month_keys = _recent_months(year, month, count=months)
    chronological_month_keys = list(reversed(month_keys))
    products = {product.id: product for product in db.scalars(select(Product)).all()}
    per_product_totals: dict[int, dict[tuple[int, int], int]] = defaultdict(lambda: defaultdict(int))

    for movement in db.scalars(select(StockMovement)).all():
        if _normalize_movement_type(movement.movement_type) != MovementType.OUT:
            continue
        month_key = (movement.movement_date.year, movement.movement_date.month)
        if month_key not in chronological_month_keys:
            continue
        per_product_totals[movement.product_id][month_key] += movement.quantity

    month_summaries = [
        MonthlyTrendMonth(
            year=month_year,
            month=month_value,
            label=f"{month_year}-{month_value:02d}",
            total_outbound_quantity=sum(
                product_totals.get((month_year, month_value), 0)
                for product_totals in per_product_totals.values()
            ),
        )
        for month_year, month_value in chronological_month_keys
    ]

    items = []
    for product_id, product_totals in sorted(
        per_product_totals.items(),
        key=lambda item: products[item[0]].name if item[0] in products else "",
    ):
        quantities = [product_totals.get(month_key, 0) for month_key in chronological_month_keys]
        total = sum(quantities)
        product = products.get(product_id)
        items.append(
            MonthlyTrendProductRow(
                product_id=product_id,
                product_code=product.product_code if product else None,
                legacy_code=product.legacy_code if product else None,
                name=product.name if product else "",
                monthly_quantities=quantities,
                total_outbound_quantity=total,
                average_outbound_quantity=round(total / months, 2),
            )
        )

    return MonthlyTrendResponse(
        anchor_year=year,
        anchor_month=month,
        months=month_summaries,
        items=items,
    )


def build_shortage_report(db: Session) -> ShortageResponse:
    today = date.today()
    products = list(db.scalars(select(Product).order_by(Product.name)).all())
    metrics_map = calculate_product_metrics_map(db, today)
    items = []
    for product in products:
        metrics = metrics_map.get(product.id, ProductMetrics(0, 0, 0, 0, 0, "정상", False))
        if metrics.shortage_status == "정상":
            continue
        items.append(
            ShortageItem(
                product_id=product.id,
                product_code=product.product_code,
                legacy_code=product.legacy_code,
                name=product.name,
                current_stock=metrics.current_stock,
                current_month_outbound=metrics.current_month_outbound,
                average_monthly_outbound_last_3_months=metrics.average_monthly_outbound_last_3_months,
                remaining_expected_outbound_this_month=metrics.remaining_expected_outbound_this_month,
                projected_stock_after_expected_outbound=metrics.projected_stock_after_expected_outbound,
                shortage_status=metrics.shortage_status,
                production_order_required=metrics.production_order_required,
            )
        )
    return ShortageResponse(items=items)


def calculate_product_metrics_map(
    db: Session,
    today: date | None = None,
) -> dict[int, ProductMetrics]:
    current_day = today or date.today()
    movements = list(db.scalars(select(StockMovement)).all())
    monthly_records = list(db.scalars(select(MonthlyInventoryRecord)).all())
    product_ids = set(db.scalars(select(Product.id)).all())
    product_ids.update(movement.product_id for movement in movements)
    product_ids.update(record.product_id for record in monthly_records)
    return {
        product_id: _calculate_metrics(product_id, movements, monthly_records, current_day)
        for product_id in product_ids
    }


def _calculate_metrics(
    product_id: int,
    movements: list[StockMovement],
    monthly_records: list[MonthlyInventoryRecord],
    today: date,
) -> ProductMetrics:
    movement_current_stock = 0
    current_month_outbound_from_movements = 0
    monthly_outbound_totals_from_movements = defaultdict(int)
    previous_three_months = _previous_months(today.year, today.month, count=3)
    current_month_key = (today.year, today.month)
    monthly_record_map = {
        (record.year, record.month): record
        for record in monthly_records
        if record.product_id == product_id
    }
    current_month_record = monthly_record_map.get(current_month_key)

    for movement in movements:
        if movement.product_id != product_id:
            continue
        movement_type = _normalize_movement_type(movement.movement_type)
        if movement_type == MovementType.IN:
            movement_current_stock += movement.quantity
        elif movement_type == MovementType.OUT:
            movement_current_stock -= movement.quantity
            month_key = (movement.movement_date.year, movement.movement_date.month)
            monthly_outbound_totals_from_movements[month_key] += movement.quantity
            if month_key == current_month_key:
                current_month_outbound_from_movements += movement.quantity
        elif movement_type == MovementType.ADJUST:
            movement_current_stock += movement.quantity

    if current_month_record:
        current_stock = current_month_record.file_current_stock
        current_month_outbound = current_month_record.outbound_quantity
        post_snapshot_delta = 0
        post_snapshot_outbound = 0
        for movement in movements:
            if movement.product_id != product_id:
                continue
            if movement.movement_date.year != today.year or movement.movement_date.month != today.month:
                continue
            if _is_monthly_upload_generated_movement(movement.memo):
                continue
            if movement.created_at and movement.created_at <= current_month_record.updated_at:
                continue
            movement_type = _normalize_movement_type(movement.movement_type)
            if movement_type == MovementType.IN:
                post_snapshot_delta += movement.quantity
            elif movement_type == MovementType.OUT:
                post_snapshot_delta -= movement.quantity
                post_snapshot_outbound += movement.quantity
            elif movement_type == MovementType.ADJUST:
                post_snapshot_delta += movement.quantity
        current_stock += post_snapshot_delta
        current_month_outbound += post_snapshot_outbound
    else:
        current_stock = movement_current_stock
        current_month_outbound = current_month_outbound_from_movements

    last_3_month_total = sum(
        monthly_record_map[month_key].outbound_quantity
        if month_key in monthly_record_map
        else monthly_outbound_totals_from_movements[month_key]
        for month_key in previous_three_months
    )
    average = last_3_month_total / 3
    remaining_expected_outbound = max(average - current_month_outbound, 0) * 1.1
    projected_stock_after_expected_outbound = current_stock - remaining_expected_outbound
    shortage_status = "정상"
    if remaining_expected_outbound > 0 and current_stock < remaining_expected_outbound * 0.5:
        shortage_status = "심각 부족"
    elif projected_stock_after_expected_outbound < 0:
        shortage_status = "부족"

    return ProductMetrics(
        current_stock=current_stock,
        current_month_outbound=current_month_outbound,
        average_monthly_outbound_last_3_months=round(average, 2),
        remaining_expected_outbound_this_month=round(remaining_expected_outbound, 2),
        projected_stock_after_expected_outbound=round(projected_stock_after_expected_outbound, 2),
        shortage_status=shortage_status,
        production_order_required=shortage_status != "정상",
    )


def _recent_months(year: int, month: int, count: int) -> list[tuple[int, int]]:
    months = []
    current_year = year
    current_month = month
    for _ in range(count):
        months.append((current_year, current_month))
        current_month -= 1
        if current_month == 0:
            current_month = 12
            current_year -= 1
    return months


def _previous_months(year: int, month: int, count: int) -> list[tuple[int, int]]:
    previous_month = month - 1
    previous_year = year
    if previous_month == 0:
        previous_month = 12
        previous_year -= 1
    return _recent_months(previous_year, previous_month, count)


def _is_monthly_upload_generated_movement(memo: str | None) -> bool:
    text = memo or ""
    return text.startswith("MONTHLY_UPLOAD_OUTBOUND:") or text.startswith("MONTHLY_UPLOAD_ADJUST:")


def _normalize_movement_type(value: str | MovementType) -> MovementType | None:
    if isinstance(value, MovementType):
        return value

    normalized = str(value or "").strip().upper()
    alias_map = {
        "IN": MovementType.IN,
        "INBOUND": MovementType.IN,
        "OUT": MovementType.OUT,
        "OUTBOUND": MovementType.OUT,
        "ADJUST": MovementType.ADJUST,
        "ADJUSTMENT": MovementType.ADJUST,
    }
    return alias_map.get(normalized)
