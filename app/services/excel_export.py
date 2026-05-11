"""Excel 보고서 생성.

openpyxl 사용. 6개 시트 multi-sheet 워크북.

시트 구성:
1. 응답_원본       : 모든 응답 raw data (행 = 응답자)
2. 기술분류_집계   : 카테고리별 빈도
3. 연구기간_집계   : 연도별 빈도
4. 성과물유형_집계 : 유형별 빈도
5. 제안자_명단     : 이름·소속·이메일만 (개인정보 별도 시트)
6. 요약통계        : 주요 지표 한눈에
"""

from datetime import datetime
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from app.database import get_pool
from app.services import statistics


# ──────────────────────────────────────────────────────────────
# 스타일 헬퍼
# ──────────────────────────────────────────────────────────────

_HEADER_FILL = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
_HEADER_FONT = Font(name="맑은 고딕", size=11, bold=True, color="FFFFFF")
_BODY_FONT = Font(name="맑은 고딕", size=10)
_TITLE_FONT = Font(name="맑은 고딕", size=14, bold=True)


def _style_header(ws: Worksheet, row: int = 1) -> None:
    """주어진 행을 헤더 스타일로 변환."""
    for cell in ws[row]:
        cell.fill = _HEADER_FILL
        cell.font = _HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _autosize(ws: Worksheet, max_width: int = 60) -> None:
    """컬럼 폭 자동 조정 (한글 가중치 포함)."""
    for col_cells in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col_cells[0].column)
        for cell in col_cells:
            if cell.value is None:
                continue
            s = str(cell.value)
            # 한글·한자는 폭 1.7배로 가중
            length = sum(1.7 if ord(c) > 127 else 1.0 for c in s)
            max_len = max(max_len, length)
        ws.column_dimensions[col_letter].width = min(max(max_len + 2, 10), max_width)


# ──────────────────────────────────────────────────────────────
# 데이터 조회
# ──────────────────────────────────────────────────────────────


async def _fetch_all_responses() -> list[dict]:
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT * FROM responses
                ORDER BY created_at ASC;
            """)
            rows = await cur.fetchall()
            cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in rows]


# ──────────────────────────────────────────────────────────────
# 시트 빌더
# ──────────────────────────────────────────────────────────────


_RAW_COLUMNS = [
    ("연번", "_index"),
    ("제출일시", "created_at"),
    ("과제명(기술명)", "project_title"),
    ("키워드", "keywords"),
    ("RC동등경쟁력", "tech_cat_rc_competitive"),
    ("사망사고제로", "tech_cat_zero_fatality"),
    ("상품성확보", "tech_cat_marketability"),
    ("산업스케일업", "tech_cat_scaleup"),
    ("기타분류", "tech_cat_other"),
    ("기타분류 내용", "tech_cat_other_text"),
    ("기술개요", "tech_overview"),
    ("기술필요성", "tech_necessity"),
    ("연구내용", "research_content"),
    ("최종성과물", "final_outcome"),
    ("경제사회적효과", "impact_socioeconomic"),
    ("과학기술적효과", "impact_scientific"),
    ("연구기간(년)", "research_period_years"),
    ("성명", "proposer_name"),
    ("소속기관", "proposer_organization"),
    ("직위", "proposer_position"),
    ("연락처", "proposer_phone"),
    ("E-mail", "proposer_email"),
    ("시스템", "output_type_system"),
    ("공법기법", "output_type_method"),
    ("재료자재", "output_type_material"),
    ("소프트웨어", "output_type_software"),
    ("장비장치", "output_type_equipment"),
    ("기준지침", "output_type_standard"),
]


def _bool_to_mark(v) -> str:
    if v is True:
        return "○"
    if v is False:
        return ""
    return str(v) if v is not None else ""


def _format_value(key: str, value):
    """셀 값 포맷팅."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return _bool_to_mark(value)
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def _add_raw_sheet(wb: Workbook, responses: list[dict]) -> None:
    ws = wb.create_sheet("응답_원본")

    # 헤더
    headers = [label for label, _ in _RAW_COLUMNS]
    ws.append(headers)
    _style_header(ws)

    # 데이터
    for i, row in enumerate(responses, start=1):
        line = []
        for label, key in _RAW_COLUMNS:
            if key == "_index":
                line.append(i)
            else:
                line.append(_format_value(key, row.get(key)))
        ws.append(line)

    # 본문 스타일
    for r in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in r:
            cell.font = _BODY_FONT
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    ws.freeze_panes = "B2"
    _autosize(ws, max_width=50)


