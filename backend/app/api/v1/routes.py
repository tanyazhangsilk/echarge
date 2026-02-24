from fastapi import APIRouter


api_router = APIRouter()


@api_router.get("/health", tags=["system"])
async def health_check() -> dict:
    return {"status": "ok"}


@api_router.get("/overview/summary", tags=["overview"])
async def get_overview_summary() -> dict:
    """
    Overview cards data for dashboard, aligned with the prototype.
    """
    return {
        "today_orders": 145,
        "today_orders_change": 12.5,
        "today_revenue": 12580,
        "today_revenue_change": 8.2,
        "online_piles": 89,
        "total_piles": 102,
        "pile_availability": 87.3,
        "active_users": 2845,
        "new_users_month": 201,
    }


@api_router.get("/overview/realtime-orders", tags=["overview"])
async def get_realtime_orders() -> list[dict]:
    """
    Mock realtime charging orders list for dashboard table.
    """
    return [
        {
            "user_name": "张三",
            "station_name": "中心广场充电站",
            "charged_kwh": 45,
            "status": "charging",
        },
        {
            "user_name": "李四",
            "station_name": "商业区充电站",
            "charged_kwh": 32,
            "status": "charging",
        },
        {
            "user_name": "王五",
            "station_name": "工业园充电站",
            "charged_kwh": 68,
            "status": "charging",
        },
    ]

