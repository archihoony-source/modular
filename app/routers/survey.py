"""설문 폼 및 제출 라우터.

- GET  /            : 설문 폼 페이지
- POST /submit      : Pydantic 검증 후 DB 저장 → /thank-you 리다이렉트
                      검증 실패 시 폼 재표시 (입력값 보존 + 에러 메시지)
- GET  /thank-you   : 제출 완료 페이지
"""

import hashlib
import re
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.config import settings
from app.database import get_pool
from app.models import SurveyResponseSubmit

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# ──────────────────────────────────────────────────────────────
# Helper: 폼 데이터 → dict 변환
# ──────────────────────────────────────────────────────────────


_BOOL_FIELDS = {
    "privacy_consent",
    "tech_cat_rc_competitive", "tech_cat_zero_fatality",
    "tech_cat_marketability", "tech_cat_scaleup", "tech_cat_other",
    "output_type_system", "output_type_method", "output_type_material",
    "output_type_software", "output_type_equipment", "output_type_standard",
}

# 라디오 버튼 value → 해당하는 boolean 필드명 매핑
# (DB 스키마는 5개 boolean 컬럼을 그대로 유지하므로, 라디오 선택값을
#  해당 boolean 1개만 True로 설정하는 방식으로 호환성 보존)
_TECH_CATEGORY_MAP = {
    "rc_competitive": "tech_cat_rc_competitive",
    "zero_fatality": "tech_cat_zero_fatality",
    "marketability": "tech_cat_marketability",
    "scaleup": "tech_cat_scaleup",
    "other": "tech_cat_other",
}


def form_to_dict(form_data) -> dict:
    """FastAPI form data를 Pydantic이 받을 수 있는 dict로 변환.

    - 체크박스가 선택되지 않으면 form에 키 자체가 없음 → False로 보정
    - 'true' 문자열 → True
    - tech_category 라디오 → 5개 boolean 중 1개만 True로 매핑
    """
    result: dict = {}
    for key, value in form_data.items():
        if key in _BOOL_FIELDS:
            result[key] = (str(value).lower() == "true")
        elif isinstance(value, str):
            result[key] = value.strip()
        else:
            result[key] = value

    # 누락된 체크박스 = False로 보정
    for bf in _BOOL_FIELDS:
        result.setdefault(bf, False)

    # tech_category 라디오 값 → 해당 boolean 필드만 True로 설정
    # 원본 라디오 값은 보존(검증 실패 시 폼 재표시할 때 선택 상태 유지를 위해).
    # Pydantic 모델은 알 수 없는 필드를 무시하므로 검증에는 영향 없음.
    radio_value = result.get("tech_category")
    if radio_value and radio_value in _TECH_CATEGORY_MAP:
        # 우선 모든 tech_cat 필드를 False로 초기화 후, 선택된 1개만 True
        for boolean_field in _TECH_CATEGORY_MAP.values():
            result[boolean_field] = False
        result[_TECH_CATEGORY_MAP[radio_value]] = True

    return result


def hash_client_ip(request: Request) -> str:
    """클라이언트 IP를 SHA256으로 비식별화."""
    ip = (request.client.host if request.client else "") or ""
    if not ip:
        return ""
    return hashlib.sha256(ip.encode()).hexdigest()[:32]


def parse_pydantic_errors(exc: ValidationError) -> dict[str, str]:
    """Pydantic ValidationError → {field_name: korean_message} 변환.

    model_validator에서 발생한 에러는 메시지 끝에 [field=xxx] 형태로
    필드명을 명시했으므로 이를 파싱.
    """
    field_errors: dict[str, str] = {}
    for err in exc.errors():
        msg = err["msg"]
        loc = err["loc"]

        # 메시지에서 [field=xxx] 패턴 추출 (모델 수준 검증 케이스)
        m = re.search(r"\[field=([^\]]+)\]", msg)
        if m:
            field_name = m.group(1)
            clean_msg = re.sub(r"\s*\[field=[^\]]+\]\s*", "", msg)
            field_errors[field_name] = clean_msg.replace("Value error, ", "")
        elif loc:
            field_name = str(loc[-1])
            field_errors[field_name] = msg.replace("Value error, ", "")
        else:
            field_errors["_global"] = msg

    return field_errors


