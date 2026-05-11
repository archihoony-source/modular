"""Pydantic 모델 정의.

PDF 양식의 모든 필드를 1:1 매핑.
모델 수준 검증으로 기술분류/성과물 최소 1개 필수 보장.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ──────────────────────────────────────────────────────────────
# 제출 모델 (응답자 → 서버)
# ──────────────────────────────────────────────────────────────


class SurveyResponseSubmit(BaseModel):
    """수요조사 제출 데이터.

    HTML 폼의 모든 필드를 그대로 받아 검증.
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
    tech_overview: Annotated[str, Field(min_length=10, max_length=10000)]
    tech_necessity: Annotated[str, Field(max_length=10000)] = ""
    research_content: Annotated[str, Field(max_length=10000)] = ""
    final_outcome: Annotated[str, Field(max_length=5000)] = ""

    # 기대효과
    impact_socioeconomic: Annotated[str, Field(max_length=5000)] = ""
    impact_scientific: Annotated[str, Field(max_length=5000)] = ""

    # 연구기간
    research_period_years: Annotated[int, Field(ge=1, le=7)]

    # 제안자
    proposer_name: Annotated[str, Field(min_length=1, max_length=100)]
    proposer_organization: Annotated[str, Field(min_length=1, max_length=200)]
    proposer_position: Annotated[str, Field(max_length=100)] = ""
    proposer_phone: Annotated[str, Field(max_length=50)] = ""
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
            raise ValueError("개인정보 수집·이용에 동의해야 제출할 수 있습니다.")
        return v

    @model_validator(mode="after")
    def at_least_one_tech_category(self) -> "SurveyResponseSubmit":
        if not any([
            self.tech_cat_rc_competitive,
            self.tech_cat_zero_fatality,
            self.tech_cat_marketability,
            self.tech_cat_scaleup,
            self.tech_cat_other,
        ]):
            raise ValueError("기술 분류를 1개 이상 선택해 주십시오. [field=tech_category]")

        if self.tech_cat_other and not self.tech_cat_other_text.strip():
            raise ValueError("'기타' 선택 시 내용을 입력해 주십시오. [field=tech_cat_other_text]")

        return self

    @model_validator(mode="after")
    def at_least_one_output_type(self) -> "SurveyResponseSubmit":
        if not any([
            self.output_type_system, self.output_type_method,
            self.output_type_material, self.output_type_software,
            self.output_type_equipment, self.output_type_standard,
        ]):
            raise ValueError("성과물 유형을 1개 이상 선택해 주십시오. [field=output_type]")
        return self


# ──────────────────────────────────────────────────────────────
# 조회 모델
# ──────────────────────────────────────────────────────────────


class SurveyResponse(SurveyResponseSubmit):
    """DB에서 읽어온 응답 1건."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    submission_status: str
