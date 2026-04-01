from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.crud.order_crud import (
    count_abnormal_orders,
    count_charging_orders,
    count_today_completed_orders,
    get_order_by_id,
    list_abnormal_orders,
    list_history_orders,
    list_realtime_orders,
    sum_today_charge_amount,
    sum_today_total_amount,
)
from app.models.models import Order


ORDER_STATUS_LABELS = {
    0: "charging",
    1: "completed",
    2: "abnormal",
}
PAY_STATUS_LABELS = {
    0: "unpaid",
    1: "paid",
    2: "refunded",
}
SETTLEMENT_STATUS_LABELS = {
    0: "pending",
    1: "settled",
}


def get_station_name(order: Order) -> str:
    if order.station:
        return order.station.name
    if order.charger and order.charger.station:
        return order.charger.station.name
    return ""


def order_duration_minutes(order: Order) -> int:
    if order.charge_duration is not None:
        return order.charge_duration
    if order.start_time and order.end_time:
        return max(int((order.end_time - order.start_time).total_seconds() / 60), 0)
    if order.start_time and order.status == 0:
        return max(int((datetime.now() - order.start_time).total_seconds() / 60), 0)
    return 0


def serialize_order(order: Order) -> dict[str, Any]:
    return {
        "id": order.id,
        "order_no": order.order_no,
        "user_id": order.user_id,
        "user_phone": order.user.phone if order.user else "",
        "operator_id": order.operator_id,
        "operator_name": order.operator.name if order.operator else "",
        "station_id": order.station_id,
        "station_name": get_station_name(order),
        "charger_id": order.charger_id,
        "charger_sn": order.charger.sn_code if order.charger else "",
        "vin": order.vin or (order.user.vin_code if order.user else None),
        "start_time": order.start_time.strftime("%Y-%m-%d %H:%M:%S") if order.start_time else "",
        "end_time": order.end_time.strftime("%Y-%m-%d %H:%M:%S") if order.end_time else "",
        "charge_duration": order_duration_minutes(order),
        "charge_amount": float(order.charge_amount),
        "electricity_fee": float(order.electricity_fee),
        "service_fee": float(order.service_fee),
        "total_amount": float(order.total_amount),
        "pay_status": order.pay_status,
        "pay_status_label": PAY_STATUS_LABELS.get(order.pay_status, "unknown"),
        "order_status": ORDER_STATUS_LABELS.get(order.status, "unknown"),
        "order_status_code": order.status,
        "abnormal_reason": order.abnormal_reason,
        "settlement_status": order.settle_status,
        "settlement_status_label": SETTLEMENT_STATUS_LABELS.get(order.settle_status, "unknown"),
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else "",
        "updated_at": order.updated_at.strftime("%Y-%m-%d %H:%M:%S") if order.updated_at else "",
    }


def get_realtime_order_list(db: Session, limit: int = 50) -> list[dict[str, Any]]:
    return [serialize_order(order) for order in list_realtime_orders(db, limit=limit)]


def get_history_order_list(db: Session, limit: int = 100) -> list[dict[str, Any]]:
    return [serialize_order(order) for order in list_history_orders(db, limit=limit)]


def get_abnormal_order_list(db: Session, limit: int = 50) -> list[dict[str, Any]]:
    return [serialize_order(order) for order in list_abnormal_orders(db, limit=limit)]


def get_order_detail_data(db: Session, order_id: int) -> dict[str, Any] | None:
    order = get_order_by_id(db, order_id)
    if not order:
        return None
    return serialize_order(order)


def force_stop_order(db: Session, order_id: int) -> Order | None:
    order = get_order_by_id(db, order_id)
    if not order or order.status != 0:
        return None

    now = datetime.now()
    order.end_time = now
    order.charge_duration = order_duration_minutes(order)
    order.status = 1
    order.pay_status = 1
    if order.station_id is None and order.charger and order.charger.station_id:
        order.station_id = order.charger.station_id
    if not order.vin and order.user and order.user.vin_code:
        order.vin = order.user.vin_code
    db.commit()
    db.refresh(order)
    return order


def mark_order_abnormal(db: Session, order_id: int, abnormal_reason: str) -> Order | None:
    order = get_order_by_id(db, order_id)
    if not order or order.status != 0:
        return None

    now = datetime.now()
    order.end_time = now
    order.charge_duration = order_duration_minutes(order)
    order.status = 2
    order.abnormal_reason = abnormal_reason.strip() or "系统标记异常"
    if order.station_id is None and order.charger and order.charger.station_id:
        order.station_id = order.charger.station_id
    if not order.vin and order.user and order.user.vin_code:
        order.vin = order.user.vin_code
    db.commit()
    db.refresh(order)
    return order


def get_order_stats(db: Session) -> dict[str, Any]:
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    charging_count = count_charging_orders(db)
    abnormal_count = count_abnormal_orders(db)
    today_completed = count_today_completed_orders(db, today_start, today_end)
    today_charge_amount = sum_today_charge_amount(db, today_start, today_end)
    today_total_amount = sum_today_total_amount(db, today_start, today_end)

    return {
        "charging_count": charging_count,
        "today_completed_count": today_completed,
        "today_charge_amount": float(Decimal(str(today_charge_amount))),
        "today_total_amount": float(Decimal(str(today_total_amount))),
        "abnormal_count": abnormal_count,
    }