def _add_summary_table(ws: Worksheet, start_row: int, title: str,
                       data: list[dict], label_key: str, value_key: str = "count") -> int:
    """단일 집계표 추가. 반환값 = 다음 사용 가능 행 번호."""
    # 섹션 제목
    ws.cell(row=start_row, column=1, value=title).font = _TITLE_FONT
    ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=3)

    # 헤더
    header_row = start_row + 1
    ws.cell(row=header_row, column=1, value="구분").font = _HEADER_FONT
    ws.cell(row=header_row, column=1).fill = _HEADER_FILL
    ws.cell(row=header_row, column=1).alignment = Alignment(horizontal="center")
    ws.cell(row=header_row, column=2, value="응답 수").font = _HEADER_FONT
    ws.cell(row=header_row, column=2).fill = _HEADER_FILL
    ws.cell(row=header_row, column=2).alignment = Alignment(horizontal="center")
    ws.cell(row=header_row, column=3, value="비율(%)").font = _HEADER_FONT
    ws.cell(row=header_row, column=3).fill = _HEADER_FILL
    ws.cell(row=header_row, column=3).alignment = Alignment(horizontal="center")

    # 데이터
    total = sum(int(d.get(value_key, 0)) for d in data)
    r = header_row
    for d in data:
        r += 1
        cnt = int(d.get(value_key, 0))
        pct = (cnt / total * 100) if total > 0 else 0
        ws.cell(row=r, column=1, value=str(d.get(label_key, ""))).font = _BODY_FONT
        ws.cell(row=r, column=2, value=cnt).font = _BODY_FONT
        ws.cell(row=r, column=2).alignment = Alignment(horizontal="center")
        ws.cell(row=r, column=3, value=f"{pct:.1f}").font = _BODY_FONT
        ws.cell(row=r, column=3).alignment = Alignment(horizontal="center")

    # 합계
    r += 1
    ws.cell(row=r, column=1, value="합계").font = Font(name="맑은 고딕", size=10, bold=True)
    ws.cell(row=r, column=2, value=total).font = Font(name="맑은 고딕", size=10, bold=True)
    ws.cell(row=r, column=2).alignment = Alignment(horizontal="center")
    ws.cell(row=r, column=3, value="100.0").font = Font(name="맑은 고딕", size=10, bold=True)
    ws.cell(row=r, column=3).alignment = Alignment(horizontal="center")

    return r + 2  # 다음 표까지 1줄 띄움


async def _add_aggregation_sheets(wb: Workbook) -> None:
    """기술분류·연구기간·성과물유형 집계 시트 추가."""
    # 기술분류
    ws = wb.create_sheet("기술분류_집계")
    data = await statistics.aggregate_tech_categories()
    _add_summary_table(ws, 1, "기술 분류 분포 (중복 응답 가능)", data, "category")
    _autosize(ws)

    # 연구기간
    ws = wb.create_sheet("연구기간_집계")
    periods = await statistics.aggregate_research_periods()
    formatted = [{"label": f"{p['years']}년", "count": p["count"]} for p in periods]
    _add_summary_table(ws, 1, "연구기간 분포", formatted, "label")
    _autosize(ws)

    # 성과물유형
    ws = wb.create_sheet("성과물유형_집계")
    data = await statistics.aggregate_output_types()
    _add_summary_table(ws, 1, "성과물 유형 분포 (중복 응답 가능)", data, "output_type")
    _autosize(ws)

    # 소속 분포
    ws = wb.create_sheet("소속_분포")
    orgs = await statistics.aggregate_organizations()
    _add_summary_table(ws, 1, "제안자 소속 분포 (산·학·연·관)", orgs, "sector")
    _autosize(ws)

    # 키워드
    ws = wb.create_sheet("키워드_빈도")
    kws = await statistics.aggregate_keywords_top(n=100)
    _add_summary_table(ws, 1, "키워드 빈도 (상위 100)", kws, "keyword")
    _autosize(ws)


