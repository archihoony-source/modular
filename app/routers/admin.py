"""관리자 페이지 라우터.

- GET  /admin/login         : 관리자 로그인 폼
- POST /admin/login         : 비밀번호 검증
- POST /admin/logout        : 로그아웃
- GET  /admin               : 통계 대시보드 (HTML)
- GET  /admin/statistics    : 집계 결과 JSON (Plotly용)
- GET  /admin/responses     : 응답 목록 JSON
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import get_pool
from app.services import statistics

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# ──────────────────────────────────────────────────────────────
# 인증
# ──────────────────────────────────────────────────────────────


def require_admin(request: Request) -> None:
    if not request.session.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="관리자 권한이 필요합니다.",
            headers={"Location": "/admin/login"},
        )


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    if request.session.get("is_admin"):
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={"error": None, "survey_title": settings.survey_title},
    )


@router.post("/login")
async def login_submit(request: Request, password: str = Form(...)):
    if password == settings.admin_password:
        request.session["is_admin"] = True
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={
            "error": "비밀번호가 올바르지 않습니다.",
            "survey_title": settings.survey_title,
        },
        status_code=401,
    )


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)


# ──────────────────────────────────────────────────────────────
# 대시보드 페이지
# ──────────────────────────────────────────────────────────────


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, _: None = Depends(require_admin)):
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={"survey_title": settings.survey_title},
    )


# ──────────────────────────────────────────────────────────────
# 통계 JSON API
# ──────────────────────────────────────────────────────────────


@router.get("/statistics", response_class=JSONResponse)
async def get_statistics(_: None = Depends(require_admin)) -> dict:
    """모든 집계 결과를 한 번에 반환. Plotly가 직접 소비."""
    return await statistics.aggregate_all()


# ──────────────────────────────────────────────────────────────
# 응답 목록
# ──────────────────────────────────────────────────────────────


_LIST_SQL = """
    SELECT id, created_at, project_title, proposer_name,
           proposer_organization, proposer_email,
           research_period_years
    FROM responses
    ORDER BY created_at DESC
    LIMIT %(limit)s OFFSET %(offset)s;
"""


@router.get("/responses", response_class=JSONResponse)
async def list_responses(
    _: None = Depends(require_admin),
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """응답 목록 (관리자 확인용)."""
    limit = max(1, min(500, int(limit)))
    offset = max(0, int(offset))

    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(_LIST_SQL, {"limit": limit, "offset": offset})
            rows = await cur.fetchall()
            cols = [d[0] for d in cur.description]

    items = []
    for row in rows:
        item = dict(zip(cols, row))
        item["id"] = str(item["id"])
        item["created_at"] = item["created_at"].isoformat() if item["created_at"] else None
        items.append(item)

    return {"items": items, "limit": limit, "offset": offset}


# ──────────────────────────────────────────────────────────────
# 응답 상세
# ──────────────────────────────────────────────────────────────


@router.get("/responses/{response_id}", response_class=JSONResponse)
async def get_response_detail(
    response_id: str,
    _: None = Depends(require_admin),
) -> dict:
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM responses WHERE id = %s;", (response_id,))
            row = await cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="응답을 찾을 수 없습니다.")
            cols = [d[0] for d in cur.description]

    item = dict(zip(cols, row))
    item["id"] = str(item["id"])
    for key in ("created_at", "updated_at"):
        if item.get(key):
            item[key] = item[key].isoformat()
    return item
