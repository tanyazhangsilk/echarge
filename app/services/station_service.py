from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.models import Charger, Operator, PriceTemplate, Station


STATION_STATUS_TEXT = {
    0: "已审核通过",
    1: "已停用",
    2: "维护中",
    3: "待审核",
    4: "已驳回",
}

VISIBILITY_TEXT = {
    "public": "公开站点",
    "private": "私有站点",
}

CHARGER_STATUS_TEXT = {
    0: "空闲",
    1: "充电中",
    2: "故障",
    3: "停用",
}


def _normalize_page(page: int | None, page_size: int | None, *, default_size: int = 10, max_size: int = 100) -> tuple[int, int]:
    safe_page = max(int(page or 1), 1)
    safe_page_size = max(int(page_size or default_size), 1)
    return safe_page, min(safe_page_size, max_size)


def station_status_text(status: int) -> str:
    return STATION_STATUS_TEXT.get(status, "未知状态")


def visibility_text(visibility: str | None) -> str:
    return VISIBILITY_TEXT.get((visibility or "").lower(), "未知可见性")


def charger_status_text(status: int) -> str:
    return CHARGER_STATUS_TEXT.get(status, "未知状态")


def normalize_source_site_photos(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
        return [item.strip() for item in stripped.replace("\r", "\n").split("\n") if item.strip()]
    return []


def dump_site_photos(value: Any) -> str:
    return json.dumps(normalize_source_site_photos(value), ensure_ascii=False)


def compose_station_address(station: Station) -> str:
    parts = [station.province, station.city, station.district, station.address]
    joined = "".join([part for part in parts if part])
    if joined:
        return joined
    return f"演示地址 {station.id} 号"


def infer_charger_power_kw_by_type(charger_type: str | None) -> Decimal:
    normalized = (charger_type or "").upper()
    if normalized == "AC":
        return Decimal("7")
    if normalized == "DC":
        return Decimal("120")
    return Decimal("60")


def get_charger_power_kw(charger: Charger) -> Decimal:
    if charger.power_kw is not None:
        return Decimal(str(charger.power_kw))
    return infer_charger_power_kw_by_type(charger.type)


def build_charger_name(station_name: str, sn_code: str | None, charger_id: int | None = None) -> str:
    if sn_code:
        suffix = sn_code[-4:]
    else:
        suffix = f"{charger_id or 0:04d}"
    return f"{station_name[:8] or '充电站'}-{suffix}号桩"


def get_charger_name(charger: Charger) -> str:
    if charger.name:
        return charger.name
    station_name = charger.station.name if charger.station else "充电站"
    return build_charger_name(station_name, charger.sn_code, charger.id)


def parse_price_template_rules(template: PriceTemplate | None) -> dict[str, Any]:
    defaults = {
        "peak_price": 1.68,
        "flat_price": 1.18,
        "valley_price": 0.68,
        "service_price": 0.72,
        "scope": "全站",
        "status": "active",
    }
    if not template or not template.rules_json:
        return defaults

    try:
        data = json.loads(template.rules_json)
    except Exception:
        return defaults

    return {
        "peak_price": float(data.get("peak_price", defaults["peak_price"])),
        "flat_price": float(data.get("flat_price", defaults["flat_price"])),
        "valley_price": float(data.get("valley_price", defaults["valley_price"])),
        "service_price": float(data.get("service_price", defaults["service_price"])),
        "scope": data.get("scope", defaults["scope"]),
        "status": data.get("status", defaults["status"]),
    }


def serialize_station(station: Station, *, charger_count: int | None = None) -> dict[str, Any]:
    resolved_charger_count = charger_count if charger_count is not None else len(station.chargers or [])
    resolved_visibility = station.visibility
    if station.status != 0 and resolved_visibility == "public":
        resolved_visibility = "private"

    return {
        "id": station.id,
        "station_name": station.name,
        "operator_id": station.operator_id,
        "operator_name": station.operator.name if station.operator else "",
        "province": station.province or "",
        "city": station.city or "",
        "district": station.district or "",
        "address": station.address or "",
        "full_address": compose_station_address(station),
        "longitude": float(station.longitude or 0),
        "latitude": float(station.latitude or 0),
        "lng": float(station.longitude or 0),
        "lat": float(station.latitude or 0),
        "contact_name": station.contact_name or "",
        "contact_phone": station.contact_phone or "",
        "operation_hours": station.operation_hours or "",
        "parking_fee_desc": station.parking_fee_desc or "",
        "station_remark": station.station_remark or "",
        "planned_charger_count": int(station.planned_charger_count or 0),
        "planned_piles": int(station.planned_charger_count or 0),
        "total_power_kw": float(station.total_power_kw or 0),
        "total_power": float(station.total_power_kw or 0),
        "cover_image": station.cover_image or "",
        "site_photos": normalize_source_site_photos(station.site_photos_json),
        "qualification_remark": station.qualification_remark or "",
        "audit_remark": station.audit_remark or "",
        "status": station.status,
        "status_text": station_status_text(station.status),
        "visibility": resolved_visibility,
        "visibility_text": visibility_text(resolved_visibility),
        "charger_count": int(resolved_charger_count),
        "price_template_id": station.template_id,
        "price_template_name": station.price_template.name if station.price_template else "未绑定模板",
        "created_at": station.created_at.strftime("%Y-%m-%d %H:%M:%S") if station.created_at else "",
        "updated_at": station.updated_at.strftime("%Y-%m-%d %H:%M:%S") if station.updated_at else "",
        "can_bind_template": station.status == 0,
        "can_manage_chargers": station.status == 0,
        "can_publish": station.status == 0,
    }


def serialize_charger(charger: Charger) -> dict[str, Any]:
    return {
        "id": charger.id,
        "sn_code": charger.sn_code,
        "charger_name": get_charger_name(charger),
        "type": charger.type,
        "power_kw": float(get_charger_power_kw(charger)),
        "status": charger.status,
        "status_text": charger_status_text(charger.status),
        "station_id": charger.station_id,
        "station_name": charger.station.name if charger.station else "",
        "updated_at": charger.updated_at.strftime("%Y-%m-%d %H:%M:%S") if charger.updated_at else "",
    }


def serialize_station_row(row: Any) -> dict[str, Any]:
    resolved_visibility = row.visibility
    if row.status != 0 and resolved_visibility == "public":
        resolved_visibility = "private"

    full_address = "".join([part for part in [row.province, row.city, row.district, row.address] if part]) or f"演示地址 {row.id} 号"
    return {
        "id": row.id,
        "station_name": row.station_name,
        "operator_id": row.operator_id,
        "operator_name": row.operator_name or "",
        "province": row.province or "",
        "city": row.city or "",
        "district": row.district or "",
        "address": row.address or "",
        "full_address": full_address,
        "longitude": float(row.longitude or 0),
        "latitude": float(row.latitude or 0),
        "lng": float(row.longitude or 0),
        "lat": float(row.latitude or 0),
        "contact_name": row.contact_name or "",
        "contact_phone": row.contact_phone or "",
        "operation_hours": row.operation_hours or "",
        "parking_fee_desc": row.parking_fee_desc or "",
        "station_remark": row.station_remark or "",
        "planned_charger_count": int(row.planned_charger_count or 0),
        "planned_piles": int(row.planned_charger_count or 0),
        "total_power_kw": float(row.total_power_kw or 0),
        "total_power": float(row.total_power_kw or 0),
        "cover_image": row.cover_image or "",
        "site_photos": normalize_source_site_photos(row.site_photos_json),
        "qualification_remark": row.qualification_remark or "",
        "audit_remark": row.audit_remark or "",
        "status": row.status,
        "status_text": station_status_text(row.status),
        "visibility": resolved_visibility,
        "visibility_text": visibility_text(resolved_visibility),
        "charger_count": int(row.charger_count or 0),
        "price_template_id": row.template_id,
        "price_template_name": row.price_template_name or "未绑定模板",
        "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else "",
        "updated_at": row.updated_at.strftime("%Y-%m-%d %H:%M:%S") if row.updated_at else "",
        "can_bind_template": row.status == 0,
        "can_manage_chargers": row.status == 0,
        "can_publish": row.status == 0,
    }


def get_operator_station_page(
    db: Session,
    *,
    operator_id: int,
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    status: int | None = None,
    visibility: str | None = None,
) -> dict[str, Any]:
    safe_page, safe_page_size = _normalize_page(page, page_size)
    charger_count_subquery = (
        db.query(
            Charger.station_id.label("station_id"),
            func.count(Charger.id).label("charger_count"),
        )
        .group_by(Charger.station_id)
        .subquery()
    )

    query = (
        db.query(
            Station.id.label("id"),
            Station.operator_id.label("operator_id"),
            Station.template_id.label("template_id"),
            Station.name.label("station_name"),
            Station.province.label("province"),
            Station.city.label("city"),
            Station.district.label("district"),
            Station.address.label("address"),
            Station.longitude.label("longitude"),
            Station.latitude.label("latitude"),
            Station.contact_name.label("contact_name"),
            Station.contact_phone.label("contact_phone"),
            Station.operation_hours.label("operation_hours"),
            Station.parking_fee_desc.label("parking_fee_desc"),
            Station.station_remark.label("station_remark"),
            Station.planned_charger_count.label("planned_charger_count"),
            Station.total_power_kw.label("total_power_kw"),
            Station.cover_image.label("cover_image"),
            Station.site_photos_json.label("site_photos_json"),
            Station.qualification_remark.label("qualification_remark"),
            Station.audit_remark.label("audit_remark"),
            Station.status.label("status"),
            Station.visibility.label("visibility"),
            Station.created_at.label("created_at"),
            Station.updated_at.label("updated_at"),
            func.coalesce(charger_count_subquery.c.charger_count, 0).label("charger_count"),
            Operator.name.label("operator_name"),
            PriceTemplate.name.label("price_template_name"),
        )
        .select_from(Station)
        .join(Operator, Station.operator_id == Operator.id)
        .outerjoin(PriceTemplate, Station.template_id == PriceTemplate.id)
        .outerjoin(charger_count_subquery, charger_count_subquery.c.station_id == Station.id)
        .filter(Station.operator_id == operator_id, Station.is_deleted.is_(False))
    )

    if keyword and keyword.strip():
        search = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Station.name.like(search),
                Station.address.like(search),
                Station.province.like(search),
                Station.city.like(search),
                Station.district.like(search),
                PriceTemplate.name.like(search),
            )
        )

    if status is not None:
        query = query.filter(Station.status == status)

    if visibility and visibility.strip():
        normalized_visibility = visibility.strip().lower()
        query = query.filter(Station.visibility == normalized_visibility)
        if normalized_visibility == "public":
            query = query.filter(Station.status == 0)

    total = query.order_by(None).count()
    rows = (
        query.order_by(Station.updated_at.desc(), Station.id.desc())
        .offset((safe_page - 1) * safe_page_size)
        .limit(safe_page_size)
        .all()
    )

    summary_row = (
        db.query(
            func.count(Station.id),
            func.coalesce(func.sum(case((Station.status == 0, 1), else_=0)), 0),
            func.coalesce(func.sum(case((Station.status == 3, 1), else_=0)), 0),
            func.coalesce(func.sum(case((Station.visibility == "private", 1), else_=0)), 0),
        )
        .filter(Station.operator_id == operator_id, Station.is_deleted.is_(False))
        .one()
    )

    return {
        "items": [serialize_station_row(row) for row in rows],
        "total": int(total),
        "page": safe_page,
        "page_size": safe_page_size,
        "summary": {
            "total_count": int(summary_row[0] or 0),
            "online_count": int(summary_row[1] or 0),
            "pending_count": int(summary_row[2] or 0),
            "private_count": int(summary_row[3] or 0),
        },
    }


