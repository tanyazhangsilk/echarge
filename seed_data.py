# backend/seed_data.py
import random
import uuid
from datetime import datetime, date, time, timedelta
from faker import Faker
from app.db.database import SessionLocal, engine
from app.models.models import Base, User, Operator, Station, Charger, Order, SettlementRecord
from app.services.settlement_service import settle_t_plus_1

fake = Faker('zh_CN') # 使用中文生成器

def generate_seed_data():
    db = SessionLocal()
    
    try:
        print("清理旧数据 (如果存在)...")
        # 简单粗暴：先清空所有表再重建（注意：这会清空你现有的数据）
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        print("1. 正在生成 运营商...")
        operators = []
        for _ in range(3):
            op = Operator(
                name=fake.company() + "新能源科技有限公司",
                org_type="enterprise",
                is_verified=True
            )
            db.add(op)
            operators.append(op)
        db.commit()

        print("2. 正在生成 充电站和电桩...")
        stations = []
        chargers = []
        for i in range(10):
            op = random.choice(operators)
            station = Station(
                operator_id=op.id,
                name=fake.city() + fake.street_name() + "超级充电站",
                longitude=fake.longitude(),
                latitude=fake.latitude(),
                status=0 # 营业中
            )
            db.add(station)
            db.flush() # 获取 station.id
            stations.append(station)
            
            # 每个电站生成 5 个电桩
            for j in range(5):
                charger = Charger(
                    station_id=station.id,
                    sn_code=f"SN{fake.random_number(digits=8, fix_len=True)}",
                    type=random.choice(["DC", "AC"]),
                    status=0 # 默认空闲
                )
                db.add(charger)
                chargers.append(charger)
        db.commit()

        print("3. 正在生成 用户...")
        users = []
        for _ in range(100):
            user = User(
                phone=fake.phone_number(),
                nickname=fake.name(),
                password_hash="mock_hash_123", # 假密码
                role="user"
            )
            db.add(user)
            users.append(user)
        db.commit()

        print("4. 正在生成 订单 (包含历史和实时)...")
        now = datetime.now()
        
        # 生成 200 条历史订单 (已完成)
        for _ in range(200):
            user = random.choice(users)
            charger = random.choice(chargers)
            start_time = fake.date_time_between(start_date="-30d", end_date="now")
            end_time = start_time + timedelta(minutes=random.randint(20, 120))
            kwh = round(random.uniform(10.0, 60.0), 2)
            fee = round(kwh * 1.5, 2) # 假设1.5元/度
            
            order = Order(
                order_no=str(uuid.uuid4()).replace("-", ""),
                user_id=user.id,
                charger_id=charger.id,
                operator_id=charger.station.operator_id,
                start_time=start_time,
                end_time=end_time,
                total_kwh=kwh,
                total_fee=fee,
                status=1, # 1=已完成
                settle_status=random.choice([0, 1])
            )
            db.add(order)

        # 生成 10 条正在充电的“实时订单”
        for _ in range(10):
            user = random.choice(users)
            charger = random.choice(chargers)
            charger.status = 1 # 把电桩状态改成“充电中”
            start_time = now - timedelta(minutes=random.randint(1, 60))
            kwh = round(random.uniform(1.0, 20.0), 2)
            
            order = Order(
                order_no=str(uuid.uuid4()).replace("-", ""),
                user_id=user.id,
                charger_id=charger.id,
                operator_id=charger.station.operator_id,
                start_time=start_time,
                total_kwh=kwh,
                status=0 # 0=进行中
            )
            db.add(order)

        db.commit()
        print("🎉 太棒了！海量数据生成完毕，你的数据库现在非常丰富了！")

    except Exception as e:
        print(f"生成失败: {e}")
        db.rollback()
    finally:
        db.close()

def generate_wealth_data():
    db = SessionLocal()
    # 1. 明确目标日期：昨天
    yesterday = date.today() - timedelta(days=1)
    
    print(f"💰 正在为 {yesterday} 批量制造 500 笔‘暴富’订单...")
    
    try:
        users = db.query(User).all()
        chargers = db.query(Charger).all()
        
        if not users or not chargers:
            print("❌ 错误：数据库中没有用户或电桩，请先运行基础生成脚本！")
            return

        # 2. 循环生成 100 笔订单
        for i in range(100):
            user = random.choice(users)
            charger = random.choice(chargers)
            
            # 随机生成昨天的具体时间点
            random_hour = random.randint(0, 23)
            random_minute = random.randint(0, 59)
            start_time = datetime.combine(yesterday, time(random_hour, random_minute))
            
            # 设置一个体面的金额：每笔 30-150 元不等
            kwh = round(random.uniform(20.0, 80.0), 2)
            ele_fee = round(kwh * 1.2, 2)    # 电费
            service_fee = round(kwh * 0.6, 2) # 服务费
            total_fee = ele_fee + service_fee
            
            new_order = Order(
                order_no=f"E{yesterday.strftime('%Y%m%d')}{i:04d}{random.randint(10, 99)}",
                user_id=user.id,
                charger_id=charger.id,
                operator_id=charger.station.operator_id,
                start_time=start_time,
                end_time=start_time + timedelta(minutes=random.randint(30, 90)),    
                total_kwh=kwh,
                ele_fee=ele_fee,
                service_fee=service_fee,
                total_fee=total_fee,
                status=1,        # 状态：已完成
                settle_status=0  # 状态：未结算
            )
            db.add(new_order)
        
        db.commit()
        print(f"✅ 成功！昨天的 100 笔订单已入库。")
        print(f"📈 预计总流水：约 {100 * 80} 元（这波稳了！）")

        processed = settle_t_plus_1(yesterday, db=db)
        record = db.query(SettlementRecord).filter(SettlementRecord.settle_date == yesterday).first()
        print(f"🧾 清分已执行：处理 {processed} 笔订单")
        if record:
            print(
                f"🧾 结算记录已生成：date={record.settle_date}, "
                f"order_count={record.order_count}, total_amount={record.total_amount}, "
                f"platform_fee={record.platform_fee}, settle_amount={record.settle_amount}"
            )

    except Exception as e:
        db.rollback()
        print(f"❌ 生成失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    generate_seed_data()
    generate_wealth_data()
