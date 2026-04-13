from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.models import Charger, Operator, PriceTemplate, Station


STATION_STATUS_TEXT = {
    0: "已上线",
    1: "停用",
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
}

DEFAULT_TEMPLATE_PRESETS = [
    {
        "name": "城市快充标准模板",
        "peak_price": 1.88,
        "flat_price": 1.34,
        "valley_price": 0.76,
        "service_price": 0.80,
        "scope": "全站",
        "status": "active",
    },
    {
        "name": "园区夜充模板",
        "peak_price": 1.56,
        "flat_price": 1.12,
        "valley_price": 0.58,
        "service_price": 0.65,
        "scope": "指定站点",
        "status": "active",
    },
    {
        "name": "公交车队专属模板",
        "peak_price": 1.68,
        "flat_price": 1.18,
        "valley_price": 0.62,
        "service_price": 0.72,
        "scope": "车队站点",
        "status": "draft",
    },
]


def _now_text(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


def _looks_like_mojibake(value: str | None) -> bool:
    if not value:
        return False
    return any(flag in value for flag in ["鍩", "鍥", "绔", "妯", "鍏", "绀"])


def station_status_text(status: int) -> str:
    return STATION_STATUS_TEXT.get(status, "未知状态")


def visibility_text(visibility: str | None) -> str:
    return VISIBILITY_TEXT.get((visibility or "").lower(), "未知可见性")


def charger_status_text(status: int) -> str:
    return CHARGER_STATUS_TEXT.get(status, "未知状态")


def infer_station_address(station: Station) -> str:
    district = ["南山区", "福田区", "宝安区", "龙华区", "龙岗区"][station.id % 5]
    return f"深圳市{district}示范路{station.id}号 · {station.name}"


def infer_charger_power_kw(charger: Charger) -> int:
    charger_type = (charger.type or "").upper()
    if "AC" in charger_type:
        return 7
    if "DC" in charger_type:
        return 120 if charger.id % 2 == 0 else 90
    return 60


def infer_charger_name(charger: Charger) -> str:
    station_name = charger.station.name[:8] if charger.station and charger.station.name else "示范站"
    suffix = charger.sn_code[-4:] if charger.sn_code else f"{charger.id:04d}"
    return f"{station_name}-{suffix}号桩"


def parse_price_template_rules(template: PriceTemplate | None) -> dict:
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


def ensure_operator_price_templates(db: Session, operator: Operator) -> list[PriceTemplate]:
    templates = (
        db.query(PriceTemplate)
        .filter(PriceTemplate.operator_id == operator.id, PriceTemplate.is_deleted.is_(False))
        .order_by(PriceTemplate.updated_at.desc(), PriceTemplate.id.desc())
        .all()
    )
    if templates:
        dirty = False
        for index, item in enumerate(reversed(templates)):
            preset = DEFAULT_TEMPLATE_PRESETS[min(index, len(DEFAULT_TEMPLATE_PRESETS) - 1)]
            if _looks_like_mojibake(item.name):
                item.name = preset["name"]
                dirty = True
            if not item.rules_json or _looks_like_mojibake(item.rules_json):
                item.rules_json = json.dumps(preset, ensure_ascii=False)
                dirty = True
        if dirty:
            db.commit()
            for item in templates:
                db.refresh(item)
        return templates

    created: list[PriceTemplate] = []
    for preset in DEFAULT_TEMPLATE_PRESETS:
        item = PriceTemplate(
            operator_id=operator.id,
            name=preset["name"],
            rules_json=json.dumps(preset, ensure_ascii=False),
        )
        db.add(item)
        created.append(item)

    db.commit()
    for item in created:
        db.refresh(item)
    return created


def ensure_station_chargers(db: Session, station: Station, count: int = 4) -> list[Charger]:
    if station.chargers:
        return station.chargers

    created: list[Charger] = []
    for index in range(count):
        charger = Charger(
            station_id=station.id,
            sn_code=f"ST{station.id:03d}CH{index + 1:02d}",
            type="DC" if index % 2 == 0 else "AC",
            status=0,
        )
        db.add(charger)
        created.append(charger)

    db.commit()
    db.refresh(station)
    return station.chargers


def ensure_operator_demo_assets(db: Session, operator: Operator) -> dict:
    templates = ensure_operator_price_templates(db, operator)
    stations = (
        db.query(Station)
        .filter(Station.operator_id == operator.id, Station.is_deleted.is_(False))
        .order_by(Station.created_at.asc())
        .all()
    )

    if not stations:
        stations = []
        seed_statuses = [0, 3, 4]
        seed_names = ["科技园旗舰站", "湾区综合补能站", "城际枢纽示范站"]
        for index, status in enumerate(seed_statuses):
            station = Station(
                operator_id=operator.id,
                template_id=templates[0].id if status == 0 else None,
                name=f"{operator.name[:6]}{seed_names[index]}",
                longitude=Decimal(f"113.9{index + 1}1234"),
                latitude=Decimal(f"22.5{index + 1}1234"),
                status=status,
                visibility="public" if status == 0 else "private",
            )
            db.add(station)
            stations.append(station)
        db.commit()
        for station in stations:
            db.refresh(station)

    for station in stations:
        ensure_station_chargers(db, station)

    return {"stations": stations, "templates": templates}


def serialize_price_template(template: PriceTemplate) -> dict:
    rules = parse_price_template_rules(template)
    return {
        "id": template.id,
        "name": template.name,
        "peak_price": rules["peak_price"],
        "flat_price": rules["flat_price"],
        "valley_price": rules["valley_price"],
        "service_price": rules["service_price"],
        "scope": rules["scope"],
        "status": rules["status"],
        "updated_at": _now_text(template.updated_at),
    }


def serialize_operator_station(station: Station) -> dict:
    return {
        "id": station.id,
        "station_name": station.name,
        "operator_name": station.operator.name if station.operator else "",
        "address": infer_station_address(station),
        "status": station.status,
        "status_text": station_status_text(station.status),
        "visibility": station.visibility,
        "visibility_text": visibility_text(station.visibility),
        "charger_count": len(station.chargers),
        "price_template_id": station.template_id,
        "price_template_name": station.price_template.name if station.price_template else "未绑定模板",
        "created_at": _now_text(station.created_at),
        "updated_at": _now_text(station.updated_at),
    }


def serialize_operator_charger(charger: Charger) -> dict:
    return {
        "id": charger.id,
        "sn_code": charger.sn_code,
        "charger_name": infer_charger_name(charger),
        "type": charger.type,
        "power_kw": infer_charger_power_kw(charger),
        "status": charger.status,
        "status_text": charger_status_text(charger.status),
        "station_id": charger.station_id,
        "station_name": charger.station.name if charger.station else "",
        "updated_at": _now_text(charger.updated_at),
    }
