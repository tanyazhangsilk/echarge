# seed_extra_orders.py
import random
import uuid
from datetime import datetime, timedelta
from app.db.database import SessionLocal
from app.models.models import Order, User, Charger, Operator

def seed_extra():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        charger = db.query(Charger).first()
        operator = db.query(Operator).first()
        
        if not all([user, charger, operator]):
            print("请先运行基础的 seed_data.py 生成基础数据！")
            return

        now = datetime.now()
        
        # 1. 生成 15 笔实时订单 (status = 0)
        print("正在生成实时订单...")
        for i in range(15):
            start = now - timedelta(minutes=random.randint(5, 120))
            order = Order(
                order_no=f"RT{uuid.uuid4().hex[:12].upper()}",
                user_id=user.id,
                charger_id=charger.id,
                operator_id=operator.id,
                start_time=start,
                total_kwh=round(random.uniform(5.0, 40.0), 2),
                ele_fee=round(random.uniform(10.0, 50.0), 2),
                service_fee=round(random.uniform(2.0, 15.0), 2),
                total_fee=round(random.uniform(12.0, 65.0), 2),
                status=0, # 进行中
                settle_status=0
            )
            db.add(order)
            
        # 2. 生成 10 笔异常订单 (status = 2)
        print("正在生成异常订单...")
        for i in range(10):
            start = now - timedelta(days=random.randint(1, 5), hours=random.randint(1, 10))
            end = start + timedelta(minutes=random.randint(1, 10)) # 异常订单通常很快结束
            order = Order(
                order_no=f"ERR{uuid.uuid4().hex[:12].upper()}",
                user_id=user.id,
                charger_id=charger.id,
                operator_id=operator.id,
                start_time=start,
                end_time=end,
                total_kwh=round(random.uniform(0.1, 2.0), 2), # 异常订单电量通常很小
                total_fee=round(random.uniform(1.0, 5.0), 2),
                status=2, # 异常
                settle_status=0
            )
            db.add(order)
            
        db.commit()
        print("✅ 成功！实时订单与异常订单已入库！")
    except Exception as e:
        db.rollback()
        print(f"❌ 失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_extra()