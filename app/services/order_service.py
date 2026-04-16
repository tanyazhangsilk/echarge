from __future__ import annotations

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session, joinedload, load_only

from app.models.models import Charger, Operator, Order, PriceTemplate, Station, User
from app.services.station_service import get_charger_name, get_charger_power_kw, station_status_text


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

ORDER_SOURCE_TEXTS = {
    "manual_demo": "手动模拟",
    "qr_code": "扫码充电",
    "mini_program": "小程序",
}

DEFAULT_FLAT_PRICE = Decimal("1.18")
DEFAULT_SERVICE_PRICE = Decimal("0.72")


def _normalize_page(page: int | None, page_size: int | None, *, default_size: int = 10, max_size: int = 100) -> tuple[int, int]:
    safe_page = max(int(page or 1), 1)
    safe_page_size = max(int(page_size or default_size), 1)
    return safe_page, min(safe_page_size, max_size)


def _to_decimal(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _parse_date_text(value: str | None, *, end_of_day: bool = False) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.strptime(value.strip(), "%Y-%m-%d")
    except ValueError:
        return None
    if end_of_day:
        return parsed + timedelta(days=1)
    return parsed


def get_station_name(order: Order) -> str:
    if order.station:
        return order.station.name
    if order.charger and order.charger.station:
        return order.charger.station.name
    return ""


def get_order_source_text(source_type: str | None) -> str:
    return ORDER_SOURCE_TEXTS.get((source_type or "").strip(), "未知来源")


def get_order_charger_name(order: Order) -> str:
    if not order.charger:
        return ""
    return get_charger_name(order.charger)


def get_order_charger_power_kw(order: Order) -> Decimal:
    if not order.charger:
        return Decimal("60")
    return get_charger_power_kw(order.charger)


def order_duration_minutes(order: Order) -> int:
    if order.charge_duration is not None:
        return order.charge_duration
    if order.start_time and order.end_time:
        return max(int((order.end_time - order.start_time).total_seconds() / 60), 0)
    if order.start_time and order.status == 0:
        return max(int((datetime.now() - order.start_time).total_seconds() / 60), 0)
    return 0


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
            return DEFAULT_FLAT_PRICE, DEFAULT_SERVICE_PRICE
    return DEFAULT_FLAT_PRICE, DEFAULT_SERVICE_PRICE


def _build_fee_detail(order: Order) -> dict[str, Any]:
    flat_price, service_price = _resolve_template_rates(order)
    return {
        "charge_amount": float(order.charge_amount or 0),
        "electricity_fee": float(order.electricity_fee or 0),
        "service_fee": float(order.service_fee or 0),
        "total_amount": float(order.total_amount or 0),
        "flat_price": float(flat_price),
        "service_price": float(service_price),
    }


def _build_status_flow(order: Order) -> list[dict[str, Any]]:
    items = [
        {
            "key": "created",
            "title": "创建订单",
            "time": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else "",
            "desc": f"订单来源：{get_order_source_text(order.source_type)}",
            "tone": "primary",
        },
        {
            "key": "started",
            "title": "开始充电",
            "time": order.start_time.strftime("%Y-%m-%d %H:%M:%S") if order.start_time else "",
            "desc": f"电站：{get_station_name(order) or '-'}，电桩：{get_order_charger_name(order) or '-'}",
            "tone": "warning",
        },
    ]

    if order.end_time:
        items.append(
            {
                "key": "ended",
                "title": "异常结束" if order.status == 2 else "完成充电",
                "time": order.end_time.strftime("%Y-%m-%d %H:%M:%S") if order.end_time else "",
                "desc": order.abnormal_reason if order.status == 2 else "订单已结束并进入归档列表",
                "tone": "danger" if order.status == 2 else "success",
            }
        )
    else:
        items.append(
            {
                "key": "running",
                "title": "充电进行中",
                "time": order.updated_at.strftime("%Y-%m-%d %H:%M:%S") if order.updated_at else "",
                "desc": "当前订单仍处于实时充电状态",
                "tone": "warning",
            }
        )

    return items


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

    power_kw = min(get_order_charger_power_kw(order), Decimal("180"))
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
        "user_nickname": order.user.nickname if order.user and order.user.nickname else (f"用户{str(order.user.phone)[-4:]}" if order.user else ""),
        "operator_id": order.operator_id,
        "operator_name": order.operator.name if order.operator else "",
        "station_id": order.station_id,
        "station_name": get_station_name(order),
        "station_status": order.station.status if order.station else None,
        "station_status_text": station_status_text(order.station.status) if order.station else "",
        "charger_id": order.charger_id,
        "charger_sn": order.charger.sn_code if order.charger else "",
        "charger_name": get_order_charger_name(order),
        "vin": order.vin or (order.user.vin_code if order.user else None),
        "start_time": order.start_time.strftime("%Y-%m-%d %H:%M:%S") if order.start_time else "",
        "end_time": order.end_time.strftime("%Y-%m-%d %H:%M:%S") if order.end_time else "",
        "charge_duration": duration,
        "charge_duration_text": f"{duration} 分钟",
        "charge_amount": float(order.charge_amount or 0),
        "electricity_fee": float(order.electricity_fee or 0),
        "ele_fee": float(order.electricity_fee or 0),
        "service_fee": float(order.service_fee or 0),
        "total_amount": float(order.total_amount or 0),
        "total_fee": float(order.total_amount or 0),
        "pay_status": order.pay_status,
        "pay_status_label": PAY_STATUS_LABELS.get(order.pay_status, "unknown"),
        "pay_status_text": PAY_STATUS_TEXTS.get(order.pay_status, "未知"),
        "order_status": ORDER_STATUS_LABELS.get(order.status, "unknown"),
        "status": order.status,
        "order_status_code": order.status,
        "status_text": ORDER_STATUS_TEXTS.get(order.status, "未知状态"),
        "source_type": order.source_type or "mini_program",
        "source_type_text": get_order_source_text(order.source_type),
        "abnormal_reason": order.abnormal_reason,
        "settlement_status": order.settle_status,
        "settlement_status_label": SETTLEMENT_STATUS_LABELS.get(order.settle_status, "unknown"),
        "price_template_name": order.station.price_template.name if order.station and order.station.price_template else "",
        "fee_detail": _build_fee_detail(order),
        "status_flow": _build_status_flow(order),
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else "",
        "updated_at": order.updated_at.strftime("%Y-%m-%d %H:%M:%S") if order.updated_at else "",
    }


