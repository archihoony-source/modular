"""FastAPI 진입점.

라우터 등록, 미들웨어, 정적 파일 마운트를 담당.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import close_db_pool, init_db_pool
from app.routers import admin, export, survey

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 DB 풀 관리."""
    await init_db_pool()
    yield
    await close_db_pool()


app = FastAPI(
    title=settings.survey_title,
    description="KICT 차세대 모듈러 건축 핵심기술 수요조사",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None,         # 운영 시 Swagger 비공개
    redoc_url=None,
)

# 세션 미들웨어 (관리자 인증용)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    max_age=60 * 60 * 8,   # 8시간
    same_site="lax",
    https_only=settings.is_production,
)

# 정적 파일
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

# 라우터 등록
app.include_router(survey.router)
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(export.router, prefix="/admin/export", tags=["export"])


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    """Render healthcheck용."""
    return {"status": "ok"}
