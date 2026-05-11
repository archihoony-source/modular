"""Pydantic 모델 정의.

PDF 양식의 모든 필드를 그대로 매핑. 폼 검증 및 DB 저장에 사용.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ──────────────────────────────────────────────────────────────
# 폼 제출 모델 (응답자 → 서버)
# ──────────────────────────────────────────────────────────────


class SurveyResponseSubmit(BaseModel):
    """수요조사 제출 데이터.

    모든 필드는 PDF 양식의 항목과 1:1 대응.
    """

    # 과제 정보
    project_title: Annotated[str, Field(min_length=2, max_length=500)]
    keywords: str = ""

    # 기술 분류 (다중 체크)
    tech_cat_rc_competitive: bool = False
    tech_cat_zero_fatality: bool = False
    tech_cat_marketability: bool = False
    tech_cat_scaleup: bool = False
    tech_cat_other: bool = False
    tech_cat_other_text: str = ""

    # 기술 내용
    tech_overview: Annotated[str, Field(min_length=10)]
    tech_necessity: str = ""
    research_content: str = ""
    final_outcome: str = ""

    # 기대효과
    impact_socioeconomic: str = ""
    impact_scientific: str = ""

    # 연구기간
    research_period_years: Annotated[int, Field(ge=1, le=7)]

    # 제안자
    proposer_name: Annotated[str, Field(min_length=1, max_length=100)]
    proposer_organization: Annotated[str, Field(min_length=1, max_length=200)]
    proposer_position: str = ""
    proposer_phone: str = ""
    proposer_email: EmailStr

    # 성과물 유형 (다중 체크)
    output_type_system: bool = False
    output_type_method: bool = False
    output_type_material: bool = False
    output_type_software: bool = False
    output_type_equipment: bool = False
    output_type_standard: bool = False

    # 동의
    privacy_consent: bool

    @field_validator("privacy_consent")
    @classmethod
    def must_consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("개인정보 수집 및 이용에 동의해야 제출할 수 있습니다.")
        return v

    @field_validator("tech_cat_rc_competitive", "tech_cat_zero_fatality",
                     "tech_cat_marketability", "tech_cat_scaleup", "tech_cat_other")
    @classmethod
    def at_least_one_category(cls, v: bool, info) -> bool:
        # 개별 검증으로는 한계 → 모델 수준 검증으로 별도 처리 권장
        return v


# ──────────────────────────────────────────────────────────────
# DB 조회 모델
# ──────────────────────────────────────────────────────────────


class SurveyResponse(SurveyResponseSubmit):
    """DB에서 읽어온 응답 1건."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    submission_status: str
