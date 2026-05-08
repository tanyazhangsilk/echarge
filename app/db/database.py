from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

def _with_charset(url: str) -> str:
    if "?" in url:
        return url
    return f"{url}?charset=utf8mb4"

database_url = _with_charset(settings.database_url)
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_timeout": 5,
}
if database_url.startswith("mysql"):
    # 避免 MySQL 不可达时长时间阻塞，触发前端请求超时。
    engine_kwargs["connect_args"] = {
        "connect_timeout": 3,
        "read_timeout": 8,
        "write_timeout": 8,
    }

engine = create_engine(
    database_url,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