# ──────────────────────────────────────────────────────────────
# DB INSERT
# ──────────────────────────────────────────────────────────────


_INSERT_SQL = """
INSERT INTO responses (
    project_title, keywords,
    tech_cat_rc_competitive, tech_cat_zero_fatality, tech_cat_marketability,
    tech_cat_scaleup, tech_cat_other, tech_cat_other_text,
    tech_overview, tech_necessity, research_content, final_outcome,
    impact_socioeconomic, impact_scientific,
    research_period_years,
    proposer_name, proposer_organization, proposer_position,
    proposer_phone, proposer_email,
    output_type_system, output_type_method, output_type_material,
    output_type_software, output_type_equipment, output_type_standard,
    privacy_consent, client_ip_hash
) VALUES (
    %(project_title)s, %(keywords)s,
    %(tech_cat_rc_competitive)s, %(tech_cat_zero_fatality)s, %(tech_cat_marketability)s,
    %(tech_cat_scaleup)s, %(tech_cat_other)s, %(tech_cat_other_text)s,
    %(tech_overview)s, %(tech_necessity)s, %(research_content)s, %(final_outcome)s,
    %(impact_socioeconomic)s, %(impact_scientific)s,
    %(research_period_years)s,
    %(proposer_name)s, %(proposer_organization)s, %(proposer_position)s,
    %(proposer_phone)s, %(proposer_email)s,
    %(output_type_system)s, %(output_type_method)s, %(output_type_material)s,
    %(output_type_software)s, %(output_type_equipment)s, %(output_type_standard)s,
    %(privacy_consent)s, %(client_ip_hash)s
) RETURNING id;
"""


async def insert_response(data: SurveyResponseSubmit, ip_hash: str) -> str:
    """검증된 응답을 DB에 저장하고 생성된 UUID 반환."""
    params = data.model_dump()
    params["proposer_email"] = str(data.proposer_email)
    params["client_ip_hash"] = ip_hash

    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(_INSERT_SQL, params)
            row = await cur.fetchone()
        await conn.commit()
    return str(row[0])


# ──────────────────────────────────────────────────────────────
# 라우트
# ──────────────────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
async def survey_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="survey_form.html",
        context={
            "survey_title": settings.survey_title,
            "survey_deadline": settings.survey_deadline,
            "old": {},
            "errors": {},
            "global_error": None,
        },
    )


@router.post("/submit")
async def submit_response(request: Request):
    """폼 제출 처리.

    검증 실패 시: 입력값을 그대로 보존한 채 폼 재표시 + 필드별 에러 메시지
    검증 성공 시: DB 저장 후 /thank-you 리다이렉트
    """
    form_data = await request.form()
    raw = form_to_dict(form_data)

    # Pydantic 검증
    try:
        validated = SurveyResponseSubmit(**raw)
    except ValidationError as exc:
        field_errors = parse_pydantic_errors(exc)
        return templates.TemplateResponse(
            request=request,
            name="survey_form.html",
            context={
                "survey_title": settings.survey_title,
                "survey_deadline": settings.survey_deadline,
                "old": raw,
                "errors": field_errors,
                "global_error": "입력 내용에 오류가 있습니다. 빨간색으로 표시된 항목을 확인해 주십시오.",
            },
            status_code=422,
        )

    # DB 저장
    try:
        ip_hash = hash_client_ip(request)
        await insert_response(validated, ip_hash)
    except Exception as e:
        # 운영 환경에서는 logger.exception(e)로 기록
        return templates.TemplateResponse(
            request=request,
            name="survey_form.html",
            context={
                "survey_title": settings.survey_title,
                "survey_deadline": settings.survey_deadline,
                "old": raw,
                "errors": {},
                "global_error": f"저장 중 오류가 발생했습니다. 잠시 후 다시 시도해 주십시오. ({type(e).__name__})",
            },
            status_code=500,
        )

    return RedirectResponse(url="/thank-you", status_code=303)


@router.get("/thank-you", response_class=HTMLResponse)
async def thank_you(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="thank_you.html",
        context={"survey_title": settings.survey_title},
    )
