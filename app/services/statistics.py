"""응답 데이터 집계 로직.

DB에서 raw 응답을 읽어 통계 항목별로 가공.
pandas DataFrame을 중간 표현으로 사용.
"""

# from typing import Any
# import pandas as pd
# from app.database import get_pool


async def fetch_responses_as_dataframe():
    """전체 응답을 pandas DataFrame으로 로드.

    구현 메모:
    - SELECT * FROM responses
    - pd.DataFrame() 생성
    - 캐싱 검토 (관리자 페이지 새로고침 시마다 쿼리 발생 방지)
    """
    raise NotImplementedError("다음 단계에서 구현 예정.")


async def aggregate_tech_categories() -> list[dict]:
    """기술분류 4종 + 기타의 빈도 집계.

    반환 예:
    [{"category": "RC 동등 이상 경쟁력", "count": 12}, ...]
    """
    raise NotImplementedError("다음 단계에서 구현 예정.")


async def aggregate_research_periods() -> list[dict]:
    """연구기간(1~7년) 분포.

    반환 예:
    [{"years": 1, "count": 3}, {"years": 2, "count": 8}, ...]
    """
    raise NotImplementedError("다음 단계에서 구현 예정.")


async def aggregate_output_types() -> list[dict]:
    """성과물 유형 6종의 빈도 집계."""
    raise NotImplementedError("다음 단계에서 구현 예정.")


async def aggregate_organizations() -> list[dict]:
    """제안자 소속을 산·학·연·관으로 분류.

    구현 메모:
    - '대학교', '대학' → 학
    - '연구원', '연구소' → 연
    - '청', '공사', '공단', '부' → 관
    - 그 외 → 산
    """
    raise NotImplementedError("다음 단계에서 구현 예정.")


async def aggregate_keywords_top(n: int = 30) -> list[dict]:
    """키워드(쉼표 분리) 빈도 상위 N개.

    반환 예:
    [{"keyword": "고층모듈러", "count": 7}, ...]
    """
    raise NotImplementedError("다음 단계에서 구현 예정.")


async def aggregate_daily_responses() -> list[dict]:
    """일별 응답 수 (응답 추이 라인차트용)."""
    raise NotImplementedError("다음 단계에서 구현 예정.")


async def aggregate_all() -> dict:
    """관리자 페이지 한 번에 모든 통계 반환."""
    return {
        "total_responses": 0,
        "tech_categories": await aggregate_tech_categories(),
        "research_periods": await aggregate_research_periods(),
        "output_types": await aggregate_output_types(),
        "organizations": await aggregate_organizations(),
        "keywords_top": await aggregate_keywords_top(),
        "daily_responses": await aggregate_daily_responses(),
    }