def _build_filtered_order_query(
    db: Session,
    *,
    operator_id: int | None = None,
    keyword: str | None = None,
    status: int | None = None,
    station_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    abnormal_reason: str | None = None,
    default_status: int | None = None,
):
    query = db.query(Order)

    if operator_id is not None:
        query = query.filter(Order.operator_id == operator_id)

    effective_status = status if status is not None else default_status
    if effective_status is not None:
        query = query.filter(Order.status == effective_status)

    if station_id is not None:
        query = query.filter(Order.station_id == station_id)

    normalized_keyword = (keyword or "").strip()
    if normalized_keyword:
        search = f"%{normalized_keyword}%"
        query = (
            query.outerjoin(User, Order.user_id == User.id)
            .outerjoin(Station, Order.station_id == Station.id)
            .outerjoin(Charger, Order.charger_id == Charger.id)
        )
        query = query.filter(
            or_(
                Order.order_no.like(search),
                User.phone.like(search),
                User.nickname.like(search),
                Order.vin.like(search),
                Station.name.like(search),
                Charger.sn_code.like(search),
                Order.source_type.like(search),
            )
        )

    if abnormal_reason and abnormal_reason.strip():
        query = query.filter(Order.abnormal_reason.like(f"%{abnormal_reason.strip()}%"))

    start_value = _parse_date_text(start_date)
    if start_value:
        query = query.filter(Order.start_time >= start_value)

    end_value = _parse_date_text(end_date, end_of_day=True)
    if end_value:
        query = query.filter(Order.start_time < end_value)

    return query


def _build_order_summary(query, total: int) -> dict[str, Any]:
    summary_row = query.with_entities(
        func.coalesce(func.sum(Order.total_kwh), 0),
        func.coalesce(func.sum(Order.ele_fee), 0),
        func.coalesce(func.sum(Order.service_fee), 0),
        func.coalesce(func.sum(Order.total_fee), 0),
        func.coalesce(func.sum(case((Order.status == 0, 1), else_=0)), 0),
        func.coalesce(func.sum(case((Order.status == 1, 1), else_=0)), 0),
        func.coalesce(func.sum(case((Order.status == 2, 1), else_=0)), 0),
        func.count(func.distinct(Order.station_id)),
        func.count(func.distinct(Order.abnormal_reason)),
    ).one()

    return {
        "total_count": int(total),
        "total_charge_amount": float(_to_decimal(summary_row[0])),
        "total_ele_fee": float(_to_decimal(summary_row[1])),
        "total_service_fee": float(_to_decimal(summary_row[2])),
        "total_amount": float(_to_decimal(summary_row[3])),
        "charging_count": int(summary_row[4] or 0),
        "completed_count": int(summary_row[5] or 0),
        "abnormal_count": int(summary_row[6] or 0),
        "station_count": int(summary_row[7] or 0),
        "reason_count": int(summary_row[8] or 0),
    }


