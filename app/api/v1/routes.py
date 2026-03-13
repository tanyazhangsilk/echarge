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


@api_router.get("/orders/realtime", tags=["orders"])
async def get_realtime_orders(db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    # 查询 status = 0 (进行中) 的订单，按时间倒序
    orders = db.query(Order).options(
        joinedload(Order.user), joinedload(Order.charger)
    ).filter(Order.status == 0).order_by(Order.start_time.desc()).limit(50).all()
    
    return {
        "code": 200,
        "data": [{
            "order_no": o.order_no,
            "user_phone": o.user.phone if o.user else "未知用户",
            "charger_sn": o.charger.sn_code if o.charger else "未知设备",
            "start_time": o.start_time.strftime("%Y-%m-%d %H:%M:%S") if o.start_time else "",
            "total_kwh": float(o.total_kwh),
            "total_fee": float(o.total_fee),
            "duration_mins": int((datetime.now() - o.start_time).total_seconds() / 60) if o.start_time else 0
        } for o in orders]
    }

@api_router.get("/orders/abnormal", tags=["orders"])
async def get_abnormal_orders(db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    import random
    # 查询 status = 2 (异常) 的订单
    orders = db.query(Order).options(
        joinedload(Order.user), joinedload(Order.charger)
    ).filter(Order.status == 2).order_by(Order.start_time.desc()).limit(50).all()
    
    # 模拟几种常见的异常原因
    error_types = ["设备离线断电", "用户账户余额不足", "枪头温度过高保护", "通讯心跳超时", "结算扣款失败"]
    
    return {
        "code": 200,
        "data": [{
            "order_no": o.order_no,
            "user_phone": o.user.phone if o.user else "未知",
            "charger_sn": o.charger.sn_code if o.charger else "未知",
            "start_time": o.start_time.strftime("%Y-%m-%d %H:%M:%S") if o.start_time else "",
            "total_fee": float(o.total_fee),
            "error_reason": random.choice(error_types), # 随机分配异常原因展示
            "handle_status": 0 # 0-未处理, 1-已处理
        } for o in orders]
    }


@api_router.get("/finance/invoices", tags=["finance"])
async def get_invoices(db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    from app.models.models import Invoice
    
    # 联表查询发票与对应的申请用户，按时间倒序
    invoices = db.query(Invoice).options(joinedload(Invoice.user)).order_by(Invoice.created_at.desc()).all()
    
    return {
        "code": 200,
        "data": [{
            "id": inv.id,
            "invoice_no": f"INV{inv.created_at.strftime('%Y%m%d')}{str(inv.id).zfill(4)}",
            "user_phone": inv.user.phone if inv.user else "未知用户",
            "amount": float(inv.amount),
            "email": inv.email,
            "status": inv.status,
            "created_at": inv.created_at.strftime("%Y-%m-%d %H:%M:%S") if inv.created_at else "",
            "file_url": inv.file_url
        } for inv in invoices]
    }

@api_router.post("/finance/invoices/{invoice_id}/process", tags=["finance"])
async def process_invoice(invoice_id: int, payload: dict, db: Session = Depends(get_db)):
    from app.models.models import Invoice
    
    action = payload.get("action") # 'approve' 或 'reject'
    file_url = payload.get("file_url", "")
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        return {"code": 404, "message": "发票申请不存在"}
        
    if action == "approve":
        invoice.status = 1
        invoice.file_url = file_url
    elif action == "reject":
        invoice.status = 2
        
    db.commit()
    return {"code": 200, "message": "处理成功"}