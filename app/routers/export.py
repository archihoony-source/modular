"""내보내기 라우터.

- GET /admin/export/excel  : multi-sheet Excel 다운로드
- GET /admin/export/word   : KICT 보고서 양식 Word 다운로드
"""

from datetime import datetime
from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.routers.admin import require_admin
from app.services import excel_export, word_export

router = APIRouter()


def _download_filename(prefix: str, ext: str) -> str:
    """타임스탬프 포함 파일명."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"{prefix}_{stamp}.{ext}"


def _content_disposition(filename: str) -> str:
    """RFC 5987에 따른 UTF-8 파일명 헤더."""
    encoded = quote(filename)
    return f"attachment; filename*=UTF-8''{encoded}"


@router.get("/excel")
async def export_excel(_: None = Depends(require_admin)):
    """전체 응답 + 통계 → Excel 다운로드."""
    data = await excel_export.build_workbook()
    filename = _download_filename("modular_survey_data", "xlsx")

    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": _content_disposition(filename)},
    )


@router.get("/word")
async def export_word(_: None = Depends(require_admin)):
    """KICT 보고서 양식 Word 다운로드."""
    data = await word_export.build_report()
    filename = _download_filename("modular_survey_report", "docx")

    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": _content_disposition(filename)},
    )
