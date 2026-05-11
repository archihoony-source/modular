"""응답 데이터 집계 로직.

각 함수는 DB에서 raw 응답을 직접 SQL로 집계하여 JSON-친화적 dict 리스트 반환.
관리자 대시보드와 Excel/Word 보고서가 공통으로 사용.
"""

from collections import Counter
from datetime import date
from typing import Any

from app.database import get_pool


# ──────────────────────────────────────────────────────────────
# 기본 통계
# ──────────────────────────────────────────────────────────────


async def get_total_count() -> int:
    """총 응답 수."""
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM responses;")
            row = await cur.fetchone()
    return int(row[0]) if row else 0


# ──────────────────────────────────────────────────────────────
# 기술 분류
# ──────────────────────────────────────────────────────────────

_TECH_CATEGORY_LABELS = [
    ("tech_cat_rc_competitive", "RC 동등 이상 경쟁력"),
    ("tech_cat_zero_fatality", "사망사고 제로"),
    ("tech_cat_marketability", "상품성 확보"),
    ("tech_cat_scaleup", "산업 스케일업"),
    ("tech_cat_other", "기타"),
]


async def aggregate_tech_categories() -> list[dict[str, Any]]:
    """기술분류 5종(4개 + 기타) 빈도.

    다중 체크이므로 단순 COUNT(*) FILTER로 컬럼별 집계.
    """
    pool = await get_pool()
    parts = [
        f"COUNT(*) FILTER (WHERE {col}) AS {col}"
        for col, _ in _TECH_CATEGORY_LABELS
    ]
    sql = f"SELECT {', '.join(parts)} FROM responses;"

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            row = await cur.fetchone()

    if row is None:
        return [{"category": label, "count": 0} for _, label in _TECH_CATEGORY_LABELS]

    return [
        {"category": label, "count": int(row[i])}
        for i, (_, label) in enumerate(_TECH_CATEGORY_LABELS)
    ]


# ──────────────────────────────────────────────────────────────
# 연구기간
# ──────────────────────────────────────────────────────────────


