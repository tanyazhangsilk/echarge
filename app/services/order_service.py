from __future__ import annotations

import json
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
    list_all_orders,
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
ORDER_STATUS_TEXTS = {
    0: "充电中",
    1: "已完成",
    2: "异常结束",
}
PAY_STATUS_LABELS = {
    0: "unpaid",
    1: "paid",
    2: "refunded",
}
PAY_STATUS_TEXTS = {
    0: "待支付",
    1: "已支付",
    2: "已退款",
}
SETTLEMENT_STATUS_LABELS = {
    0: "pending",
    1: "settled",
}
DEFAULT_FLAT_PRICE = Decimal("1.18")
DEFAULT_SERVICE_PRICE = Decimal("0.72")


def get_station_name(order: Order) -> str:
    if order.station:
        return order.station.name
    if order.charger and order.charger.station:
        return order.charger.station.name
    return ""


def get_charger_name(order: Order) -> str:
    if not order.charger:
        return ""
    station_name = get_station_name(order)[:8] or "示范站"
    suffix = order.charger.sn_code[-4:] if order.charger.sn_code else f"{order.charger.id:04d}"
    return f"{station_name}-{suffix}号桩"


def get_charger_power_kw(order: Order) -> Decimal:
    if not order.charger or not order.charger.type:
        return Decimal("60")
    charger_type = order.charger.type.upper()
    if "AC" in charger_type:
        return Decimal("7")
    if "DC" in charger_type:
        return Decimal("120") if order.charger.id % 2 == 0 else Decimal("90")
    return Decimal("60")


def order_duration_minutes(order: Order) -> int:
    if order.charge_duration is not None:
        return order.charge_duration
    if order.start_time and order.end_time:
        return max(int((order.end_time - order.start_time).total_seconds() / 60), 0)
    if order.start_time and order.status == 0:
        return max(int((datetime.now() - order.start_time).total_seconds() / 60), 0)
    return 0


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _resolve_template_rates(order: Order) -> tuple[Decimal, Decimal]:
    template = order.station.price_template if order.station else None
    if template and template.rules_json:
        try:
            data = json.loads(template.rules_json)
            return (
                Decimal(str(data.get("flat_price", DEFAULT_FLAT_PRICE))),
                Decimal(str(data.get("service_price", DEFAULT_SERVICE_PRICE))),
            )
        except Exception:
            pass
    return DEFAULT_FLAT_PRICE, DEFAULT_SERVICE_PRICE


def recalculate_order_amounts(
    order: Order,
    now: datetime | None = None,
    minimum_charge_kwh: Decimal | None = None,
) -> Order:
    current_time = now or datetime.now()
    if order.start_time is None:
        order.start_time = current_time

    if order.end_time and order.end_time > order.start_time:
        duration = max(int((order.end_time - order.start_time).total_seconds() / 60), 0)
    else:
        duration = max(int((current_time - order.start_time).total_seconds() / 60), 0)

    power_kw = min(get_charger_power_kw(order), Decimal("60"))
    estimated_charge = Decimal(str(max(duration, 1))) / Decimal("60") * power_kw * Decimal("0.55")
    baseline_charge = Decimal(str(order.total_kwh or 0))
    if minimum_charge_kwh is not None:
        baseline_charge = max(baseline_charge, minimum_charge_kwh)
    charge_amount = max(baseline_charge, estimated_charge)

    order.charge_duration = duration
    order.total_kwh = _quantize_decimal(charge_amount)

    flat_price, service_price = _resolve_template_rates(order)
    order.ele_fee = _quantize_decimal(order.total_kwh * flat_price)
    order.service_fee = _quantize_decimal(order.total_kwh * service_price)
    order.total_fee = _quantize_decimal(order.ele_fee + order.service_fee)
    return order