def _order_duration_minutes_from_row(row: Any) -> int:
    if row.charge_duration is not None:
        return row.charge_duration
    if row.start_time and row.end_time:
        return max(int((row.end_time - row.start_time).total_seconds() / 60), 0)
    if row.start_time and row.status == 0:
        return max(int((datetime.now() - row.start_time).total_seconds() / 60), 0)
    return 0


def _serialize_order_row(row: Any) -> dict[str, Any]:
    duration = _order_duration_minutes_from_row(row)
    user_phone = row.user_phone or ""
    user_nickname = row.user_nickname or (f"用户{str(user_phone)[-4:]}" if user_phone else "")
    charger_name = row.charger_name or (get_charger_name(row.charger_obj) if getattr(row, "charger_obj", None) else "")
    return {
        "id": row.id,
        "order_no": row.order_no,
        "user_id": row.user_id,
        "user_phone": user_phone,
        "user_nickname": user_nickname,
        "operator_id": row.operator_id,
        "operator_name": row.operator_name or "",
        "station_id": row.station_id,
        "station_name": row.station_name or "",
        "charger_id": row.charger_id,
        "charger_sn": row.charger_sn or "",
        "charger_name": charger_name,
        "vin": row.vin or row.user_vin_code,
        "start_time": row.start_time.strftime("%Y-%m-%d %H:%M:%S") if row.start_time else "",
        "end_time": row.end_time.strftime("%Y-%m-%d %H:%M:%S") if row.end_time else "",
        "charge_duration": duration,
        "charge_duration_text": f"{duration} 分钟",
        "charge_amount": float(row.total_kwh or 0),
        "electricity_fee": float(row.ele_fee or 0),
        "ele_fee": float(row.ele_fee or 0),
        "service_fee": float(row.service_fee or 0),
        "total_amount": float(row.total_fee or 0),
        "total_fee": float(row.total_fee or 0),
        "pay_status": row.pay_status,
        "pay_status_label": PAY_STATUS_LABELS.get(row.pay_status, "unknown"),
        "pay_status_text": PAY_STATUS_TEXTS.get(row.pay_status, "未知"),
        "order_status": ORDER_STATUS_LABELS.get(row.status, "unknown"),
        "status": row.status,
        "order_status_code": row.status,
        "status_text": ORDER_STATUS_TEXTS.get(row.status, "未知状态"),
        "source_type": row.source_type or "mini_program",
        "source_type_text": get_order_source_text(row.source_type),
        "abnormal_reason": row.abnormal_reason,
        "settlement_status": row.settle_status,
        "settlement_status_label": SETTLEMENT_STATUS_LABELS.get(row.settle_status, "unknown"),
        "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else "",
        "updated_at": row.updated_at.strftime("%Y-%m-%d %H:%M:%S") if row.updated_at else "",
    }


def _load_order_rows_by_ids(db: Session, order_ids: list[int]) -> list[dict[str, Any]]:
    if not order_ids:
        return []

    rows = (
        db.query(
            Order.id,
            Order.order_no,
            Order.user_id,
            Order.operator_id,
            Order.station_id,
            Order.charger_id,
            Order.vin,
            Order.start_time,
            Order.end_time,
            Order.charge_duration,
            Order.total_kwh,
            Order.ele_fee,
            Order.service_fee,
            Order.total_fee,
            Order.source_type,
            Order.pay_status,
            Order.status,
            Order.abnormal_reason,
            Order.settle_status,
            Order.created_at,
            Order.updated_at,
            User.phone.label("user_phone"),
            User.nickname.label("user_nickname"),
            User.vin_code.label("user_vin_code"),
            Operator.name.label("operator_name"),
            Station.name.label("station_name"),
            Charger.sn_code.label("charger_sn"),
            Charger.name.label("charger_name"),
        )
        .select_from(Order)
        .outerjoin(User, Order.user_id == User.id)
        .outerjoin(Operator, Order.operator_id == Operator.id)
        .outerjoin(Station, Order.station_id == Station.id)
        .outerjoin(Charger, Order.charger_id == Charger.id)
        .filter(Order.id.in_(order_ids))
        .all()
    )

    row_map = {row.id: _serialize_order_row(row) for row in rows}
    return [row_map[item_id] for item_id in order_ids if item_id in row_map]


