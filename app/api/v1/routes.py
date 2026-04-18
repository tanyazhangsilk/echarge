import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

import random

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from app.db.database import get_db
from app.models.models import (
    Charger,
    Fleet,
    Invoice,
    Operator,
    OperatorBankCard,
    OperatorSettlementRecord,
    Order,
    PriceTemplate,
    SettlementRecord,
    Station,
    User,
)
from app.schemas import InvoiceApplySchema, InvoiceProcessSchema, OrderActionSchema
from app.services.order_service import (
    ORDER_STATUS_LABELS,
    finish_order,
    get_abnormal_order_list,
    get_all_order_list,
    get_history_order_list,
    get_order_page,
    get_order_detail_data,
    get_order_stats,
    get_realtime_order_list,
    get_station_name,
    mark_order_abnormal,
    order_duration_minutes,
    recalculate_order_amounts,
    serialize_order,
    force_stop_order,
)
from app.services.operator_demo_service import (
    ensure_operator_demo_assets,
    ensure_operator_price_templates,
    serialize_price_template,
)
from app.services.station_service import (
    batch_create_station_chargers,
    charger_status_text,
    create_station_charger,
    dump_site_photos,
    get_operator_station_options,
    get_operator_station_page,
    serialize_charger,
    serialize_station,
    station_status_text,
    visibility_text,
)
from app.services.notification_service import send_invoice_email
from app.services.settlement_service import settle_t_plus_1_by_operator
from app.services.wallet_service import get_wallet_summary, get_wallet_transaction_list

api_router = APIRouter()
logger = logging.getLogger(__name__)

operator_audit_store: dict[int, dict[str, Any]] = {}
marketing_audit_store: dict[int, dict[str, Any]] = {}
blacklist_store: set[int] = set()
system_param_store: dict[str, Any] = {
    "station_auto_publish": False,
    "operator_auto_approve": False,
    "station_public_requires_review": True,
    "invoice_auto_approve_limit": 300.0,
    "settlement_platform_rate": 10,
    "settlement_cycle_days": 1,
    "settlement_minimum_amount": 100.0,
    "abnormal_order_sla_minutes": 30,
    "user_refund_limit_per_day": 2,
    "support_email": "support@echarge.com",
    "support_phone": "400-800-1024",
    "notification_email_enabled": True,
    "notification_sms_enabled": True,
    "invoice_notice_enabled": True,
    "abnormal_order_notify_roles": "平台运营, 财务审核",
}
permission_settings_store: list[dict[str, Any]] = [
    {"module": "运营商管理", "view": True, "edit": True, "approve": True, "export": False},
    {"module": "电站管理", "view": True, "edit": True, "approve": True, "export": True},
    {"module": "订单管理", "view": True, "edit": True, "approve": False, "export": True},
    {"module": "财务管理", "view": True, "edit": True, "approve": True, "export": True},
    {"module": "用户管理", "view": True, "edit": True, "approve": False, "export": True},
    {"module": "营销管理", "view": True, "edit": False, "approve": True, "export": False},
    {"module": "系统设置", "view": True, "edit": True, "approve": False, "export": False},
]
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
    operator_auto_approve: bool
    station_public_requires_review: bool
    invoice_auto_approve_limit: float
    settlement_platform_rate: int
    settlement_cycle_days: int
    settlement_minimum_amount: float
    abnormal_order_sla_minutes: int
    user_refund_limit_per_day: int
    support_email: str
    support_phone: str
    notification_email_enabled: bool
    notification_sms_enabled: bool
    invoice_notice_enabled: bool
    abnormal_order_notify_roles: str


class PermissionSettingsPayload(BaseModel):
    modules: list[dict[str, Any]]


class BankCardSubmitPayload(BaseModel):
    account_name: str
    bank_name: str
    bank_account: str
    is_default: bool = True


class StationVisibilityPayload(BaseModel):
    visibility: str


class BindTemplatePayload(BaseModel):
    template_id: int


class StationApplyPayload(BaseModel):
    station_name: str
    province: str
    city: str
    district: str
    address: str
    longitude: float
    latitude: float
    contact_name: str
    contact_phone: str
    operation_hours: str = ""
    parking_fee_desc: str = ""
    station_remark: str = ""
    planned_charger_count: int = 0
    total_power_kw: float = 0
    cover_image: str = ""
    site_photos: list[str] | str | None = None
    qualification_remark: str = ""


class StationAuditProcessPayload(BaseModel):
    action: str
    remark: str = ""


class StationChargerCreatePayload(BaseModel):
    sn_code: str
    charger_name: str
    type: str
    power_kw: float
    status: int = 0


class StationChargerBatchCreatePayload(BaseModel):
    count: int
    type: str
    power_kw: float


class StationChargerUpdatePayload(BaseModel):
    charger_name: str | None = None
    status: int | None = None


class DemoStartOrderPayload(BaseModel):
    user_id: int | None = None
    station_id: int | None = None
    charger_id: int | None = None
    source_type: str = "manual_demo"


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


def get_operator_by_context(db: Session, context: RoleContext) -> Operator | None:
    if context.operator_id is not None:
        operator = db.query(Operator).filter(Operator.id == context.operator_id).first()
        if operator:
            return operator
    return get_current_operator(db)


def resolve_operator_id(db: Session, context: RoleContext) -> int:
    if context.operator_id is not None:
        row = db.query(Operator.id).filter(Operator.id == context.operator_id).first()
        if row:
            return row[0]

    fallback = db.query(Operator.id).order_by(Operator.id.asc()).first()
    if not fallback:
        raise HTTPException(status_code=404, detail="运营商不存在")
    return fallback[0]


def get_operator_basic_info(db: Session, operator_id: int) -> dict[str, Any] | None:
    row = (
        db.query(
            Operator.id.label("id"),
            Operator.name.label("name"),
            Operator.is_verified.label("is_verified"),
        )
        .filter(Operator.id == operator_id)
        .first()
    )
    if not row:
        return None
    return {
        "id": row.id,
        "name": row.name,
        "is_verified": bool(row.is_verified),
    }


