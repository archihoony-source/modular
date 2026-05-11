"""내보내기 라우터.

- GET /admin/export/excel  : 전체 응답 + 통계 Excel 다운로드
- GET /admin/export/word   : 보고서 형식 Word 다운로드
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.routers.admin import require_admin

router = APIRouter()


@router.get("/excel")
async def export_excel(_: None = Depends(require_admin)):
    """Multi-sheet Excel 파일을 스트리밍 다운로드.

    구현 메모:
    1. services/excel_export.py 의 build_workbook() 호출
    2. openpyxl Workbook → BytesIO → StreamingResponse
    3. 시트 구성: 응답_원본, 기술분류_집계, 연구기간_집계,
                  성과물유형_집계, 제안자_명단, 요약통계
    """
    # TODO: 다음 단계에서 구현
    raise NotImplementedError("다음 단계에서 구현 예정.")


@router.get("/word")
async def export_word(_: None = Depends(require_admin)):
    """KICT 보고서 형식 Word 파일 다운로드.

    구현 메모:
    1. services/word_export.py 의 build_report() 호출
    2. python-docx Document → BytesIO → StreamingResponse
    3. 구성: 표지, 응답현황, 기술분류, 연구기간, 성과물유형, 키워드,
            응답자 의견 발췌, 부록(전체 명단)
    """
    # TODO: 다음 단계에서 구현
    raise NotImplementedError("다음 단계에서 구현 예정.")