def get_order_page(
    db: Session,
    *,
    operator_id: int | None = None,
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    status: int | None = None,
    station_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    abnormal_reason: str | None = None,
    default_status: int | None = None,
) -> dict[str, Any]:
    safe_page, safe_page_size = _normalize_page(page, page_size)
    filtered_query = _build_filtered_order_query(
        db,
        operator_id=operator_id,
        keyword=keyword,
        status=status,
        station_id=station_id,
        start_date=start_date,
        end_date=end_date,
        abnormal_reason=abnormal_reason,
        default_status=default_status,
    )

    total = filtered_query.with_entities(func.count(Order.id)).order_by(None).scalar() or 0
    summary = _build_order_summary(filtered_query.order_by(None), total)

    effective_status = status if status is not None else default_status
    if effective_status == 0:
        order_column = Order.start_time.desc()
    elif effective_status in {1, 2}:
        order_column = Order.end_time.desc()
    else:
        order_column = Order.updated_at.desc()

    order_ids = [
        item[0]
        for item in (
            filtered_query.with_entities(Order.id)
            .order_by(order_column, Order.id.desc())
            .offset((safe_page - 1) * safe_page_size)
            .limit(safe_page_size)
            .all()
        )
    ]
    items = _load_order_rows_by_ids(db, order_ids)

    return {
        "items": items,
        "total": int(total),
        "page": safe_page,
        "page_size": safe_page_size,
        "summary": summary,
    }


def get_all_order_list(db: Session, limit: int = 100, operator_id: int | None = None) -> list[dict[str, Any]]:
    return get_order_page(db, operator_id=operator_id, page=1, page_size=limit)["items"]


def get_realtime_order_list(db: Session, limit: int = 50, operator_id: int | None = None) -> list[dict[str, Any]]:
    return get_order_page(db, operator_id=operator_id, page=1, page_size=limit, default_status=0)["items"]


def get_history_order_list(db: Session, limit: int = 100, operator_id: int | None = None) -> list[dict[str, Any]]:
    return get_order_page(db, operator_id=operator_id, page=1, page_size=limit, default_status=1)["items"]


def get_abnormal_order_list(db: Session, limit: int = 50, operator_id: int | None = None) -> list[dict[str, Any]]:
    return get_order_page(db, operator_id=operator_id, page=1, page_size=limit, default_status=2)["items"]


def get_order_detail_data(db: Session, order_id: int, operator_id: int | None = None) -> dict[str, Any] | None:
    query = (
        db.query(Order)
        .options(
            joinedload(Order.user),
            joinedload(Order.operator),
            joinedload(Order.station).joinedload(Station.price_template),
            joinedload(Order.charger).joinedload(Charger.station),
        )
        .filter(Order.id == order_id)
    )
    if operator_id is not None:
        query = query.filter(Order.operator_id == operator_id)

    order = query.first()
    if not order:
        return None
    return serialize_order(order)


def force_stop_order(db: Session, order_id: int, operator_id: int | None = None) -> Order | None:
    query = db.query(Order).options(
        joinedload(Order.user),
        joinedload(Order.station).joinedload(Station.price_template),
        joinedload(Order.charger),
    )
    query = query.filter(Order.id == order_id)
    if operator_id is not None:
        query = query.filter(Order.operator_id == operator_id)

    order = query.first()
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
    query = db.query(Order).options(
        joinedload(Order.user),
        joinedload(Order.station).joinedload(Station.price_template),
        joinedload(Order.charger),
    )
    query = query.filter(Order.id == order_id)
    if operator_id is not None:
        query = query.filter(Order.operator_id == operator_id)

    order = query.first()
    if not order or order.status != 0:
        return None

    now = datetime.now()
    order.end_time = now
    recalculate_order_amounts(order, now=now)
    order.status = 2
    order.abnormal_reason = abnormal_reason.strip() or "设备或会话异常，订单已转入异常列表"
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

    query = db.query(Order).filter(Order.start_time >= today_start, Order.start_time < today_end)
    if operator_id is not None:
        query = query.filter(Order.operator_id == operator_id)

    summary = query.with_entities(
        func.coalesce(func.sum(case((Order.status == 0, 1), else_=0)), 0),
        func.coalesce(func.sum(case((Order.status == 1, 1), else_=0)), 0),
        func.coalesce(func.sum(case((Order.status == 2, 1), else_=0)), 0),
        func.coalesce(func.sum(Order.total_kwh), 0),
        func.coalesce(func.sum(Order.total_fee), 0),
    ).one()

    return {
        "charging_count": int(summary[0] or 0),
        "today_completed_count": int(summary[1] or 0),
        "abnormal_count": int(summary[2] or 0),
        "today_charge_amount": float(_to_decimal(summary[3])),
        "today_total_amount": float(_to_decimal(summary[4])),
    }
