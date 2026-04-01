import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class BaseModel:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        comment="最后更新时间",
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

    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, comment="手机号")
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="用户昵称")
    password_hash: Mapped[str] = mapped_column(String(255), comment="密码哈希")
    vin_code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True, comment="车辆VIN")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="用户状态")
    role: Mapped[str] = mapped_column(String(20), default="user", comment="用户角色")

    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user", lazy="selectin")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="user", lazy="selectin")
    wallet_transactions: Mapped[List["WalletTransaction"]] = relationship(
        "WalletTransaction",
        back_populates="user",
        lazy="selectin",
    )
    user_coupons: Mapped[List["UserCoupon"]] = relationship("UserCoupon", back_populates="user", lazy="selectin")
    member_of_fleets: Mapped[List["Fleet"]] = relationship(
        "Fleet",
        secondary=user_fleet_association,
        back_populates="members",
        lazy="selectin",
    )


class Operator(Base, BaseModel):
    __tablename__ = "sys_operators"

    name: Mapped[str] = mapped_column(String(100), comment="运营商名称")
    org_type: Mapped[str] = mapped_column(String(50), comment="组织类型")
    license_url: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="营业执照URL")
    bank_account: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="银行账户")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已认证")

    fleets: Mapped[List["Fleet"]] = relationship("Fleet", back_populates="operator", lazy="selectin")
    stations: Mapped[List["Station"]] = relationship("Station", back_populates="operator", lazy="selectin")
    price_templates: Mapped[List["PriceTemplate"]] = relationship(
        "PriceTemplate", back_populates="operator", lazy="selectin"
    )
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="operator", lazy="selectin")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="operator", lazy="selectin")
    bank_cards: Mapped[List["OperatorBankCard"]] = relationship(
        "OperatorBankCard",
        back_populates="operator",
        lazy="selectin",
    )
    coupons: Mapped[List["Coupon"]] = relationship("Coupon", back_populates="operator", lazy="selectin")


class Fleet(Base, BaseModel):
    __tablename__ = "busi_fleets"

    operator_id: Mapped[int] = mapped_column(ForeignKey("sys_operators.id"), comment="所属运营商ID")
    name: Mapped[str] = mapped_column(String(100), comment="车队名称")
    is_whitelist: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否白名单车队")

    operator: Mapped["Operator"] = relationship("Operator", back_populates="fleets", lazy="joined")
    members: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_fleet_association,
        back_populates="member_of_fleets",
        lazy="selectin",
    )


class Station(Base, BaseModel):
    __tablename__ = "eq_stations"

    operator_id: Mapped[int] = mapped_column(ForeignKey("sys_operators.id"), comment="所属运营商ID")
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("busi_price_templates.id"),
        nullable=True,
        comment="计费模板ID",
    )
    name: Mapped[str] = mapped_column(String(100), comment="充电站名称")
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), comment="经度")
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), comment="纬度")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="充电站状态")
    visibility: Mapped[str] = mapped_column(String(20), default="public", comment="可见性")

    operator: Mapped["Operator"] = relationship("Operator", back_populates="stations", lazy="joined")
    price_template: Mapped["PriceTemplate"] = relationship(
        "PriceTemplate", back_populates="stations", lazy="joined"
    )
    chargers: Mapped[List["Charger"]] = relationship("Charger", back_populates="station", lazy="selectin")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="station", lazy="selectin")


class Charger(Base, BaseModel):
    __tablename__ = "eq_chargers"

    station_id: Mapped[int] = mapped_column(ForeignKey("eq_stations.id"), comment="所属充电站ID")
    sn_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment="充电桩序列号")
    type: Mapped[str] = mapped_column(String(20), comment="充电桩类型")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="充电桩状态")

    station: Mapped["Station"] = relationship("Station", back_populates="chargers", lazy="joined")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="charger", lazy="selectin")


class PriceTemplate(Base, BaseModel):
    __tablename__ = "busi_price_templates"

    operator_id: Mapped[int] = mapped_column(ForeignKey("sys_operators.id"), comment="所属运营商ID")
    name: Mapped[str] = mapped_column(String(100), comment="模板名称")
    rules_json: Mapped[str] = mapped_column(Text, comment="计费规则JSON")

    operator: Mapped["Operator"] = relationship("Operator", back_populates="price_templates", lazy="joined")
    stations: Mapped[List["Station"]] = relationship("Station", back_populates="price_template", lazy="selectin")