def serialize_order(order: Order) -> dict[str, Any]:
    duration = order_duration_minutes(order)
    return {
        "id": order.id,
        "order_no": order.order_no,
        "user_id": order.user_id,
        "user_phone": order.user.phone if order.user else "",
        "user_nickname": order.user.nickname if order.user and order.user.nickname else f"用户{str(order.user.phone)[-4:]}" if order.user else "",
        "operator_id": order.operator_id,
        "operator_name": order.operator.name if order.operator else "",
        "station_id": order.station_id,
        "station_name": get_station_name(order),
        "charger_id": order.charger_id,
        "charger_sn": order.charger.sn_code if order.charger else "",
        "charger_name": get_charger_name(order),
        "vin": order.vin or (order.user.vin_code if order.user else None),
        "start_time": order.start_time.strftime("%Y-%m-%d %H:%M:%S") if order.start_time else "",
        "end_time": order.end_time.strftime("%Y-%m-%d %H:%M:%S") if order.end_time else "",
        "charge_duration": duration,
        "charge_duration_text": f"{duration} 分钟",
        "charge_amount": float(order.charge_amount),
        "electricity_fee": float(order.electricity_fee),
        "ele_fee": float(order.electricity_fee),
        "service_fee": float(order.service_fee),
        "total_amount": float(order.total_amount),
        "total_fee": float(order.total_amount),
        "pay_status": order.pay_status,
        "pay_status_label": PAY_STATUS_LABELS.get(order.pay_status, "unknown"),
        "pay_status_text": PAY_STATUS_TEXTS.get(order.pay_status, "未知"),
        "order_status": ORDER_STATUS_LABELS.get(order.status, "unknown"),
        "status": order.status,
        "order_status_code": order.status,
        "status_text": ORDER_STATUS_TEXTS.get(order.status, "未知状态"),
        "abnormal_reason": order.abnormal_reason,
        "settlement_status": order.settle_status,
        "settlement_status_label": SETTLEMENT_STATUS_LABELS.get(order.settle_status, "unknown"),
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else "",
        "updated_at": order.updated_at.strftime("%Y-%m-%d %H:%M:%S") if order.updated_at else "",
    }


def get_all_order_list(db: Session, limit: int = 100, operator_id: int | None = None) -> list[dict[str, Any]]:
    return [serialize_order(order) for order in list_all_orders(db, limit=limit, operator_id=operator_id)]


def get_realtime_order_list(db: Session, limit: int = 50, operator_id: int | None = None) -> list[dict[str, Any]]:
    return [serialize_order(order) for order in list_realtime_orders(db, limit=limit, operator_id=operator_id)]


def get_history_order_list(db: Session, limit: int = 100, operator_id: int | None = None) -> list[dict[str, Any]]:
    return [serialize_order(order) for order in list_history_orders(db, limit=limit, operator_id=operator_id)]


def get_abnormal_order_list(db: Session, limit: int = 50, operator_id: int | None = None) -> list[dict[str, Any]]:
    return [serialize_order(order) for order in list_abnormal_orders(db, limit=limit, operator_id=operator_id)]


def get_order_detail_data(db: Session, order_id: int, operator_id: int | None = None) -> dict[str, Any] | None:
    order = get_order_by_id(db, order_id, operator_id=operator_id)
    if not order:
        return None
    return serialize_order(order)


def force_stop_order(db: Session, order_id: int, operator_id: int | None = None) -> Order | None:
    order = get_order_by_id(db, order_id, operator_id=operator_id)
    if not order or order.status != 0:
        return None

    now = datetime.now()
    order.end_time = now
    recalculate_order_amounts(order, now=now)
    order.status = 1
    order.pay_status = 1
    if order.station_id is None and order.charger and order.charger.station_id:
        order.station_id = order.charger.station_id
    if not order.vin and order.user and order.user.vin_code:
        order.vin = order.user.vin_code
    if order.charger:
        order.charger.status = 0
    db.commit()
    db.refresh(order)
    return order


def finish_order(db: Session, order_id: int, operator_id: int | None = None) -> Order | None:
    return force_stop_order(db, order_id, operator_id=operator_id)


def mark_order_abnormal(db: Session, order_id: int, abnormal_reason: str, operator_id: int | None = None) -> Order | None:
    order = get_order_by_id(db, order_id, operator_id=operator_id)
    if not order or order.status != 0:
        return None

    now = datetime.now()
    order.end_time = now
    recalculate_order_amounts(order, now=now)
    order.status = 2
    order.abnormal_reason = abnormal_reason.strip() or "运营商手动标记异常"
    if order.station_id is None and order.charger and order.charger.station_id:
        order.station_id = order.charger.station_id
    if not order.vin and order.user and order.user.vin_code:
        order.vin = order.user.vin_code
    if order.charger:
        order.charger.status = 2
    db.commit()
    db.refresh(order)
    return order


def get_order_stats(db: Session, operator_id: int | None = None) -> dict[str, Any]:
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    charging_count = count_charging_orders(db, operator_id=operator_id)
    abnormal_count = count_abnormal_orders(db, operator_id=operator_id)
    today_completed = count_today_completed_orders(db, today_start, today_end, operator_id=operator_id)
    today_charge_amount = sum_today_charge_amount(db, today_start, today_end, operator_id=operator_id)
    today_total_amount = sum_today_total_amount(db, today_start, today_end, operator_id=operator_id)

    return {
        "charging_count": charging_count,
        "today_completed_count": today_completed,
        "today_charge_amount": float(Decimal(str(today_charge_amount))),
        "today_total_amount": float(Decimal(str(today_total_amount))),
        "abnormal_count": abnormal_count,
    }
