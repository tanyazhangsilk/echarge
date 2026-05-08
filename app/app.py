import sys
from pathlib import Path

# Ensure project root on sys.path for consistent imports
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.demo_routes import demo_api_router
from app.api.v1.routes import api_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(demo_api_router, prefix=settings.API_V1_PREFIX)
