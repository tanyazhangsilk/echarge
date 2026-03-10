from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.db.database import get_db
from backend.app.models.models import Order, Station, Charger, User
from datetime import datetime, timedelta


api_router = APIRouter()


@api_router.get("/health", tags=["system"])
async def health_check() -> dict:
    return {"status": "ok"}


@api_router.get("/overview/summary", tags=["overview"])
async def get_overview_summary(db: Session = Depends(get_db)) -> dict:
    """
    Overview cards data for dashboard, aligned with the prototype.
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)

    # 今日订单数
    today_orders_count = db.query(func.count(Order.id)).filter(Order.start_time >= today_start).scalar()
    # 昨日订单数
    yesterday_orders_count = db.query(func.count(Order.id)).filter(
        Order.start_time >= yesterday_start, 
        Order.start_time < today_start
    ).scalar()
    
    # 订单变化率
    today_orders_change = 0
    if yesterday_orders_count > 0:
        today_orders_change = round((today_orders_count - yesterday_orders_count) / yesterday_orders_count * 100, 1)

    # 今日收益
    today_revenue = db.query(func.sum(Order.total_fee)).filter(Order.start_time >= today_start).scalar() or 0
    # 昨日收益
    yesterday_revenue = db.query(func.sum(Order.total_fee)).filter(
        Order.start_time >= yesterday_start, 
        Order.start_time < today_start
    ).scalar() or 0
    
    # 收益变化率
    today_revenue_change = 0
    if yesterday_revenue > 0:
        today_revenue_change = round((float(today_revenue) - float(yesterday_revenue)) / float(yesterday_revenue) * 100, 1)

    # 在线电桩 (这里简单定义 status != 2 为在线)
    online_piles = db.query(func.count(Charger.id)).filter(Charger.status != 2).scalar()
    total_piles = db.query(func.count(Charger.id)).scalar()
    pile_availability = round(online_piles / total_piles * 100, 1) if total_piles > 0 else 0

    # 活跃用户 (有订单的用户)
    active_users = db.query(func.count(func.distinct(Order.user_id))).scalar()
    
    # 本月新增用户
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
    """
    真正的实时订单接口！直接从 MySQL 数据库查询正在充电的订单。
    """
    # 1. 告诉数据库：去 Order 表里找，条件是 status == 0 (进行中)
    # 并且把关联的 user 和 charger(及其所在的 station) 一起带出来
    realtime_orders = db.query(Order).filter(Order.status == 0).limit(10).all()
    
    # 2. 把数据库查询出来的复杂对象，转换成前端 Vue 能看懂的简单字典
    result = []
    for order in realtime_orders:
        result.append({
            "user_name": order.user.nickname, # 刚刚 Faker 随机生成的人名
            "station_name": order.charger.station.name, # 随机生成的充电站名
            "charged_kwh": float(order.total_kwh), # 已经充了多少度电
            "status": "charging"
        })
        
    return result

