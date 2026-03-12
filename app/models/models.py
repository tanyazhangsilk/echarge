import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Boolean,
    Numeric,
    JSON,
    Text,
    func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    """SQLAlchemy 声明性基类"""
    pass

class BaseModel:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=func.now(),
        comment="创建时间"
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        comment="最后更新时间"
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="逻辑删除标记")

user_fleet_association = Table(
    "busi_user_fleet_association",
    Base.metadata,
    Column("user_id", ForeignKey("sys_users.id"), primary_key=True, comment="用户ID"),
    Column("fleet_id", ForeignKey("busi_fleets.id"), primary_key=True, comment="车队ID"),
)

class User(Base, BaseModel):
    __tablename__ = "sys_users"

    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, comment="手机号 (唯一)")
    nickname: Mapped[str] = mapped_column(String(50), nullable=True, comment="用户昵称")
    password_hash: Mapped[str] = mapped_column(String(255), comment="哈希后的密码")
    vin_code: Mapped[str] = mapped_column(String(50), nullable=True, index=True, comment="车辆识别码 (VIN)")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="用户状态 (例如: 0-正常, 1-禁用)")
    role: Mapped[str] = mapped_column(String(20), default="user", comment="用户角色 (admin/operator/user)")

    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user", lazy="selectin")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="user", lazy="selectin")
    user_coupons: Mapped[List["UserCoupon"]] = relationship("UserCoupon", back_populates="user", lazy="selectin")
    member_of_fleets: Mapped[List["Fleet"]] = relationship(
        "Fleet",
        secondary=user_fleet_association,
        back_populates="members",
        lazy="selectin"
    )

class Operator(Base, BaseModel):
    __tablename__ = "sys_operators"

    name: Mapped[str] = mapped_column(String(100), comment="运营商名称")
    org_type: Mapped[str] = mapped_column(String(50), comment="组织类型 (例如: '企业', '个人')")
    license_url: Mapped[str] = mapped_column(String(255), nullable=True, comment="营业执照图片URL")
    bank_account: Mapped[str] = mapped_column(String(100), nullable=True, comment="银行账户")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已认证")

    fleets: Mapped[List["Fleet"]] = relationship("Fleet", back_populates="operator", lazy="selectin")
    stations: Mapped[List["Station"]] = relationship("Station", back_populates="operator", lazy="selectin")
    price_templates: Mapped[List["PriceTemplate"]] = relationship("PriceTemplate", back_populates="operator", lazy="selectin")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="operator", lazy="selectin")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="operator", lazy="selectin")
    coupons: Mapped[List["Coupon"]] = relationship("Coupon", back_populates="operator", lazy="selectin")

class Fleet(Base, BaseModel):
    __tablename__ = "busi_fleets"

    operator_id: Mapped[int] = mapped_column(ForeignKey("sys_operators.id"), comment="所属运营商ID")
    name: Mapped[str] = mapped_column(String(100), comment="车队名称")
    is_whitelist: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为白名单车队")

    operator: Mapped["Operator"] = relationship("Operator", back_populates="fleets", lazy="joined")
    members: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_fleet_association,
        back_populates="member_of_fleets",
        lazy="selectin"
    )

class Station(Base, BaseModel):
    __tablename__ = "eq_stations"

    operator_id: Mapped[int] = mapped_column(ForeignKey("sys_operators.id"), comment="所属运营商ID")
    template_id: Mapped[int] = mapped_column(ForeignKey("busi_price_templates.id"), nullable=True, comment="计费模板ID")
    name: Mapped[str] = mapped_column(String(100), comment="充电站名称")
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), comment="经度")
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), comment="纬度")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="充电站状态 (例如: 0-运营, 1-建设中, 2-关闭)")
    visibility: Mapped[str] = mapped_column(String(20), default="public", comment="可见性 (public/private)")

    operator: Mapped["Operator"] = relationship("Operator", back_populates="stations", lazy="joined")
    price_template: Mapped["PriceTemplate"] = relationship("PriceTemplate", back_populates="stations", lazy="joined")
    chargers: Mapped[List["Charger"]] = relationship("Charger", back_populates="station", lazy="selectin")

class Charger(Base, BaseModel):
    __tablename__ = "eq_chargers"

    station_id: Mapped[int] = mapped_column(ForeignKey("eq_stations.id"), comment="所属充电站ID")
    sn_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment="充电桩序列号 (唯一)")
    type: Mapped[str] = mapped_column(String(20), comment="充电桩类型 (例如: 'AC'-交流, 'DC'-直流)")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="充电桩状态 (例如: 0-空闲, 1-充电中, 2-故障)")

    station: Mapped["Station"] = relationship("Station", back_populates="chargers", lazy="joined")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="charger", lazy="selectin")

