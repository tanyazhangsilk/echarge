from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.models import Charger, Order


def _order_query(db: Session):
    return db.query(Order).options(
        joinedload(Order.user),
        joinedload(Order.operator),
        joinedload(Order.station),
        joinedload(Order.charger).joinedload(Charger.station),
    )


def list_realtime_orders(db: Session, limit: int = 50) -> list[Order]:
    return (
        _order_query(db)
        .filter(Order.status == 0)
        .order_by(Order.start_time.desc())
        .limit(limit)
        .all()
    )


def list_history_orders(db: Session, limit: int = 100) -> list[Order]:
    return (
        _order_query(db)
        .filter(Order.status.in_([1, 2]))
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )


def list_abnormal_orders(db: Session, limit: int = 50) -> list[Order]:
    return (
        _order_query(db)
        .filter(Order.status == 2)
        .order_by(Order.start_time.desc())
        .limit(limit)
        .all()
    )


def get_order_by_id(db: Session, order_id: int) -> Order | None:
    return _order_query(db).filter(Order.id == order_id).first()


def count_charging_orders(db: Session) -> int:
    return db.query(func.count(Order.id)).filter(Order.status == 0).scalar() or 0


def count_abnormal_orders(db: Session) -> int:
    return db.query(func.count(Order.id)).filter(Order.status == 2).scalar() or 0


def count_today_completed_orders(db: Session, today_start: datetime, today_end: datetime) -> int:
    return (
        db.query(func.count(Order.id))
        .filter(Order.status == 1, Order.end_time >= today_start, Order.end_time < today_end)
        .scalar()
        or 0
    )


def sum_today_charge_amount(db: Session, today_start: datetime, today_end: datetime) -> Decimal:
    value = (
        db.query(func.coalesce(func.sum(Order.total_kwh), 0))
        .filter(Order.status == 1, Order.end_time >= today_start, Order.end_time < today_end)
        .scalar()
    )
    return Decimal(str(value or 0))


def sum_today_total_amount(db: Session, today_start: datetime, today_end: datetime) -> Decimal:
    value = (
        db.query(func.coalesce(func.sum(Order.total_fee), 0))
        .filter(Order.status == 1, Order.end_time >= today_start, Order.end_time < today_end)
        .scalar()
    )
    return Decimal(str(value or 0))
