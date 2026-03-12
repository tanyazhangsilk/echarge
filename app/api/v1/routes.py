import logging
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.models.models import Order, Station, Charger, User, SettlementRecord
from app.services.settlement_service import settle_t_plus_1

api_router = APIRouter()
logger = logging.getLogger(__name__)

@api_router.get("/health", tags=["system"])
async def health_check() -> dict:
    return {"status": "ok"}

@api_router.get("/overview/summary", tags=["overview"])
async def get_overview_summary(db: Session = Depends(get_db)) -> dict:
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)

    today_orders_count = db.query(func.count(Order.id)).filter(Order.start_time >= today_start).scalar()
    yesterday_orders_count = db.query(func.count(Order.id)).filter(
        Order.start_time >= yesterday_start, 
        Order.start_time < today_start
    ).scalar()
    today_orders_change = 0
    if yesterday_orders_count > 0:
        today_orders_change = round((today_orders_count - yesterday_orders_count) / yesterday_orders_count * 100, 1)

    today_revenue = db.query(func.sum(Order.total_fee)).filter(Order.start_time >= today_start).scalar() or 0
    yesterday_revenue = db.query(func.sum(Order.total_fee)).filter(
        Order.start_time >= yesterday_start, 
        Order.start_time < today_start
    ).scalar() or 0
    today_revenue_change = 0
    if yesterday_revenue > 0:
        today_revenue_change = round((float(today_revenue) - float(yesterday_revenue)) / float(yesterday_revenue) * 100, 1)

    online_piles = db.query(func.count(Charger.id)).filter(Charger.status != 2).scalar()
    total_piles = db.query(func.count(Charger.id)).scalar()
    pile_availability = round(online_piles / total_piles * 100, 1) if total_piles > 0 else 0

    active_users = db.query(func.count(func.distinct(Order.user_id))).scalar()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_month = db.query(func.count(User.id)).filter(User.created_at >= month_start).scalar()

    return {
        "today_orders": today_orders_count,
        "today_orders_change": today_orders_change,
        "today_revenue": float(today_revenue),
        "today_revenue_change": today_revenue_change,
        "online_piles": online_piles,
        "total_piles": total_piles,
        "pile_availability": pile_availability,
        "active_users": active_users,
        "new_users_month": new_users_month,
    }

@api_router.get("/overview/realtime-orders", tags=["overview"])
async def get_realtime_orders(db: Session = Depends(get_db)) -> list[dict]:
    realtime_orders = db.query(Order).filter(Order.status == 0).limit(5).all()
    result = []
    for order in realtime_orders:
        result.append({
            "user_name": order.user.nickname,
            "station_name": order.charger.station.name,
            "charged_kwh": float(order.total_kwh),
            "status": "charging"
        })
    return result

class ManualSettleRequest(BaseModel):
    date: date

@api_router.post("/settlements/manual_settle", tags=["settlements"])
async def manual_settle(payload: ManualSettleRequest, db: Session = Depends(get_db)) -> dict:
    try:
        processed = settle_t_plus_1(payload.date, db=db)
        logger.info("manual_settle", extra={"date": str(payload.date), "processed": processed})
        return {"code": 0, "processed": processed}
    except Exception as e:
        logger.exception("manual_settle_failed", extra={"date": str(payload.date)})
        return {"code": 1, "processed": 0, "message": str(e)}

@api_router.get("/finance/settlements", tags=["finance"])
async def get_settlements(db: Session = Depends(get_db)):
    records = db.query(SettlementRecord).order_by(SettlementRecord.settle_date.desc()).all()
    result = []
    for r in records:
        result.append({
            "settle_date": str(r.settle_date),
            "order_count": r.order_count,
            "total_amount": float(r.total_amount),
            "platform_fee": float(r.platform_fee),
            "settle_amount": float(r.settle_amount),
            "status": r.status
        })
    return {"code": 200, "data": result}


@api_router.post("/finance/settle", tags=["finance"])
async def trigger_settle(db: Session = Depends(get_db)):
    target = date.today() - timedelta(days=1)
    try:
        processed = settle_t_plus_1(target, db=db)
        return {"code": 200, "message": f"清分完成，处理 {processed} 笔订单", "processed": processed}
    except Exception as e:
        logger.exception("finance_settle_failed", extra={"date": str(target)})
        return {"code": 500, "message": f"清分失败: {str(e)}", "processed": 0}