class PriceTemplate(Base, BaseModel):
    __tablename__ = "busi_price_templates"

    operator_id: Mapped[int] = mapped_column(ForeignKey("sys_operators.id"), comment="所属运营商ID")
    name: Mapped[str] = mapped_column(String(100), comment="模板名称")
    rules_json: Mapped[dict] = mapped_column(Text, comment="计费规则 (JSON格式)")

    operator: Mapped["Operator"] = relationship("Operator", back_populates="price_templates", lazy="joined")
    stations: Mapped[List["Station"]] = relationship("Station", back_populates="price_template", lazy="selectin")

class Order(Base, BaseModel):
    __tablename__ = "trade_orders"

    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="订单号 (唯一)")
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_users.id"), comment="用户ID")
    charger_id: Mapped[int] = mapped_column(ForeignKey("eq_chargers.id"), comment="充电桩ID")
    operator_id: Mapped[int] = mapped_column(ForeignKey("sys_operators.id"), comment="运营商ID")
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime, comment="充电开始时间")
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, comment="充电结束时间")
    total_kwh: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.0"), comment="总充电度数 (kWh)")
    ele_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.0"), comment="电费 (元)")
    service_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.0"), comment="服务费 (元)")
    total_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.0"), comment="总费用 (元)")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="订单状态 (例如: 0-进行中, 1-已完成, 2-异常)")
    settle_status: Mapped[int] = mapped_column(Integer, default=0, comment="结算状态 (例如: 0-未结算, 1-已结算)")

    user: Mapped["User"] = relationship("User", back_populates="orders", lazy="joined")
    charger: Mapped["Charger"] = relationship("Charger", back_populates="orders", lazy="joined")
    operator: Mapped["Operator"] = relationship("Operator", back_populates="orders", lazy="joined")

class Invoice(Base, BaseModel):
    __tablename__ = "trade_invoices"

    user_id: Mapped[int] = mapped_column(ForeignKey("sys_users.id"), comment="申请用户ID")
    operator_id: Mapped[int] = mapped_column(ForeignKey("sys_operators.id"), comment="开票运营商ID")
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), comment="发票金额")
    email: Mapped[str] = mapped_column(String(100), comment="接收邮箱")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="开票状态 (例如: 0-申请中, 1-已开票, 2-失败)")
    file_url: Mapped[str] = mapped_column(String(255), nullable=True, comment="发票文件URL")

    user: Mapped["User"] = relationship("User", back_populates="invoices", lazy="joined")
    operator: Mapped["Operator"] = relationship("Operator", back_populates="invoices", lazy="joined")

class Coupon(Base, BaseModel):
    __tablename__ = "mkt_coupons"

    operator_id: Mapped[int] = mapped_column(ForeignKey("sys_operators.id"), nullable=True, comment="所属运营商ID (空则为平台券)")
    type: Mapped[str] = mapped_column(String(50), comment="优惠券类型 (例如: 'discount'-折扣, 'cash'-代金券)")
    discount_val: Mapped[Decimal] = mapped_column(Numeric(10, 2), comment="折扣或金额值")

    operator: Mapped["Operator"] = relationship("Operator", back_populates="coupons", lazy="joined")
    user_coupons: Mapped[List["UserCoupon"]] = relationship("UserCoupon", back_populates="coupon", lazy="selectin")

class UserCoupon(Base, BaseModel):
    __tablename__ = "mkt_user_coupons"

    user_id: Mapped[int] = mapped_column(ForeignKey("sys_users.id"), comment="用户ID")
    coupon_id: Mapped[int] = mapped_column(ForeignKey("mkt_coupons.id"), comment="优惠券ID")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="使用状态 (例如: 0-未使用, 1-已使用, 2-已过期)")

    user: Mapped["User"] = relationship("User", back_populates="user_coupons", lazy="joined")
    coupon: Mapped["Coupon"] = relationship("Coupon", back_populates="user_coupons", lazy="joined")

class SettlementRecord(Base):
    __tablename__ = "trade_settlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    settle_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True, unique=True, comment="结算日期 (即 T 日)")
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="包含的订单笔数")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="订单总额 (元)")
    platform_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="平台抽成 (元)")
    settle_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="应结算金额 (元)")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="打款状态 (0-待打款, 1-已打款)")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), comment="最后更新时间")