async def aggregate_research_periods() -> list[dict[str, Any]]:
    """연구기간(1~7년) 분포. 결측은 제외."""
    pool = await get_pool()
    sql = """
        SELECT research_period_years AS years, COUNT(*) AS cnt
        FROM responses
        WHERE research_period_years IS NOT NULL
        GROUP BY research_period_years
        ORDER BY research_period_years;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rows = await cur.fetchall()

    # 1~7년 전체 범위 채우기 (응답 없는 연도는 0)
    counts = {int(r[0]): int(r[1]) for r in rows}
    return [{"years": n, "count": counts.get(n, 0)} for n in range(1, 8)]


# ──────────────────────────────────────────────────────────────
# 성과물 유형
# ──────────────────────────────────────────────────────────────

_OUTPUT_TYPE_LABELS = [
    ("output_type_system", "시스템"),
    ("output_type_method", "공법·기법"),
    ("output_type_material", "재료·자재"),
    ("output_type_software", "소프트웨어"),
    ("output_type_equipment", "장비·장치"),
    ("output_type_standard", "기준·지침"),
]


async def aggregate_output_types() -> list[dict[str, Any]]:
    """성과물 유형 6종 빈도. 다중 체크."""
    pool = await get_pool()
    parts = [
        f"COUNT(*) FILTER (WHERE {col}) AS {col}"
        for col, _ in _OUTPUT_TYPE_LABELS
    ]
    sql = f"SELECT {', '.join(parts)} FROM responses;"

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            row = await cur.fetchone()

    if row is None:
        return [{"output_type": label, "count": 0} for _, label in _OUTPUT_TYPE_LABELS]

    return [
        {"output_type": label, "count": int(row[i])}
        for i, (_, label) in enumerate(_OUTPUT_TYPE_LABELS)
    ]


# ──────────────────────────────────────────────────────────────
# 제안자 소속 (산·학·연·관 분류)
# ──────────────────────────────────────────────────────────────


def classify_organization(org: str) -> str:
    """소속명 → 산·학·연·관·기타 분류.

    분류 규칙은 휴리스틱 기반 — 정확한 분류는 보고서 단계에서 수동 보정 가능.
    """
    if not org:
        return "미분류"
    s = org.strip()

    # 관(공공)
    public_kw = ["청", "공사", "공단", "부", "원(가)", "위원회", "재단",
                 "지원단", "지자체", "시청", "도청", "구청", "행정"]
    if any(k in s for k in public_kw):
        return "관"

    # 연구기관
    research_kw = ["연구원", "연구소", "연구센터", "Institute", "Research"]
    if any(k in s for k in research_kw):
        return "연"

    # 학계
    edu_kw = ["대학교", "대학원", "University", "Univ", "College", "고등학교",
              "전문대학", "특성화고"]
    if any(k in s for k in edu_kw) and "대학원생" not in s:
        return "학"

    # 협회/학회 → 별도 분류 가능하지만 단순화: 관에 포함
    assoc_kw = ["협회", "학회", "조합"]
    if any(k in s for k in assoc_kw):
        return "관"

    # 그 외 → 산업체로 추정
    return "산"


async def aggregate_organizations() -> list[dict[str, Any]]:
    """제안자 소속을 산·학·연·관·기타로 분류한 빈도."""
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT proposer_organization FROM responses;")
            rows = await cur.fetchall()

    counter: Counter[str] = Counter()
    for (org,) in rows:
        counter[classify_organization(org)] += 1

    # 표시 순서 고정
    order = ["산", "학", "연", "관", "미분류"]
    return [{"sector": k, "count": counter.get(k, 0)} for k in order if counter.get(k, 0) > 0 or k != "미분류"]


# ──────────────────────────────────────────────────────────────
# 키워드 빈도
# ──────────────────────────────────────────────────────────────


async def aggregate_keywords_top(n: int = 30) -> list[dict[str, Any]]:
    """쉼표로 구분된 키워드 필드를 파싱하여 상위 N개 빈도 반환."""
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT keywords FROM responses WHERE keywords IS NOT NULL AND keywords <> '';")
            rows = await cur.fetchall()

    counter: Counter[str] = Counter()
    for (kw_str,) in rows:
        for kw in str(kw_str).split(","):
            kw = kw.strip()
            if kw and len(kw) <= 40:
                counter[kw] += 1

    return [{"keyword": k, "count": c} for k, c in counter.most_common(n)]


# ──────────────────────────────────────────────────────────────
# 일별 응답 추이
# ──────────────────────────────────────────────────────────────


async def aggregate_daily_responses() -> list[dict[str, Any]]:
    """일별 응답 수 (응답 추이 라인차트용)."""
    pool = await get_pool()
    sql = """
        SELECT DATE(created_at AT TIME ZONE 'Asia/Seoul') AS d,
               COUNT(*) AS cnt
        FROM responses
        GROUP BY 1
        ORDER BY 1;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rows = await cur.fetchall()

    return [
        {
            "date": (r[0].isoformat() if isinstance(r[0], date) else str(r[0])),
            "count": int(r[1]),
        }
        for r in rows
    ]


# ──────────────────────────────────────────────────────────────
# 통합
# ──────────────────────────────────────────────────────────────


async def aggregate_all() -> dict[str, Any]:
    """관리자 대시보드용 모든 통계를 한 번에 반환."""
    return {
        "total_responses": await get_total_count(),
        "tech_categories": await aggregate_tech_categories(),
        "research_periods": await aggregate_research_periods(),
        "output_types": await aggregate_output_types(),
        "organizations": await aggregate_organizations(),
        "keywords_top": await aggregate_keywords_top(),
        "daily_responses": await aggregate_daily_responses(),
    }