class Order(Base, BaseModel):
    __tablename__ = "trade_orders"
    __table_args__ = (
        Index("ix_trade_orders_station_id", "station_id"),
        Index("ix_trade_orders_status", "status"),
        Index("ix_trade_orders_created_at", "created_at"),
    )

    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="订单号")
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_users.id"), comment="用户ID")
    operator_id: Mapped[int] = mapped_column(ForeignKey("sys_operators.id"), comment="运营商ID")
    station_id: Mapped[int | None] = mapped_column(ForeignKey("eq_stations.id"), nullable=True, comment="电站ID")
    charger_id: Mapped[int] = mapped_column(ForeignKey("eq_chargers.id"), comment="充电桩ID")
    vin: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="车辆VIN")
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime, comment="开始充电时间")
    end_time: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True, comment="结束充电时间")
    charge_duration: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="充电时长(分钟)")
    total_kwh: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), comment="充电量(kWh)")
    ele_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), comment="电费")
    service_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), comment="服务费")
    total_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), comment="总金额")
    pay_status: Mapped[int] = mapped_column(Integer, default=0, server_default="0", comment="支付状态")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="订单状态 0-charging 1-completed 2-abnormal")
    abnormal_reason: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="异常原因")
    settle_status: Mapped[int] = mapped_column(Integer, default=0, comment="结算状态")

    user: Mapped["User"] = relationship("User", back_populates="orders", lazy="joined")
    operator: Mapped["Operator"] = relationship("Operator", back_populates="orders", lazy="joined")
    station: Mapped["Station | None"] = relationship("Station", back_populates="orders", lazy="joined")
    charger: Mapped["Charger"] = relationship("Charger", back_populates="orders", lazy="joined")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="related_order", lazy="selectin")
    wallet_transactions: Mapped[List["WalletTransaction"]] = relationship(
        "WalletTransaction",
        back_populates="related_order",
        lazy="selectin",
    )

    @property
    def charge_amount(self) -> Decimal:
        return self.total_kwh

    @property
    def electricity_fee(self) -> Decimal:
        return self.ele_fee

    @property
    def total_amount(self) -> Decimal:
        return self.total_fee

    @property
    def order_status(self) -> str:
        return {0: "charging", 1: "completed", 2: "abnormal"}.get(self.status, "unknown")

    @property
    def settlement_status(self) -> int:
        return self.settle_status


class Invoice(Base, BaseModel):
    __tablename__ = "trade_invoices"
    __table_args__ = (
        Index("ix_trade_invoices_order_id", "order_id"),
        Index("ix_trade_invoices_status", "status"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("sys_users.id"), comment="申请用户ID")
    operator_id: Mapped[int] = mapped_column(ForeignKey("sys_operators.id"), comment="开票运营商ID")
    order_id: Mapped[int | None] = mapped_column(ForeignKey("trade_orders.id"), nullable=True, comment="关联订单ID")
    invoice_title: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="发票抬头")
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), comment="发票金额")
    email: Mapped[str] = mapped_column(String(100), comment="接收邮箱")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="发票状态")
    file_url: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="发票文件URL")
    uploaded_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True, comment="上传时间")
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="备注")

    user: Mapped["User"] = relationship("User", back_populates="invoices", lazy="joined")
    operator: Mapped["Operator"] = relationship("Operator", back_populates="invoices", lazy="joined")
    related_order: Mapped["Order | None"] = relationship("Order", back_populates="invoices", lazy="joined")


class OperatorBankCard(Base):
    __tablename__ = "sys_operator_bank_cards"
    __table_args__ = (
        Index("ix_sys_operator_bank_cards_operator_id", "operator_id"),
        Index("ix_sys_operator_bank_cards_bind_status", "bind_status"),
        Index("ix_sys_operator_bank_cards_is_default", "is_default"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    operator_id: Mapped[int] = mapped_column(ForeignKey("sys_operators.id"), comment="运营商ID")
    account_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="开户名")
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="银行名称")
    bank_account: Mapped[str] = mapped_column(String(100), nullable=False, comment="银行卡号")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否默认卡")
    bind_status: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="绑卡状态")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        comment="最后更新时间",
    )

    operator: Mapped["Operator"] = relationship("Operator", back_populates="bank_cards", lazy="joined")


class WalletTransaction(Base):
    __tablename__ = "trade_wallet_transactions"
    __table_args__ = (
        Index("ix_trade_wallet_transactions_user_id", "user_id"),
        Index("ix_trade_wallet_transactions_created_at", "created_at"),
        Index("ix_trade_wallet_transactions_transaction_type", "transaction_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_users.id"), comment="用户ID")
    transaction_type: Mapped[str] = mapped_column(String(20), comment="流水类型")
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="变动金额")
    balance_after: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="变动后余额")
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="备注")
    related_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("trade_orders.id"),
        nullable=True,
        comment="关联订单ID",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), comment="创建时间")

    user: Mapped["User"] = relationship("User", back_populates="wallet_transactions", lazy="joined")
    related_order: Mapped["Order | None"] = relationship("Order", back_populates="wallet_transactions", lazy="joined")


class Coupon(Base, BaseModel):
    __tablename__ = "mkt_coupons"

    operator_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_operators.id"),
        nullable=True,
        comment="所属运营商ID",
    )
    type: Mapped[str] = mapped_column(String(50), comment="优惠券类型")
    discount_val: Mapped[Decimal] = mapped_column(Numeric(10, 2), comment="优惠值")

    operator: Mapped["Operator"] = relationship("Operator", back_populates="coupons", lazy="joined")
    user_coupons: Mapped[List["UserCoupon"]] = relationship("UserCoupon", back_populates="coupon", lazy="selectin")


class UserCoupon(Base, BaseModel):
    __tablename__ = "mkt_user_coupons"

    user_id: Mapped[int] = mapped_column(ForeignKey("sys_users.id"), comment="用户ID")
    coupon_id: Mapped[int] = mapped_column(ForeignKey("mkt_coupons.id"), comment="优惠券ID")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="使用状态")

    user: Mapped["User"] = relationship("User", back_populates="user_coupons", lazy="joined")
    coupon: Mapped["Coupon"] = relationship("Coupon", back_populates="user_coupons", lazy="joined")


class SettlementRecord(Base):
    __tablename__ = "trade_settlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    settle_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True, unique=True, comment="清分日期")
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="订单数量")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="订单总金额")
    platform_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="平台抽成")
    settle_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="应结金额")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="打款状态")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        comment="最后更新时间",
    )