def get_or_create_demo_user(db: Session) -> User:
    user = db.query(User).order_by(User.id.asc()).first()
    if user:
        return user

    user = User(
        phone="13800138000",
        nickname="演示车主",
        password_hash="demo-password",
        vin_code="DEMOEV20260001",
        status=0,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def generate_demo_order_no(db: Session) -> str:
    while True:
        order_no = f"EC{datetime.now():%Y%m%d%H%M%S}{random.randint(1000, 9999)}"
        exists = db.query(Order.id).filter(Order.order_no == order_no).first()
        if not exists:
            return order_no


def user_display_name(user: User) -> str:
    return user.nickname or f"鐢ㄦ埛{str(user.phone)[-4:]}"


def get_station_for_operator(
    db: Session,
    *,
    station_id: int,
    operator_id: int,
    with_chargers: bool = False,
) -> Station | None:
    query = (
        db.query(Station)
        .options(joinedload(Station.operator), joinedload(Station.price_template))
        .filter(Station.id == station_id, Station.operator_id == operator_id, Station.is_deleted.is_(False))
    )
    if with_chargers:
        query = query.options(joinedload(Station.chargers).joinedload(Charger.station))
    return query.first()


def validate_station_manageable(station: Station) -> tuple[bool, str]:
    if station.status != 0:
        return False, "电站审核通过后才允许配置电桩和绑定模板"
    return True, ""


SETTLEMENT_STATUS_TEXT = {
    0: "待打款",
    1: "已打款",
    2: "挂起待补资料",
}

INVOICE_STATUS_TEXT = {
    0: "待开票",
    1: "已开票",
    2: "已驳回",
}

BANK_CARD_STATUS_TEXT = {
    0: "待审核",
    1: "已通过",
    2: "已驳回",
}


def mask_bank_account(bank_account: str | None) -> str:
    if not bank_account:
        return ""
    digits = bank_account.replace(" ", "")
    if len(digits) < 8:
        return digits
    return f"{digits[:4]} **** **** {digits[-4:]}"


def serialize_bank_card(card: OperatorBankCard) -> dict:
    return {
        "id": card.id,
        "operator_id": card.operator_id,
        "account_name": card.account_name,
        "bank_name": card.bank_name,
        "bank_account": card.bank_account,
        "bank_account_masked": mask_bank_account(card.bank_account),
        "is_default": bool(card.is_default),
        "bind_status": card.bind_status,
        "bind_status_text": BANK_CARD_STATUS_TEXT.get(card.bind_status, "未知状态"),
        "created_at": card.created_at.strftime("%Y-%m-%d %H:%M:%S") if card.created_at else "",
        "updated_at": card.updated_at.strftime("%Y-%m-%d %H:%M:%S") if card.updated_at else "",
    }


def resolve_bank_card_audit_status(cards: list[OperatorBankCard]) -> tuple[str, str]:
    if not cards:
        return "unbound", "未绑定"
    if any(card.bind_status == 1 for card in cards):
        return "approved", "已通过"
    if any(card.bind_status == 0 for card in cards):
        return "pending", "待审核"
    return "rejected", "已驳回"


def resolve_settlement_qualification(operator: Operator | None, cards: list[OperatorBankCard]) -> tuple[bool, str]:
    is_verified = bool(operator and operator.is_verified)
    approved_default_card = next((card for card in cards if card.is_default and card.bind_status == 1), None)
    if is_verified and approved_default_card:
        return True, "已具备 T+1 清分资格"

    missing_parts: list[str] = []
    if not is_verified:
        missing_parts.append("运营商未认证")
    if not approved_default_card:
        missing_parts.append("未配置默认且审核通过的收款卡")
    return False, "，".join(missing_parts) if missing_parts else "暂不具备清分资格"


def resolve_settlement_qualification_from_flag(is_verified: bool, cards: list[OperatorBankCard]) -> tuple[bool, str]:
    approved_default_card = next((card for card in cards if card.is_default and card.bind_status == 1), None)
    if is_verified and approved_default_card:
        return True, "已具备 T+1 清分资格"

    missing_parts: list[str] = []
    if not is_verified:
        missing_parts.append("运营商未认证")
    if not approved_default_card:
        missing_parts.append("未配置默认且审核通过的收款卡")
    return False, "，".join(missing_parts) if missing_parts else "暂不具备清分资格"


def serialize_operator_settlement(record: OperatorSettlementRecord) -> dict:
    return {
        "id": record.id,
        "settle_date": str(record.settle_date),
        "operator_id": record.operator_id,
        "operator_name": record.operator.name if record.operator else "",
        "order_count": record.order_count,
        "total_amount": float(record.total_amount),
        "platform_rate": float(record.platform_rate),
        "platform_fee": float(record.platform_fee),
        "settle_amount": float(record.settle_amount),
        "status": record.status,
        "status_text": SETTLEMENT_STATUS_TEXT.get(record.status, "未知"),
        "can_payout": record.status == 0,
        "hold_reason": record.hold_reason,
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S") if record.created_at else "",
        "updated_at": record.updated_at.strftime("%Y-%m-%d %H:%M:%S") if record.updated_at else "",
    }


def serialize_invoice_record(invoice: Invoice, can_process: bool) -> dict:
    invoice_no = f"INV{invoice.created_at.strftime('%Y%m%d')}{str(invoice.id).zfill(4)}"
    return {
        "id": invoice.id,
        "invoice_no": invoice_no,
        "user_id": invoice.user_id,
        "user_phone": invoice.user.phone if invoice.user else "",
        "operator_id": invoice.operator_id,
        "operator_name": invoice.operator.name if invoice.operator else "",
        "order_id": invoice.order_id,
        "order_no": invoice.related_order.order_no if invoice.related_order else None,
        "invoice_title": invoice.invoice_title,
        "amount": float(invoice.amount or 0),
        "email": invoice.email,
        "status": invoice.status,
        "status_text": INVOICE_STATUS_TEXT.get(invoice.status, "未知状态"),
        "file_url": invoice.file_url,
        "remark": invoice.remark,
        "created_at": invoice.created_at.strftime("%Y-%m-%d %H:%M:%S") if invoice.created_at else "",
        "uploaded_at": invoice.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if invoice.uploaded_at else None,
        "updated_at": invoice.updated_at.strftime("%Y-%m-%d %H:%M:%S") if invoice.updated_at else "",
        "can_process": can_process,
    }


def seed_runtime_data(db: Session) -> None:
    operator = get_current_operator(db)
    operator_id = operator.id if operator else 0

    if not template_store:
        template_store.extend(
            [
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
            ]
        )

    if not tag_store:
        tag_store.extend(
            [
                {"id": 1, "name": "高频通勤", "color": "#409EFF", "description": "近30天充电20次以上", "user_count": 86},
                {"id": 2, "name": "夜间充电", "color": "#67C23A", "description": "夜间活跃用户", "user_count": 43},
                {"id": 3, "name": "待召回", "color": "#E6A23C", "description": "近14天未复购", "user_count": 27},
            ]
        )

    if not discount_campaign_store:
        discount_campaign_store.extend(
            [
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
            ]
        )

    if not coupon_campaign_store:
        coupon_campaign_store.extend(
            [
                {
                    "id": 1,
                    "name": "春季园区通勤券",
                    "discount_value": 10,
                    "inventory": 1000,
                    "dispatched": 640,
                    "used": 381,
                    "status": "active",
                },
                {
                    "id": 2,
                    "name": "夜充满减券",
                    "discount_value": 15,
                    "inventory": 500,
                    "dispatched": 120,
                    "used": 39,
                    "status": "paused",
                },
            ]
        )

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
        detail = settle_t_plus_1_by_operator(
            payload.date,
            db=db,
            platform_rate_percent=system_param_store.get("settlement_platform_rate", 10),
        )
        logger.info(
            "manual_settle",
            extra={
                "date": str(payload.date),
                "processed": detail["processed_order_count"],
                "operator_count": detail["processed_operator_count"],
            },
        )
        return {
            "code": 0,
            "processed": detail["processed_order_count"],
            "operator_count": detail["processed_operator_count"],
            "data": detail,
        }
    except Exception as e:
        logger.exception("manual_settle_failed", extra={"date": str(payload.date)})
        return {"code": 1, "processed": 0, "message": str(e)}

@api_router.get("/finance/settlements", tags=["finance"])
async def get_settlements(
    context: RoleContext = Depends(get_role_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context) if context.role == "operator" else None
    query = (
        db.query(OperatorSettlementRecord)
        .options(joinedload(OperatorSettlementRecord.operator))
        .order_by(OperatorSettlementRecord.settle_date.desc(), OperatorSettlementRecord.operator_id.asc())
    )
    if operator_id is not None:
        query = query.filter(OperatorSettlementRecord.operator_id == operator_id)

    records = query.all()
    if records:
        data = [serialize_operator_settlement(r) for r in records]
        return {
            "code": 200,
            "data": data,
            "summary": {
                "order_count": sum(item["order_count"] for item in data),
                "total_amount": round(sum(item["total_amount"] for item in data), 2),
                "platform_fee": round(sum(item["platform_fee"] for item in data), 2),
                "settle_amount": round(sum(item["settle_amount"] for item in data), 2),
            },
        }

    legacy_records = db.query(SettlementRecord).order_by(SettlementRecord.settle_date.desc()).all()
    legacy_data = [
        {
            "settle_date": str(r.settle_date),
            "order_count": r.order_count,
            "total_amount": float(r.total_amount),
            "platform_fee": float(r.platform_fee),
            "settle_amount": float(r.settle_amount),
            "status": r.status,
            "status_text": SETTLEMENT_STATUS_TEXT.get(r.status, "鏈煡"),
            "operator_id": None,
            "operator_name": "全网汇总",
            "platform_rate": None,
            "can_payout": None,
            "hold_reason": None,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else "",
        }
        for r in legacy_records
    ]
    return {"code": 200, "data": legacy_data}


@api_router.post("/finance/settle", tags=["finance"])
async def trigger_settle(db: Session = Depends(get_db)):
    target = date.today() - timedelta(days=1)
    try:
        detail = settle_t_plus_1_by_operator(
            target,
            db=db,
            platform_rate_percent=system_param_store.get("settlement_platform_rate", 10),
        )
        return {
            "code": 200,
            "message": (
                f"清分完成：处理订单 {detail['processed_order_count']} 笔，"
                f"覆盖运营商 {detail['processed_operator_count']} 个，"
                f"跳过已存在批次 {detail['skipped_operator_count']} 个"
            ),
            "processed": detail["processed_order_count"],
            "operator_count": detail["processed_operator_count"],
            "skipped_operator_count": detail["skipped_operator_count"],
            "data": detail,
        }
    except Exception as e:
        logger.exception("finance_settle_failed", extra={"date": str(target)})
        return {"code": 500, "message": f"娓呭垎澶辫触: {str(e)}", "processed": 0}


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
        return {"code": 400, "message": "订单不存在、无权限或当前非充电中状态"}

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
        return {"code": 400, "message": "订单不存在、无权限或当前非充电中状态"}

    return {
        "code": 200,
        "message": "订单已标记异常",
        "data": serialize_order(order),
    }


@api_router.get("/admin/orders", tags=["orders", "admin"])
async def get_admin_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: str | None = None,
    status: int | None = None,
    station_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    _context: RoleContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    return {
        "code": 200,
        "data": get_order_page(
            db,
            page=page,
            page_size=page_size,
            keyword=keyword,
            status=status,
            station_id=station_id,
            start_date=start_date,
            end_date=end_date,
        ),
    }


@api_router.get("/admin/orders/abnormal", tags=["orders", "admin"])
async def get_admin_abnormal_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: str | None = None,
    status: int | None = None,
    station_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    abnormal_reason: str | None = None,
    _context: RoleContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    return {
        "code": 200,
        "data": get_order_page(
            db,
            page=page,
            page_size=page_size,
            keyword=keyword,
            status=status,
            station_id=station_id,
            start_date=start_date,
            end_date=end_date,
            abnormal_reason=abnormal_reason,
            default_status=2,
        ),
    }


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


@api_router.get("/operator/stations", tags=["operator"])
async def get_operator_stations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: str | None = None,
    status: int | None = None,
    visibility: str | None = None,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator = get_operator_by_context(db, context)
    if not operator:
        return {"code": 404, "message": "当前运营商未找到，请先入驻"}
    ensure_operator_demo_assets(db, operator)
    operator_id = operator.id

    return {
        "code": 200,
        "data": get_operator_station_page(
            db,
            operator_id=operator_id,
            page=page,
            page_size=page_size,
            keyword=keyword,
            status=status,
            visibility=visibility,
        ),
    }


@api_router.get("/operator/stations/options", tags=["operator"])
async def get_operator_station_option_list(
    keyword: str | None = None,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator = get_operator_by_context(db, context)
    if not operator:
        return {"code": 404, "message": "当前运营商未找到，请先入驻"}
    ensure_operator_demo_assets(db, operator)
    operator_id = operator.id
    return {
        "code": 200,
        "data": get_operator_station_options(db, operator_id=operator_id, keyword=keyword),
    }


@api_router.post("/operator/stations/apply", tags=["operator"])
async def operator_apply_station(
    payload: StationApplyPayload,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator = get_operator_by_context(db, context)
    if not operator:
        return {"code": 404, "message": "当前运营商未找到，请先入驻"}

    station_name = payload.station_name.strip()
    if not station_name:
        return {"code": 400, "message": "请填写电站名称"}

    new_station = Station(
        operator_id=operator.id,
        name=station_name,
        province=payload.province.strip(),
        city=payload.city.strip(),
        district=payload.district.strip(),
        address=payload.address.strip(),
        longitude=Decimal(str(payload.longitude)),
        latitude=Decimal(str(payload.latitude)),
        contact_name=payload.contact_name.strip(),
        contact_phone=payload.contact_phone.strip(),
        operation_hours=payload.operation_hours.strip(),
        parking_fee_desc=payload.parking_fee_desc.strip(),
        station_remark=payload.station_remark.strip(),
        planned_charger_count=max(int(payload.planned_charger_count or 0), 0),
        total_power_kw=Decimal(str(payload.total_power_kw or 0)),
        cover_image=payload.cover_image.strip(),
        site_photos_json=dump_site_photos(payload.site_photos),
        qualification_remark=payload.qualification_remark.strip(),
        audit_remark="待管理员审核",
        status=3,
        visibility="private",
    )
    db.add(new_station)
    db.commit()
    db.refresh(new_station)

    return {
        "code": 200,
        "message": "电站申请已提交，等待管理员审核",
        "data": serialize_station(new_station),
    }


@api_router.get("/operator/stations/{station_id}/chargers", tags=["operator"])
async def get_operator_station_chargers(
    station_id: int,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator = get_operator_by_context(db, context)
    if not operator:
        return {"code": 404, "message": "当前运营商未找到，请先入驻"}
    ensure_operator_demo_assets(db, operator)
    operator_id = operator.id

    station = (
        db.query(Station)
        .options(joinedload(Station.chargers).joinedload(Charger.station))
        .filter(Station.id == station_id, Station.operator_id == operator_id, Station.is_deleted.is_(False))
        .first()
    )
    if not station:
        return {"code": 404, "message": "电站不存在或无权限访问"}

    return {"code": 200, "data": [serialize_charger(item) for item in station.chargers]}


@api_router.post("/operator/stations/{station_id}/chargers", tags=["operator"])
async def create_operator_station_charger(
    station_id: int,
    payload: StationChargerCreatePayload,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    station = get_station_for_operator(db, station_id=station_id, operator_id=operator_id, with_chargers=True)
    if not station:
        return {"code": 404, "message": "电站不存在或无权限访问"}

    manageable, message = validate_station_manageable(station)
    if not manageable:
        return {"code": 400, "message": message}

    sn_code = payload.sn_code.strip().upper()
    if not sn_code:
        return {"code": 400, "message": "请输入电桩编号"}
    exists = db.query(Charger.id).filter(Charger.sn_code == sn_code).first()
    if exists:
        return {"code": 400, "message": "电桩编号已存在"}

    charger_type = (payload.type or "").strip().upper()
    if charger_type not in {"AC", "DC"}:
        return {"code": 400, "message": "电桩类型仅支持 AC/DC"}

    status = int(payload.status)
    if status not in {0, 1, 2, 3}:
        return {"code": 400, "message": "电桩状态不合法"}

    charger = create_station_charger(
        db,
        station=station,
        sn_code=sn_code,
        charger_name=(payload.charger_name or "").strip() or f"{station.name[:10]}-{len(station.chargers) + 1:02d}号桩",
        charger_type=charger_type,
        power_kw=Decimal(str(payload.power_kw)),
        status=status,
    )
    return {"code": 200, "message": "电桩新增成功", "data": serialize_charger(charger)}


@api_router.post("/operator/stations/{station_id}/chargers/batch-create", tags=["operator"])
async def batch_create_operator_station_chargers(
    station_id: int,
    payload: StationChargerBatchCreatePayload,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    station = get_station_for_operator(db, station_id=station_id, operator_id=operator_id, with_chargers=True)
    if not station:
        return {"code": 404, "message": "电站不存在或无权限访问"}

    manageable, message = validate_station_manageable(station)
    if not manageable:
        return {"code": 400, "message": message}

    count = int(payload.count or 0)
    if count < 1 or count > 50:
        return {"code": 400, "message": "批量生成数量需在 1-50 之间"}

    charger_type = (payload.type or "").strip().upper()
    if charger_type not in {"AC", "DC"}:
        return {"code": 400, "message": "电桩类型仅支持 AC/DC"}

    created = batch_create_station_chargers(
        db,
        station=station,
        count=count,
        charger_type=charger_type,
        power_kw=Decimal(str(payload.power_kw)),
    )
    return {
        "code": 200,
        "message": f"已批量生成 {len(created)} 个电桩",
        "data": [serialize_charger(charger) for charger in created],
    }


@api_router.patch("/operator/stations/{station_id}/chargers/{charger_id}", tags=["operator"])
async def update_operator_station_charger(
    station_id: int,
    charger_id: int,
    payload: StationChargerUpdatePayload,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    station = get_station_for_operator(db, station_id=station_id, operator_id=operator_id, with_chargers=True)
    if not station:
        return {"code": 404, "message": "电站不存在或无权限访问"}

    charger = next((item for item in station.chargers if item.id == charger_id), None)
    if not charger:
        return {"code": 404, "message": "电桩不存在"}

    if payload.status is not None and int(payload.status) not in {0, 1, 2, 3}:
        return {"code": 400, "message": "电桩状态不合法"}

    if payload.charger_name is not None:
        charger.name = payload.charger_name.strip() or charger.name
    if payload.status is not None:
        charger.status = int(payload.status)
    db.commit()
    db.refresh(charger)
    return {"code": 200, "message": "电桩配置已更新", "data": serialize_charger(charger)}


@api_router.post("/operator/stations/{station_id}/visibility", tags=["operator"])
async def update_operator_station_visibility(
    station_id: int,
    payload: StationVisibilityPayload,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    station = (
        db.query(Station)
        .filter(Station.id == station_id, Station.operator_id == operator_id, Station.is_deleted.is_(False))
        .first()
    )
    if not station:
        return {"code": 404, "message": "电站不存在或无权限访问"}

    visibility = (payload.visibility or "").strip().lower()
    if visibility not in {"public", "private"}:
        return {"code": 400, "message": "visibility 仅支持 public/private"}
    if visibility == "public" and station.status != 0:
        return {"code": 400, "message": "电站未审核通过，不能设置为公开站点"}

    station.visibility = visibility
    db.commit()
    db.refresh(station)
    return {
        "code": 200,
        "message": "电站可见性已更新",
        "data": {
            "id": station.id,
            "visibility": station.visibility,
            "visibility_text": visibility_text(station.visibility),
            "status": station.status,
            "status_text": station_status_text(station.status),
        },
    }


@api_router.post("/operator/stations/{station_id}/bind-template", tags=["operator"])
async def bind_operator_station_template(
    station_id: int,
    payload: BindTemplatePayload,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)

    station = (
        db.query(Station)
        .options(joinedload(Station.price_template), joinedload(Station.operator), joinedload(Station.chargers))
        .filter(Station.id == station_id, Station.operator_id == operator_id, Station.is_deleted.is_(False))
        .first()
    )
    if not station:
        return {"code": 404, "message": "电站不存在或无权限访问"}

    template = (
        db.query(PriceTemplate)
        .filter(
            PriceTemplate.id == payload.template_id,
            PriceTemplate.operator_id == operator_id,
            PriceTemplate.is_deleted.is_(False),
        )
        .first()
    )
    if not template:
        return {"code": 404, "message": "电价模板不存在"}
    if station.status != 0:
        return {"code": 400, "message": "电站审核通过后才允许绑定模板"}

    station.template_id = template.id
    station.price_template = template
    db.commit()
    db.refresh(station)
    return {"code": 200, "message": "模板绑定成功", "data": serialize_station(station)}


@api_router.get("/operator/pricing/templates", tags=["operator"])
async def get_operator_pricing_templates(
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)

    templates = (
        db.query(PriceTemplate)
        .filter(PriceTemplate.operator_id == operator_id, PriceTemplate.is_deleted.is_(False))
        .order_by(PriceTemplate.updated_at.desc(), PriceTemplate.id.desc())
        .all()
    )
    if not templates:
        operator = get_operator_by_context(db, context)
        if operator:
            templates = ensure_operator_price_templates(db, operator)
    return {"code": 200, "data": [serialize_price_template(item) for item in templates]}


@api_router.get("/operator/orders/start-options", tags=["orders", "operator"])
async def get_operator_order_start_options(
    station_id: int | None = None,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator = get_operator_by_context(db, context)
    if not operator:
        return {"code": 404, "message": "运营商不存在"}

    ensure_operator_demo_assets(db, operator)
    demo_user = get_or_create_demo_user(db)
    stations = (
        db.query(Station)
        .options(joinedload(Station.operator), joinedload(Station.price_template), joinedload(Station.chargers).joinedload(Charger.station))
        .filter(Station.operator_id == operator.id, Station.is_deleted.is_(False))
        .order_by(Station.updated_at.desc(), Station.id.desc())
        .all()
    )
    selected_station = next((item for item in stations if station_id and item.id == station_id), None)
    if selected_station is None and stations:
        selected_station = stations[0]

    return {
        "code": 200,
        "data": {
            "users": [
                {
                    "id": demo_user.id,
                    "nickname": demo_user.nickname or user_display_name(demo_user),
                    "phone": demo_user.phone,
                    "vin": demo_user.vin_code,
                    "is_default": True,
                }
            ],
            "stations": [serialize_station(station) for station in stations],
            "chargers": [serialize_charger(charger) for charger in (selected_station.chargers if selected_station else [])],
            "default_user_id": demo_user.id,
            "default_station_id": selected_station.id if selected_station else None,
        },
    }


@api_router.post("/operator/orders/demo-start", tags=["orders", "operator"])
async def operator_demo_start_order(
    payload: DemoStartOrderPayload,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator = get_operator_by_context(db, context)
    if not operator:
        return {"code": 404, "message": "运营商不存在"}
    source_type = (payload.source_type or "manual_demo").strip() or "manual_demo"
    if source_type not in {"manual_demo", "qr_code", "mini_program"}:
        return {"code": 400, "message": "订单来源不合法"}

    ensure_operator_demo_assets(db, operator)
    base_station_query = (
        db.query(Station)
        .options(joinedload(Station.price_template), joinedload(Station.chargers).joinedload(Charger.station))
        .filter(Station.operator_id == operator.id, Station.is_deleted.is_(False))
    )
    if payload.station_id:
        station = base_station_query.filter(Station.id == payload.station_id).first()
    else:
        station = base_station_query.order_by(Station.status.asc(), Station.id.asc()).first()
    if not station:
        return {"code": 400, "message": "当前运营商暂无可用电站"}
    if station.status != 0:
        return {"code": 400, "message": "请选择已审核通过的电站发起充电"}
    active_charger_ids = {
        item[0]
        for item in db.query(Order.charger_id)
        .filter(Order.operator_id == operator.id, Order.status == 0)
        .all()
    }
    if payload.charger_id:
        charger = next((item for item in station.chargers if item.id == payload.charger_id), None)
    else:
        charger = next(
            (item for item in station.chargers if item.id not in active_charger_ids and item.status not in {2, 3}),
            None,
        )
    if not charger:
        charger = next((item for item in station.chargers if item.status not in {2, 3}), None)
    if not charger:
        return {"code": 400, "message": "当前电站暂无可用充电桩"}
    if charger.status in {2, 3}:
        return {"code": 400, "message": "当前电桩不可用，请选择其他电桩"}

    user = (
        db.query(User).filter(User.id == payload.user_id).first()
        if payload.user_id
        else get_or_create_demo_user(db)
    )
    if not user:
        user = get_or_create_demo_user(db)

    start_time = datetime.now() - timedelta(minutes=random.randint(12, 45))
    order = Order(
        order_no=generate_demo_order_no(db),
        user_id=user.id,
        operator_id=operator.id,
        station_id=station.id,
        charger_id=charger.id,
        vin=user.vin_code or f"VIN{user.id:08d}",
        start_time=start_time,
        source_type=source_type,
        pay_status=0,
        status=0,
        abnormal_reason=None,
        settle_status=0,
    )
    order.user = user
    order.operator = operator
    order.station = station
    order.charger = charger
    db.add(order)
    recalculate_order_amounts(order, minimum_charge_kwh=Decimal(str(random.randint(8, 36))))
    charger.status = 1
    db.commit()
    db.refresh(order)
    return {"code": 200, "message": "已创建实时订单", "data": serialize_order(order)}


@api_router.get("/operator/orders/history", tags=["orders", "operator"])
async def get_operator_history_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: str | None = None,
    status: int | None = None,
    station_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    return {
        "code": 200,
        "data": get_order_page(
            db,
            operator_id=operator_id,
            page=page,
            page_size=page_size,
            keyword=keyword,
            status=status,
            station_id=station_id,
            start_date=start_date,
            end_date=end_date,
            default_status=1,
        ),
    }


@api_router.get("/operator/orders/realtime", tags=["orders", "operator"])
async def get_operator_realtime_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: str | None = None,
    status: int | None = None,
    station_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    return {
        "code": 200,
        "data": get_order_page(
            db,
            operator_id=operator_id,
            page=page,
            page_size=page_size,
            keyword=keyword,
            status=status,
            station_id=station_id,
            start_date=start_date,
            end_date=end_date,
            default_status=0,
        ),
    }


@api_router.get("/operator/orders/abnormal", tags=["orders", "operator"])
async def get_operator_abnormal_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: str | None = None,
    status: int | None = None,
    station_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    abnormal_reason: str | None = None,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    return {
        "code": 200,
        "data": get_order_page(
            db,
            operator_id=operator_id,
            page=page,
            page_size=page_size,
            keyword=keyword,
            status=status,
            station_id=station_id,
            start_date=start_date,
            end_date=end_date,
            abnormal_reason=abnormal_reason,
            default_status=2,
        ),
    }


@api_router.get("/operator/orders/{order_id}", tags=["orders", "operator"])
async def get_operator_order_detail(
    order_id: int,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    order_data = get_order_detail_data(db, order_id, operator_id=operator_id)
    if not order_data:
        return {"code": 404, "message": "订单不存在或无权限访问"}
    return {"code": 200, "data": order_data}


@api_router.post("/operator/orders/{order_id}/finish", tags=["orders", "operator"])
async def operator_finish_order(
    order_id: int,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    order = finish_order(db, order_id, operator_id=operator_id)
    if not order:
        return {"code": 400, "message": "订单不存在、无权限或当前非充电中状态"}
    return {"code": 200, "message": "订单已完成并转入历史订单", "data": serialize_order(order)}


@api_router.post("/operator/orders/{order_id}/force-stop", tags=["orders", "operator"])
async def operator_force_stop_order(
    order_id: int,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    order = force_stop_order(db, order_id, operator_id=operator_id)
    if not order:
        return {"code": 400, "message": "订单不存在、无权限或当前非充电中状态"}
    return {"code": 200, "message": "订单已强制停止", "data": serialize_order(order)}


@api_router.post("/operator/orders/{order_id}/mark-abnormal", tags=["orders", "operator"])
async def operator_mark_order_abnormal(
    order_id: int,
    payload: OrderActionSchema,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    order = mark_order_abnormal(db, order_id, payload.abnormal_reason, operator_id=operator_id)
    if not order:
        return {"code": 400, "message": "订单不存在、无权限或当前非充电中状态"}
    return {"code": 200, "message": "订单已标记异常并转入异常订单", "data": serialize_order(order)}


@api_router.get("/finance/cards", tags=["finance"])
async def get_operator_bank_cards(
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    operator = get_operator_basic_info(db, operator_id)
    if not operator:
        return {"code": 404, "message": "运营商不存在"}

    cards = (
        db.query(OperatorBankCard)
        .filter(OperatorBankCard.operator_id == operator_id)
        .order_by(OperatorBankCard.is_default.desc(), OperatorBankCard.created_at.desc())
        .all()
    )

    audit_status, audit_status_text = resolve_bank_card_audit_status(cards)
    settlement_eligible, settlement_tip = resolve_settlement_qualification_from_flag(operator["is_verified"], cards)

    default_card_raw = next((card for card in cards if card.is_default and card.bind_status == 1), None)
    if default_card_raw is None:
        default_card_raw = next((card for card in cards if card.bind_status == 1), None)

    return {
        "code": 200,
        "data": {
            "operator_id": operator["id"],
            "operator_name": operator["name"],
            "operator_verified": operator["is_verified"],
            "audit_status": audit_status,
            "audit_status_text": audit_status_text,
            "cards": [serialize_bank_card(card) for card in cards],
            "default_card": serialize_bank_card(default_card_raw) if default_card_raw else None,
            "settlement_eligible": settlement_eligible,
            "settlement_tip": settlement_tip,
            "settlement_notice": "绑卡审核通过后才可启动 T+1 清分；如遇法定节假日，打款按清算规则顺延至下一工作日。",
        },
    }


@api_router.post("/finance/cards", tags=["finance"])
async def submit_operator_bank_card(
    payload: BankCardSubmitPayload,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    operator = get_operator_basic_info(db, operator_id)
    if not operator:
        return {"code": 404, "message": "运营商不存在"}

    account_name = payload.account_name.strip()
    bank_name = payload.bank_name.strip()
    bank_account = payload.bank_account.replace(" ", "").strip()

    if not account_name or not bank_name or len(bank_account) < 8:
        return {"code": 400, "message": "请填写完整且有效的绑卡信息"}

    existing_cards = (
        db.query(OperatorBankCard)
        .filter(OperatorBankCard.operator_id == operator_id)
        .order_by(OperatorBankCard.created_at.desc())
        .all()
    )

    is_default = bool(payload.is_default or not existing_cards)
    if is_default:
        for card in existing_cards:
            card.is_default = False

    card = OperatorBankCard(
        operator_id=operator_id,
        account_name=account_name,
        bank_name=bank_name,
        bank_account=bank_account,
        is_default=is_default,
        bind_status=0,
    )

    db.add(card)
    db.commit()
    db.refresh(card)

    return {
        "code": 200,
        "message": "绑卡资料已提交，等待平台审核",
        "data": {
            "card": serialize_bank_card(card),
            "audit_status": "pending",
            "audit_status_text": "待审核",
        },
    }


@api_router.get("/finance/cards/audit-status", tags=["finance"])
async def get_operator_bank_card_audit_status(
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context)
    operator = get_operator_basic_info(db, operator_id)
    if not operator:
        return {"code": 404, "message": "运营商不存在"}

    cards = (
        db.query(OperatorBankCard)
        .filter(OperatorBankCard.operator_id == operator_id)
        .order_by(OperatorBankCard.created_at.desc())
        .all()
    )
    audit_status, audit_status_text = resolve_bank_card_audit_status(cards)
    settlement_eligible, settlement_tip = resolve_settlement_qualification_from_flag(operator["is_verified"], cards)

    return {
        "code": 200,
        "data": {
            "audit_status": audit_status,
            "audit_status_text": audit_status_text,
            "operator_verified": operator["is_verified"],
            "settlement_eligible": settlement_eligible,
            "settlement_tip": settlement_tip,
        },
    }


@api_router.get("/finance/invoices", tags=["finance"])
async def get_invoices(
    status: int | None = None,
    keyword: str | None = None,
    context: RoleContext = Depends(get_role_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context) if context.role == "operator" else None
    query = (
        db.query(Invoice)
        .options(joinedload(Invoice.user), joinedload(Invoice.operator), joinedload(Invoice.related_order))
        .order_by(Invoice.created_at.desc())
    )

    if operator_id is not None:
        query = query.filter(Invoice.operator_id == operator_id)

    if status in (0, 1, 2):
        query = query.filter(Invoice.status == status)

    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        query = query.join(User, Invoice.user_id == User.id).filter(
            or_(
                User.phone.like(kw),
                Invoice.email.like(kw),
                Invoice.invoice_title.like(kw),
            )
        )

    invoices = query.all()
    data = [
        serialize_invoice_record(
            inv,
            can_process=(context.role == "operator" and inv.operator_id == operator_id and inv.status == 0),
        )
        for inv in invoices
    ]

    return {
        "code": 200,
        "data": data,
        "summary": {
            "pending_count": sum(1 for item in data if item["status"] == 0),
            "issued_count": sum(1 for item in data if item["status"] == 1),
            "rejected_count": sum(1 for item in data if item["status"] == 2),
            "issued_amount": round(sum(item["amount"] for item in data if item["status"] == 1), 2),
        },
        "scope": context.role,
    }


@api_router.post("/finance/invoices/apply", tags=["finance"])
async def apply_invoice(payload: InvoiceApplySchema, db: Session = Depends(get_db)):
    operator = db.query(Operator).filter(Operator.id == payload.operator_id).first()
    if not operator:
        return {"code": 404, "message": "运营商不存在"}

    if payload.order_id:
        order = db.query(Order).filter(Order.id == payload.order_id).first()
        if not order:
            return {"code": 404, "message": "订单不存在"}
        if order.operator_id != payload.operator_id:
            return {"code": 400, "message": "订单与运营商不匹配"}

    invoice = Invoice(
        user_id=payload.user_id,
        operator_id=payload.operator_id,
        order_id=payload.order_id,
        invoice_title=(payload.invoice_title or "个人")[:100],
        amount=Decimal(str(payload.amount)),
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
async def get_invoice_detail(
    invoice_id: int,
    context: RoleContext = Depends(get_role_context),
    db: Session = Depends(get_db),
):
    operator_id = resolve_operator_id(db, context) if context.role == "operator" else None
    inv = (
        db.query(Invoice)
        .options(joinedload(Invoice.user), joinedload(Invoice.operator), joinedload(Invoice.related_order))
        .filter(Invoice.id == invoice_id)
        .first()
    )
    if not inv:
        return {"code": 404, "message": "发票申请不存在"}

    if operator_id is not None and inv.operator_id != operator_id:
        return {"code": 403, "message": "无权限查看该发票"}

    return {
        "code": 200,
        "data": serialize_invoice_record(
            inv,
            can_process=(operator_id is not None and inv.operator_id == operator_id and inv.status == 0),
        ),
    }


@api_router.post("/finance/invoices/{invoice_id}/process", tags=["finance"])
async def process_invoice(
    invoice_id: int,
    payload: InvoiceProcessSchema,
    context: RoleContext = Depends(require_operator_context),
    db: Session = Depends(get_db),
):
    action = (payload.action or "").strip().lower()
    if action not in {"approve", "reject"}:
        return {"code": 400, "message": "不支持的处理动作"}

    invoice = (
        db.query(Invoice)
        .options(joinedload(Invoice.operator), joinedload(Invoice.user))
        .filter(Invoice.id == invoice_id, Invoice.operator_id == context.operator_id)
        .first()
    )
    if not invoice:
        return {"code": 404, "message": "发票申请不存在或无权限处理"}

    if invoice.status != 0:
        return {"code": 400, "message": "该发票申请已处理，请勿重复操作"}

    now = datetime.now()
    if action == "approve":
        file_url = (payload.file_url or "").strip()
        if not file_url:
            return {"code": 400, "message": "请上传发票文件后再提交"}
        invoice.status = 1
        invoice.file_url = file_url
        invoice.uploaded_at = now
        invoice.remark = payload.remark or "运营商已开票"
        notify_status = "已开票"
    else:
        invoice.status = 2
        invoice.remark = payload.remark or "运营商驳回"
        notify_status = "已驳回"

    db.commit()
    db.refresh(invoice)

    send_invoice_email(
        to_email=invoice.email,
        invoice_no=f"INV{invoice.created_at.strftime('%Y%m%d')}{str(invoice.id).zfill(4)}",
        status=notify_status,
        operator_name=invoice.operator.name if invoice.operator else f"运营商#{invoice.operator_id}",
        amount=float(invoice.amount or 0),
        file_url=invoice.file_url,
        remark=invoice.remark,
    )

    return {
        "code": 200,
        "message": f"发票申请处理成功（{notify_status}），已触发邮件通知",
        "data": serialize_invoice_record(invoice, can_process=False),
    }


@api_router.get("/admin/finance/settlements", tags=["admin"])
async def admin_get_settlements(db: Session = Depends(get_db)):
    records = (
        db.query(OperatorSettlementRecord)
        .options(joinedload(OperatorSettlementRecord.operator))
        .order_by(OperatorSettlementRecord.settle_date.desc(), OperatorSettlementRecord.operator_id.asc())
        .all()
    )

    if not records:
        legacy = db.query(SettlementRecord).order_by(SettlementRecord.settle_date.desc()).all()
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
                    "status": r.status,
                    "status_text": SETTLEMENT_STATUS_TEXT.get(r.status, "未知"),
                    "operator_count": None,
                    "ready_count": None,
                    "hold_count": None,
                }
                for r in legacy
            ],
            "operator_records": [],
        }

    operator_data = [serialize_operator_settlement(r) for r in records]
    daily_map: dict[str, dict] = {}
    for item in operator_data:
        day_key = item["settle_date"]
        if day_key not in daily_map:
            daily_map[day_key] = {
                "settle_date": day_key,
                "order_count": 0,
                "total_amount": 0.0,
                "platform_fee": 0.0,
                "settle_amount": 0.0,
                "operator_count": 0,
                "ready_count": 0,
                "hold_count": 0,
                "status": 0,
                "status_text": "待打款",
            }
        day = daily_map[day_key]
        day["order_count"] += item["order_count"]
        day["total_amount"] += item["total_amount"]
        day["platform_fee"] += item["platform_fee"]
        day["settle_amount"] += item["settle_amount"]
        day["operator_count"] += 1
        if item["status"] == 2:
            day["hold_count"] += 1
        else:
            day["ready_count"] += 1

    data = sorted(daily_map.values(), key=lambda row: row["settle_date"], reverse=True)
    for row in data:
        row["total_amount"] = round(row["total_amount"], 2)
        row["platform_fee"] = round(row["platform_fee"], 2)
        row["settle_amount"] = round(row["settle_amount"], 2)
        if row["hold_count"] > 0:
            row["status"] = 2
            row["status_text"] = "部分挂起待补资料"
        else:
            row["status"] = 0
            row["status_text"] = "待打款"

    return {"code": 200, "data": data, "operator_records": operator_data}


@api_router.post("/admin/finance/settle", tags=["admin"])
async def admin_trigger_settle(payload: dict, db: Session = Depends(get_db)):
    """管理员手动触发某日清分。"""
    target_date_str = payload.get("date")
    if target_date_str:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    else:
        target_date = datetime.now().date() - timedelta(days=1)

    try:
        detail = settle_t_plus_1_by_operator(
            target_date,
            db=db,
            platform_rate_percent=system_param_store.get("settlement_platform_rate", 10),
        )
        if detail["processed_order_count"] == 0:
            return {
                "code": 200,
                "message": f"{target_date} 没有可清分订单，或该日运营商批次已全部生成。",
                "processed": 0,
                "operator_count": 0,
                "data": detail,
            }

        return {
            "code": 200,
            "message": (
                f"清分成功：处理订单 {detail['processed_order_count']} 笔，"
                f"覆盖运营商 {detail['processed_operator_count']} 个。"
            ),
            "processed": detail["processed_order_count"],
            "operator_count": detail["processed_operator_count"],
            "skipped_operator_count": detail["skipped_operator_count"],
            "data": detail,
        }
    except Exception as e:
        return {"code": 500, "message": f"清分引擎执行失败: {str(e)}"}


@api_router.get("/admin/audit/stations", tags=["admin"])
async def get_station_audits(
    _context: RoleContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    stations = (
        db.query(Station)
        .options(joinedload(Station.operator), joinedload(Station.price_template), joinedload(Station.chargers))
        .order_by(Station.created_at.desc())
        .all()
    )

    return {
        "code": 200,
        "data": [serialize_station(station) for station in stations],
    }


@api_router.get("/admin/stations/options", tags=["admin"])
async def get_admin_station_options(
    keyword: str | None = None,
    _context: RoleContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            Station.id.label("id"),
            Station.name.label("station_name"),
        )
        .filter(Station.is_deleted.is_(False))
        .order_by(Station.updated_at.desc(), Station.id.desc())
    )

    if keyword and keyword.strip():
        query = query.filter(Station.name.like(f"%{keyword.strip()}%"))

    return {
        "code": 200,
        "data": [{"id": row.id, "station_name": row.station_name} for row in query.all()],
    }


@api_router.get("/admin/settings/permissions", tags=["admin"])
async def get_admin_permission_settings(_context: RoleContext = Depends(require_admin_context)):
    return {"code": 200, "data": {"modules": permission_settings_store}}


@api_router.put("/admin/settings/permissions", tags=["admin"])
async def update_admin_permission_settings(
    payload: PermissionSettingsPayload,
    _context: RoleContext = Depends(require_admin_context),
):
    permission_settings_store.clear()
    permission_settings_store.extend(payload.modules)
    return {"code": 200, "message": "权限配置已保存", "data": {"modules": permission_settings_store}}


@api_router.get("/admin/settings/params", tags=["admin"])
async def get_admin_system_params(_context: RoleContext = Depends(require_admin_context)):
    return {"code": 200, "data": system_param_store}


@api_router.put("/admin/settings/params", tags=["admin"])
async def update_admin_system_params(
    payload: SystemParamsPayload,
    _context: RoleContext = Depends(require_admin_context),
):
    system_param_store.update(payload.model_dump())
    return {"code": 200, "message": "系统参数已保存", "data": system_param_store}


@api_router.post("/admin/audit/stations/{station_id}/process", tags=["admin"])
async def process_station_audit(
    station_id: int,
    payload: StationAuditProcessPayload,
    _context: RoleContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    action = (payload.action or "").strip().lower()
    remark = (payload.remark or "").strip()

    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        return {"code": 404, "message": "站点不存在"}

    if action == "approve":
        station.status = 0
        station.visibility = "private"
        station.audit_remark = remark or "审核通过，可继续配置电桩并绑定模板"
    elif action == "reject":
        if not remark:
            return {"code": 400, "message": "驳回时请填写原因"}
        station.status = 4
        station.visibility = "private"
        station.audit_remark = remark
    else:
        return {"code": 400, "message": "action 仅支持 approve/reject"}

    db.commit()
    db.refresh(station)
    return {
        "code": 200,
        "message": "站点审核处理成功",
        "data": {
            "id": station.id,
            "status": station.status,
            "status_text": station_status_text(station.status),
            "visibility": station.visibility,
            "visibility_text": visibility_text(station.visibility),
            "remark": station.audit_remark or "",
        },
    }