def _add_proposer_sheet(wb: Workbook, responses: list[dict]) -> None:
    """개인정보 별도 시트."""
    ws = wb.create_sheet("제안자_명단")

    headers = ["연번", "성명", "소속기관", "직위", "연락처", "E-mail", "과제명", "제출일시"]
    ws.append(headers)
    _style_header(ws)

    for i, row in enumerate(responses, start=1):
        ws.append([
            i,
            row.get("proposer_name", ""),
            row.get("proposer_organization", ""),
            row.get("proposer_position", ""),
            row.get("proposer_phone", ""),
            row.get("proposer_email", ""),
            row.get("project_title", ""),
            _format_value("created_at", row.get("created_at")),
        ])

    for r in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in r:
            cell.font = _BODY_FONT

    ws.freeze_panes = "B2"
    _autosize(ws, max_width=40)


async def _add_summary_sheet(wb: Workbook, responses: list[dict]) -> None:
    """주요 지표 요약 시트."""
    ws = wb.create_sheet("요약통계", 0)  # 첫 번째 시트로 배치

    total = len(responses)
    tech_cats = await statistics.aggregate_tech_categories()
    output_types = await statistics.aggregate_output_types()

    # 제목
    ws.cell(row=1, column=1, value="차세대 모듈러 건축 핵심기술 수요조사 - 요약").font = _TITLE_FONT
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=4)

    # 메타
    ws.cell(row=3, column=1, value="생성일시").font = Font(name="맑은 고딕", size=10, bold=True)
    ws.cell(row=3, column=2, value=datetime.now().strftime("%Y-%m-%d %H:%M:%S")).font = _BODY_FONT

    ws.cell(row=4, column=1, value="총 응답 수").font = Font(name="맑은 고딕", size=10, bold=True)
    ws.cell(row=4, column=2, value=total).font = _BODY_FONT

    # 최다 응답 카테고리
    if tech_cats and total > 0:
        top_cat = max(tech_cats, key=lambda x: x["count"])
        ws.cell(row=5, column=1, value="최다 응답 기술분류").font = Font(name="맑은 고딕", size=10, bold=True)
        ws.cell(row=5, column=2, value=f"{top_cat['category']} ({top_cat['count']}건)").font = _BODY_FONT

    if output_types and total > 0:
        top_out = max(output_types, key=lambda x: x["count"])
        ws.cell(row=6, column=1, value="최다 응답 성과물유형").font = Font(name="맑은 고딕", size=10, bold=True)
        ws.cell(row=6, column=2, value=f"{top_out['output_type']} ({top_out['count']}건)").font = _BODY_FONT

    # 안내
    ws.cell(row=8, column=1, value="※ 본 통계는 자동 집계 결과이며, 정성적 분석은 별도 보고서 참조").font = Font(
        name="맑은 고딕", size=9, italic=True, color="666666"
    )

    _autosize(ws)


# ──────────────────────────────────────────────────────────────
# 메인 엔트리
# ──────────────────────────────────────────────────────────────


async def build_workbook() -> bytes:
    """전체 Excel 워크북을 bytes로 반환."""
    responses = await _fetch_all_responses()

    wb = Workbook()
    # 기본 생성된 시트 제거
    wb.remove(wb.active)

    await _add_summary_sheet(wb, responses)
    _add_raw_sheet(wb, responses)
    await _add_aggregation_sheets(wb)
    _add_proposer_sheet(wb, responses)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
