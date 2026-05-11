"""Excel 보고서 생성.

openpyxl을 사용하여 multi-sheet 워크북 생성.

시트 구성:
1. 응답_원본       : 모든 응답 raw data
2. 기술분류_집계   : 카테고리별 빈도
3. 연구기간_집계   : 연도별 빈도
4. 성과물유형_집계 : 유형별 빈도
5. 제안자_명단     : 이름·소속·이메일만 별도
6. 요약통계        : 주요 지표 요약
"""

# from io import BytesIO
# from openpyxl import Workbook
# from openpyxl.styles import Font, Alignment, PatternFill


async def build_workbook() -> bytes:
    """전체 Excel 워크북을 bytes로 반환.

    구현 메모:
    1. wb = Workbook()
    2. _add_raw_sheet(wb), _add_tech_cat_sheet(wb), ...
    3. wb.save(BytesIO()) → .getvalue()
    """
    raise NotImplementedError("다음 단계에서 구현 예정.")
