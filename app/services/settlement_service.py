from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.db.database import SessionLocal
from app.models.models import Order, SettlementRecord

logger = logging.getLogger(__name__)

PLATFORM_RATE = Decimal("0.10")

def settle_t_plus_1(target_date: date, db: Session | None = None) -> int:
    own_session = db is None
    if own_session:
        db = SessionLocal()

    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    try:
        exists = db.query(SettlementRecord.id).filter(SettlementRecord.settle_date == target_date).first()
        if exists:
            logger.info("settlement already exists", extra={"settle_date": str(target_date)})
            return 0

        unsettled_q = db.query(Order).filter(
            Order.status == 1,
            Order.settle_status == 0,
            Order.start_time >= day_start,
            Order.start_time < day_end,
        )

        order_ids = [row[0] for row in unsettled_q.with_entities(Order.id).all()]
        if not order_ids:
            logger.info("no unsettled orders", extra={"settle_date": str(target_date)})
            return 0

        order_count = len(order_ids)
        total_amount = db.query(func.coalesce(func.sum(Order.total_fee), 0)).filter(Order.id.in_(order_ids)).scalar()
        total_amount = Decimal(str(total_amount))
        platform_fee = (total_amount * PLATFORM_RATE).quantize(Decimal("0.01"))
        settle_amount = (total_amount - platform_fee).quantize(Decimal("0.01"))

        record = SettlementRecord(
            settle_date=target_date,
            order_count=order_count,
            total_amount=total_amount,
            platform_fee=platform_fee,
            settle_amount=settle_amount,
            status=0,
        )
        db.add(record)

        db.query(Order).filter(Order.id.in_(order_ids)).update(
            {"settle_status": 1},
            synchronize_session=False,
        )

        db.commit()
        logger.info(
            "settlement committed",
            extra={"settle_date": str(target_date), "processed": order_count},
        )
        return order_count
    except IntegrityError:
        db.rollback()
        logger.info("settlement unique conflict", extra={"settle_date": str(target_date)})
        return 0
    except Exception:
        db.rollback()
        logger.exception("settlement failed", extra={"settle_date": str(target_date)})
        raise
    finally:
        if own_session:
            db.close()

def execute_t_plus_1_settlement(db: Session, target_date: date = None):
    t_day = target_date if target_date else (date.today() - timedelta(days=1))
    try:
        processed = settle_t_plus_1(t_day, db=db)
        return {"status": "success", "msg": "清分完成", "processed_count": processed}
    except Exception as e:
        return {"status": "error", "msg": str(e), "processed_count": 0}
