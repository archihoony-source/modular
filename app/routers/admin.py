"""관리자 페이지 라우터.

- GET  /admin/login         : 관리자 로그인 폼
- POST /admin/login         : 비밀번호 검증
- POST /admin/logout        : 로그아웃
- GET  /admin               : 통계 대시보드
- GET  /admin/statistics    : 집계 결과 JSON (Plotly용)
- GET  /admin/responses     : 응답 목록 JSON
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# ──────────────────────────────────────────────────────────────
# 인증 의존성
# ──────────────────────────────────────────────────────────────


def require_admin(request: Request) -> None:
    """세션에 관리자 플래그가 없으면 401."""
    if not request.session.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="관리자 권한이 필요합니다.",
            headers={"Location": "/admin/login"},
        )


# ──────────────────────────────────────────────────────────────
# 인증 라우트
# ──────────────────────────────────────────────────────────────


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={"error": None},
    )


@router.post("/login")
async def login_submit(request: Request, password: str = Form(...)):
    if password == settings.admin_password:
        request.session["is_admin"] = True
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={"error": "비밀번호가 올바르지 않습니다."},
        status_code=401,
    )


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)


# ──────────────────────────────────────────────────────────────
# 대시보드
# ──────────────────────────────────────────────────────────────


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, _: None = Depends(require_admin)):
    """통계 대시보드 페이지.

    데이터는 클라이언트에서 /admin/statistics를 fetch하여 Plotly로 렌더.
    """
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={"survey_title": settings.survey_title},
    )


@router.get("/statistics", response_class=JSONResponse)
async def statistics(_: None = Depends(require_admin)) -> dict:
    """집계 통계 JSON.

    구현 메모: services/statistics.py 의 aggregate_all() 호출.
    """
    # TODO: 다음 단계에서 구현
    return {
        "total_responses": 0,
        "tech_categories": [],
        "research_periods": [],
        "output_types": [],
        "organizations": [],
        "keywords_top": [],
    }


@router.get("/responses", response_class=JSONResponse)
async def list_responses(_: None = Depends(require_admin)) -> list:
    """응답 목록 (관리자 확인용)."""
    # TODO: 다음 단계에서 구현
    return []
