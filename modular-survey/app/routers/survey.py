"""설문 폼 및 제출 라우터.

- GET  /            : 설문 폼 페이지
- POST /submit      : 응답 저장
- GET  /thank-you   : 제출 완료 페이지
"""

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
# from app.database import get_pool
# from app.models import SurveyResponseSubmit

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/", response_class=HTMLResponse)
async def survey_form(request: Request):
    """설문 폼 페이지를 표시."""
    return templates.TemplateResponse(
        request=request,
        name="survey_form.html",
        context={
            "survey_title": settings.survey_title,
            "survey_deadline": settings.survey_deadline,
        },
    )


@router.post("/submit")
async def submit_response(request: Request):
    """폼 제출을 받아 DB에 저장.

    구현 메모:
    1. request.form() 으로 폼 데이터 수신
    2. SurveyResponseSubmit으로 Pydantic 검증
    3. INSERT INTO responses ...
    4. /thank-you 로 리다이렉트
    """
    # TODO: 다음 단계에서 구현
    return RedirectResponse(url="/thank-you", status_code=303)


@router.get("/thank-you", response_class=HTMLResponse)
async def thank_you(request: Request):
    """제출 완료 페이지."""
    return templates.TemplateResponse(
        request=request,
        name="thank_you.html",
        context={"survey_title": settings.survey_title},
    )
