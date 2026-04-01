import logging
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.db.database import get_db
from app.models.models import (
    Charger,
    Fleet,
    Operator,
    Order,
    PriceTemplate,
    SettlementRecord,
    Station,
    User,
)
from app.schemas import InvoiceApplySchema, InvoiceProcessSchema, OrderActionSchema
from app.services.order_service import (
    ORDER_STATUS_LABELS,
    get_abnormal_order_list,
    get_all_order_list,
    get_history_order_list,
    get_order_detail_data,
    get_order_stats,
    get_realtime_order_list,
    get_station_name,
    mark_order_abnormal,
    order_duration_minutes,
    serialize_order,
    force_stop_order,
)
from app.services.settlement_service import settle_t_plus_1
from app.services.wallet_service import get_wallet_summary, get_wallet_transaction_list

api_router = APIRouter()
logger = logging.getLogger(__name__)

operator_audit_store: dict[int, dict[str, Any]] = {}
marketing_audit_store: dict[int, dict[str, Any]] = {}
blacklist_store: set[int] = set()
system_param_store: dict[str, Any] = {
    "station_auto_publish": False,
    "invoice_auto_approve_limit": 300.0,
    "settlement_platform_rate": 10,
    "abnormal_order_sla_minutes": 30,
    "user_refund_limit_per_day": 2,
    "support_email": "support@echarge.com",
}
template_store: list[dict[str, Any]] = []
tag_store: list[dict[str, Any]] = []
discount_campaign_store: list[dict[str, Any]] = []
coupon_campaign_store: list[dict[str, Any]] = []


class TemplatePayload(BaseModel):
    name: str
    peak_price: float
    flat_price: float
    valley_price: float
    service_price: float
    scope: str
    status: str = "active"


class FleetPayload(BaseModel):
    name: str
    is_whitelist: bool = False


class TagPayload(BaseModel):
    name: str
    color: str = "#409EFF"
    description: str = ""


class CampaignPayload(BaseModel):
    name: str
    campaign_type: str
    discount_value: float
    threshold: float = 0
    audience: str = "all"
    status: str = "draft"


class CouponDispatchPayload(BaseModel):
    dispatch_count: int = 100


class SettingsProfilePayload(BaseModel):
    name: str
    org_type: str
    contact_email: str
    contact_phone: str
    bank_account: str = ""


class SystemParamsPayload(BaseModel):
    station_auto_publish: bool
    invoice_auto_approve_limit: float
    settlement_platform_rate: int
    abnormal_order_sla_minutes: int
    user_refund_limit_per_day: int
    support_email: str


class RoleContext(BaseModel):
    role: str
    operator_id: int | None = None


def _parse_operator_id(raw: Any) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, int):
        return raw
    value = str(raw).strip()
    if not value:
        return None
    if value.isdigit():
        return int(value)
    digits = "".join(ch for ch in value if ch.isdigit())
    if digits:
        return int(digits)
    return None


def get_current_operator(db: Session) -> Operator | None:
    return db.query(Operator).order_by(Operator.id.asc()).first()


def get_role_context(
    role: str | None = None,
    operator_id: int | None = None,
    x_role: str | None = Header(default=None, alias="x-role"),
    x_operator_id: str | None = Header(default=None, alias="x-operator-id"),
) -> RoleContext:
    resolved_role = (x_role or role or "operator").strip().lower()
    if resolved_role not in {"admin", "operator"}:
        resolved_role = "operator"

    resolved_operator_id = operator_id if operator_id is not None else _parse_operator_id(x_operator_id)

    if resolved_role == "operator":
        if resolved_operator_id is None:
            resolved_operator_id = 1
    return RoleContext(role=resolved_role, operator_id=resolved_operator_id)


def require_admin_context(context: RoleContext = Depends(get_role_context)) -> RoleContext:
    if context.role != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    return context


def require_operator_context(context: RoleContext = Depends(get_role_context)) -> RoleContext:
    if context.role != "operator":
        raise HTTPException(status_code=403, detail="operator role required")
    return context


def scoped_operator_id(context: RoleContext) -> int | None:
    return None if context.role == "admin" else context.operator_id


def user_display_name(user: User) -> str:
    return user.nickname or f"用户{str(user.phone)[-4:]}"