def get_operator_station_options(db: Session, *, operator_id: int, keyword: str | None = None) -> list[dict[str, Any]]:
    query = (
        db.query(
            Station.id.label("id"),
            Station.name.label("station_name"),
            Station.status.label("status"),
        )
        .filter(Station.operator_id == operator_id, Station.is_deleted.is_(False))
        .order_by(Station.updated_at.desc(), Station.id.desc())
    )
    if keyword and keyword.strip():
        search = f"%{keyword.strip()}%"
        query = query.filter(or_(Station.name.like(search), Station.address.like(search)))

    return [
        {
            "id": station.id,
            "station_name": station.station_name,
            "status": station.status,
            "status_text": station_status_text(station.status),
        }
        for station in query.all()
    ]


def create_station_charger(
    db: Session,
    *,
    station: Station,
    sn_code: str,
    charger_name: str,
    charger_type: str,
    power_kw: Decimal,
    status: int = 0,
) -> Charger:
    charger = Charger(
        station_id=station.id,
        sn_code=sn_code,
        name=charger_name,
        type=charger_type,
        power_kw=power_kw,
        status=status,
    )
    db.add(charger)
    station.planned_charger_count = max(int(station.planned_charger_count or 0), len(station.chargers or []) + 1)
    current_total = Decimal(str(station.total_power_kw or 0))
    station.total_power_kw = current_total + Decimal(str(power_kw))
    db.commit()
    db.refresh(charger)
    return charger


def batch_create_station_chargers(
    db: Session,
    *,
    station: Station,
    count: int,
    charger_type: str,
    power_kw: Decimal,
) -> list[Charger]:
    created: list[Charger] = []
    existing_count = db.query(func.count(Charger.id)).filter(Charger.station_id == station.id).scalar() or 0

    for index in range(count):
        sequence = existing_count + index + 1
        sn_code = f"ST{station.id:03d}{charger_type.upper()}{sequence:03d}"
        charger = Charger(
            station_id=station.id,
            sn_code=sn_code,
            name=f"{station.name[:10]}-{sequence:02d}号桩",
            type=charger_type,
            power_kw=power_kw,
            status=0,
        )
        db.add(charger)
        created.append(charger)

    station.planned_charger_count = max(int(station.planned_charger_count or 0), existing_count + count)
    station.total_power_kw = Decimal(str(station.total_power_kw or 0)) + Decimal(str(power_kw)) * Decimal(str(count))
    db.commit()
    for charger in created:
        db.refresh(charger)
    return created


def update_station_charger(charger: Charger, *, charger_name: str | None = None, status: int | None = None) -> Charger:
    if charger_name is not None:
        charger.name = charger_name
    if status is not None:
        charger.status = status
    return charger
