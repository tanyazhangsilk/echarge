from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

def _with_charset(url: str) -> str:
    if "?" in url:
        return url
    return f"{url}?charset=utf8mb4"

engine = create_engine(
    _with_charset(settings.database_url),
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