def seed_runtime_data(db: Session) -> None:
    operator = get_current_operator(db)
    operator_id = operator.id if operator else 0

    if not template_store:
      db_templates = db.query(PriceTemplate).filter(PriceTemplate.operator_id == operator_id).order_by(PriceTemplate.created_at.desc()).all()
      if db_templates:
        for item in db_templates:
          template_store.append({
              "id": item.id,
              "name": item.name,
              "peak_price": 1.82,
              "flat_price": 1.26,
              "valley_price": 0.68,
              "service_price": 0.8,
              "scope": "全站",
              "status": "active",
              "updated_at": item.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
          })
      else:
        template_store.extend([
            {
                "id": 1,
                "name": "城市快充标准模板",
                "peak_price": 1.88,
                "flat_price": 1.34,
                "valley_price": 0.76,
                "service_price": 0.8,
                "scope": "全站",
                "status": "active",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            {
                "id": 2,
                "name": "园区夜充模板",
                "peak_price": 1.56,
                "flat_price": 1.12,
                "valley_price": 0.58,
                "service_price": 0.65,
                "scope": "指定站点",
                "status": "draft",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        ])

    if not tag_store:
      tag_store.extend([
          {"id": 1, "name": "高频通勤", "color": "#409EFF", "description": "近30天充电6次以上", "user_count": 86},
          {"id": 2, "name": "夜间充电", "color": "#67C23A", "description": "夜间活跃用户", "user_count": 43},
          {"id": 3, "name": "待召回", "color": "#E6A23C", "description": "近14天未复购", "user_count": 27},
      ])

    if not discount_campaign_store:
      discount_campaign_store.extend([
          {
              "id": 1,
              "name": "工作日午间充电折扣",
              "campaign_type": "满减",
              "discount_value": 8.8,
              "threshold": 30,
              "audience": "企业车队",
              "status": "active",
              "redeem_count": 326,
              "conversion_rate": 24.5,
          },
          {
              "id": 2,
              "name": "新用户首充礼",
              "campaign_type": "立减",
              "discount_value": 12,
              "threshold": 0,
              "audience": "新用户",
              "status": "draft",
              "redeem_count": 0,
              "conversion_rate": 0,
          },
      ])

    if not coupon_campaign_store:
      coupon_campaign_store.extend([
          {"id": 1, "name": "春季园区通勤券", "discount_value": 10, "inventory": 1000, "dispatched": 640, "used": 381, "status": "active"},
          {"id": 2, "name": "夜充满减券", "discount_value": 15, "inventory": 500, "dispatched": 120, "used": 39, "status": "paused"},
      ])

    operators = db.query(Operator).order_by(Operator.created_at.desc()).all()
    if not operator_audit_store:
      for item in operators:
        operator_audit_store[item.id] = {
            "status": "approved" if item.is_verified else "pending",
            "remark": "",
            "contact_email": f"bd{item.id}@echarge.com",
            "contact_phone": f"1380000{str(item.id).zfill(4)}",
        }

    if not marketing_audit_store:
      for item in discount_campaign_store:
        marketing_audit_store[item["id"]] = {
            "status": "approved" if item["status"] == "active" else "pending",
            "remark": "",
        }

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
    realtime_orders = (
        db.query(Order)
        .options(joinedload(Order.user), joinedload(Order.station), joinedload(Order.charger).joinedload(Charger.station))
        .filter(Order.status == 0)
        .order_by(Order.start_time.desc())
        .limit(5)
        .all()
    )
    return [
        {
            "id": order.id,
            "order_no": order.order_no,
            "user_name": user_display_name(order.user) if order.user else "",
            "station_name": get_station_name(order),
            "charged_kwh": float(order.charge_amount),
            "charge_duration": order_duration_minutes(order),
            "status": ORDER_STATUS_LABELS.get(order.status, "unknown"),
        }
        for order in realtime_orders
    ]

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


@api_router.get("/orders/all", tags=["orders"])
async def get_orders_all(
    context: RoleContext = Depends(get_role_context),
    db: Session = Depends(get_db),
):
    return {
        "code": 200,
        "data": get_all_order_list(db, limit=200, operator_id=scoped_operator_id(context)),
    }


@api_router.get("/orders/realtime", tags=["orders"])
async def get_orders_realtime_api(
    context: RoleContext = Depends(get_role_context),
    db: Session = Depends(get_db),
):
    return {
        "code": 200,
        "data": get_realtime_order_list(db, limit=50, operator_id=scoped_operator_id(context)),
    }


@api_router.get("/orders/abnormal", tags=["orders"])
async def get_orders_abnormal_api(
    context: RoleContext = Depends(get_role_context),
    db: Session = Depends(get_db),
):
    return {
        "code": 200,
        "data": get_abnormal_order_list(db, limit=50, operator_id=scoped_operator_id(context)),
    }


@api_router.get("/orders/history", tags=["orders"])
async def get_orders_history_api(
    context: RoleContext = Depends(get_role_context),
    db: Session = Depends(get_db),
):
    return {
        "code": 200,
        "data": get_history_order_list(db, limit=100, operator_id=scoped_operator_id(context)),
    }


@api_router.get("/orders/stats", tags=["orders"])
async def get_order_stats_api(
    context: RoleContext = Depends(get_role_context),
    db: Session = Depends(get_db),
):
    return {
        "code": 200,
        "data": get_order_stats(db, operator_id=scoped_operator_id(context)),
    }


@api_router.get("/wallet/summary", tags=["wallet"])
async def get_wallet_summary_api(user_id: int = 1, db: Session = Depends(get_db)):
    return {
        "code": 200,
        "data": get_wallet_summary(db, user_id=user_id, limit=10),
    }


@api_router.get("/wallet/transactions", tags=["wallet"])
async def get_wallet_transactions_api(user_id: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    return {
        "code": 200,
        "data": get_wallet_transaction_list(db, user_id=user_id, limit=limit),
    }


@api_router.get("/orders/{order_id}", tags=["orders"])
async def get_order_detail(
    order_id: int,
    context: RoleContext = Depends(get_role_context),
    db: Session = Depends(get_db),
):
    order_data = get_order_detail_data(db, order_id, operator_id=scoped_operator_id(context))
    if not order_data:
        return {"code": 404, "message": "订单不存在或无权限访问"}

    return {
        "code": 200,
        "data": order_data,
    }


@api_router.post("/orders/{order_id}/force-stop", tags=["orders"])
async def force_stop_order_api(
    order_id: int,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    order = force_stop_order(db, order_id, operator_id=context.operator_id)
    if not order:
        return {"code": 400, "message": "订单不存在、无权限或当前不是充电中状态"}

    return {
        "code": 200,
        "message": "订单已强制停止",
        "data": serialize_order(order),
    }


@api_router.post("/orders/{order_id}/mark-abnormal", tags=["orders"])
async def mark_order_abnormal_api(
    order_id: int,
    payload: OrderActionSchema,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    order = mark_order_abnormal(db, order_id, payload.abnormal_reason, operator_id=context.operator_id)
    if not order:
        return {"code": 400, "message": "订单不存在、无权限或当前不是充电中状态"}

    return {
        "code": 200,
        "message": "订单已标记异常",
        "data": serialize_order(order),
    }


@api_router.get("/admin/orders", tags=["orders", "admin"])
async def get_admin_orders(
    _context: RoleContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    return {"code": 200, "data": get_all_order_list(db, limit=200)}


@api_router.get("/admin/orders/abnormal", tags=["orders", "admin"])
async def get_admin_abnormal_orders(
    _context: RoleContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    return {"code": 200, "data": get_abnormal_order_list(db, limit=200)}


@api_router.get("/admin/orders/{order_id}", tags=["orders", "admin"])
async def get_admin_order_detail(
    order_id: int,
    _context: RoleContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    order_data = get_order_detail_data(db, order_id)
    if not order_data:
        return {"code": 404, "message": "订单不存在"}
    return {"code": 200, "data": order_data}


@api_router.get("/operator/orders/history", tags=["orders", "operator"])
async def get_operator_history_orders(
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    return {"code": 200, "data": get_history_order_list(db, limit=100, operator_id=context.operator_id)}


@api_router.get("/operator/orders/realtime", tags=["orders", "operator"])
async def get_operator_realtime_orders(
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    return {"code": 200, "data": get_realtime_order_list(db, limit=100, operator_id=context.operator_id)}


@api_router.get("/operator/orders/abnormal", tags=["orders", "operator"])
async def get_operator_abnormal_orders(
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    return {"code": 200, "data": get_abnormal_order_list(db, limit=100, operator_id=context.operator_id)}


@api_router.get("/operator/orders/{order_id}", tags=["orders", "operator"])
async def get_operator_order_detail(
    order_id: int,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    order_data = get_order_detail_data(db, order_id, operator_id=context.operator_id)
    if not order_data:
        return {"code": 404, "message": "订单不存在或无权限访问"}
    return {"code": 200, "data": order_data}


@api_router.post("/operator/orders/{order_id}/force-stop", tags=["orders", "operator"])
async def operator_force_stop_order(
    order_id: int,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    order = force_stop_order(db, order_id, operator_id=context.operator_id)
    if not order:
        return {"code": 400, "message": "订单不存在、无权限或当前不是充电中状态"}
    return {"code": 200, "message": "订单已强制停止", "data": serialize_order(order)}


@api_router.post("/operator/orders/{order_id}/mark-abnormal", tags=["orders", "operator"])
async def operator_mark_order_abnormal(
    order_id: int,
    payload: OrderActionSchema,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    order = mark_order_abnormal(db, order_id, payload.abnormal_reason, operator_id=context.operator_id)
    if not order:
        return {"code": 400, "message": "订单不存在、无权限或当前不是充电中状态"}
    return {"code": 200, "message": "订单已标记异常", "data": serialize_order(order)}




@api_router.get("/finance/invoices", tags=["finance"])
async def get_invoices(db: Session = Depends(get_db)):
    from app.models.models import Invoice
    
    invoices = (
        db.query(Invoice)
        .options(joinedload(Invoice.user), joinedload(Invoice.related_order))
        .order_by(Invoice.created_at.desc())
        .all()
    )
    
    return {
        "code": 200,
        "data": [{
            "id": inv.id,
            "invoice_no": f"INV{inv.created_at.strftime('%Y%m%d')}{str(inv.id).zfill(4)}",
            "user_phone": inv.user.phone if inv.user else "未知用户",
            "user_id": inv.user_id,
            "order_id": inv.order_id,
            "order_no": inv.related_order.order_no if inv.related_order else None,
            "invoice_title": inv.invoice_title,
            "amount": float(inv.amount),
            "email": inv.email,
            "status": inv.status,
            "created_at": inv.created_at.strftime("%Y-%m-%d %H:%M:%S") if inv.created_at else "",
            "uploaded_at": inv.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if inv.uploaded_at else None,
            "file_url": inv.file_url,
            "remark": inv.remark,
        } for inv in invoices]
    }

@api_router.post("/finance/invoices/apply", tags=["finance"])
async def apply_invoice(payload: InvoiceApplySchema, db: Session = Depends(get_db)):
    from app.models.models import Invoice

    invoice = Invoice(
        user_id=payload.user_id,
        operator_id=payload.operator_id,
        order_id=payload.order_id,
        invoice_title=payload.invoice_title,
        amount=payload.amount,
        email=payload.email,
        status=0,
        remark=payload.remark or None,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return {
        "code": 200,
        "message": "发票申请已提交",
        "data": {"id": invoice.id},
    }

@api_router.get("/finance/invoices/{invoice_id}", tags=["finance"])
async def get_invoice_detail(invoice_id: int, db: Session = Depends(get_db)):
    from app.models.models import Invoice

    inv = (
        db.query(Invoice)
        .options(joinedload(Invoice.user), joinedload(Invoice.operator), joinedload(Invoice.related_order))
        .filter(Invoice.id == invoice_id)
        .first()
    )
    if not inv:
        return {"code": 404, "message": "发票申请不存在"}

    return {
        "code": 200,
        "data": {
            "id": inv.id,
            "invoice_no": f"INV{inv.created_at.strftime('%Y%m%d')}{str(inv.id).zfill(4)}",
            "user_id": inv.user_id,
            "user_phone": inv.user.phone if inv.user else "",
            "operator_id": inv.operator_id,
            "order_id": inv.order_id,
            "order_no": inv.related_order.order_no if inv.related_order else None,
            "invoice_title": inv.invoice_title,
            "amount": float(inv.amount),
            "email": inv.email,
            "status": inv.status,
            "file_url": inv.file_url,
            "remark": inv.remark,
            "created_at": inv.created_at.strftime("%Y-%m-%d %H:%M:%S") if inv.created_at else "",
            "uploaded_at": inv.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if inv.uploaded_at else None,
            "updated_at": inv.updated_at.strftime("%Y-%m-%d %H:%M:%S") if inv.updated_at else "",
        },
    }

@api_router.post("/finance/invoices/{invoice_id}/process", tags=["finance"])
async def process_invoice(invoice_id: int, payload: InvoiceProcessSchema, db: Session = Depends(get_db)):
    from app.models.models import Invoice
    from datetime import datetime
    
    action = payload.action
    file_url = payload.file_url
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        return {"code": 404, "message": "发票申请不存在"}
        
    if action == "approve":
        invoice.status = 1
        invoice.file_url = file_url
        invoice.uploaded_at = datetime.now()
        invoice.remark = payload.remark or invoice.remark
    elif action == "reject":
        invoice.status = 2
        invoice.remark = payload.remark or invoice.remark
        
    db.commit()
    return {"code": 200, "message": "处理成功"}

@api_router.get("/admin/finance/settlements", tags=["admin"])
async def admin_get_settlements(db: Session = Depends(get_db)):
    """管理员获取全网历史清分记录"""
    from app.models.models import SettlementRecord
    
    # 按照清分日期倒序排列
    records = db.query(SettlementRecord).order_by(SettlementRecord.settle_date.desc()).all()
    
    return {
        "code": 200,
        "data": [
            {
                "id": r.id,
                "settle_date": str(r.settle_date),
                "order_count": r.order_count,
                "total_amount": float(r.total_amount),
                "platform_fee": float(r.platform_fee),
                "settle_amount": float(r.settle_amount),
                "status": r.status
            } for r in records
        ]
    }

@api_router.post("/admin/finance/settle", tags=["admin"])
async def admin_trigger_settle(payload: dict, db: Session = Depends(get_db)):
    """管理员手动触发某日的全局清分"""
    from app.services.settlement_service import settle_t_plus_1
    from datetime import datetime, timedelta
    
    target_date_str = payload.get("date")
    if target_date_str:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    else:
        # 默认清分昨天
        target_date = datetime.now().date() - timedelta(days=1)
        
    try:
        # 调用你之前写好的真实清分引擎
        processed = settle_t_plus_1(target_date, db=db)
        if processed == 0:
            return {"code": 200, "message": f"{target_date} 没有需要清分的已完成订单", "processed": 0}
            
        return {"code": 200, "message": f"清分成功！共处理全网 {processed} 笔订单", "processed": processed}
    except Exception as e:
        return {"code": 500, "message": f"清分引擎执行失败: {str(e)}"}


@api_router.get("/admin/audit/stations", tags=["admin"])
async def get_station_audits(db: Session = Depends(get_db)):
    """获取待审核与已驳回的电站列表"""
    from sqlalchemy.orm import joinedload
    from app.models.models import Station
    import random
    
    # 查询状态为 3(待审核) 和 4(已驳回) 的电站
    stations = db.query(Station).options(joinedload(Station.operator)).filter(
        Station.status.in_([3, 4])
    ).order_by(Station.created_at.desc()).all()
    
    return {
        "code": 200,
        "data": [{
            "id": s.id,
            "operator_name": s.operator.name if s.operator else "未知运营商",
            "station_name": s.name,
            "lng": float(s.longitude),
            "lat": float(s.latitude),
            "status": s.status,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else "",
            # 以下为丰富前端展示的模拟扩展字段 (现实中应该存在 Station 扩展表里)
            "planned_piles": (s.id % 20) + 5,
            "total_power": ((s.id % 20) + 5) * 120,
            "address": f"深圳市某某区{s.name}附近"
        } for s in stations]
    }

@api_router.post("/admin/audit/stations/{station_id}/process", tags=["admin"])
async def process_station_audit(station_id: int, payload: dict, db: Session = Depends(get_db)):
    """处理电站审核 (通过/驳回)"""
    from app.models.models import Station
    
    action = payload.get("action") # 'approve' or 'reject'
    remark = payload.get("remark", "")
    
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        return {"code": 404, "message": "电站不存在"}
        
    if action == "approve":
        station.status = 0 # 0 表示正式运营中
        station.visibility = "public" # 审核通过，对 C 端公开可见
    elif action == "reject":
        station.status = 4 # 4 表示被驳回
        
    db.commit()
    return {"code": 200, "message": "电站审核处理成功"}

@api_router.post("/operator/stations/apply", tags=["operator"])
async def operator_apply_station(payload: dict, db: Session = Depends(get_db)):
    """运营商提交新建电站申请"""
    from app.models.models import Station, Operator
    
    # 模拟获取当前登录的运营商 (真实情况应从 Token 中解析)
    operator = db.query(Operator).first()
    if not operator:
        return {"code": 404, "message": "当前运营商未找到，请先入驻"}
        
    try:
        new_station = Station(
            operator_id=operator.id,
            name=payload.get("name"),
            # 真实业务中经纬度由前端地图组件选点获取，这里用传入值
            longitude=payload.get("lng", 114.0), 
            latitude=payload.get("lat", 22.5),
            status=3,  # 核心：3 代表“待审核”
            visibility="private" # 未过审前，C端不可见
        )
        db.add(new_station)
        db.commit()
        db.refresh(new_station)
        
        return {"code": 200, "message": "电站资料提交成功，已进入平台审核队列", "station_id": new_station.id}
    except Exception as e:
        db.rollback()
        return {"code": 500, "message": f"提交失败: {str(e)}"}
