"""Word 보고서 생성.

python-docx 사용. KICT 보고서 양식 기반.

구성:
1. 표지: 제목·기간·응답 수
2. 응답 현황 요약
3. 기술분류 분석 (표 + 차트 이미지)
4. 연구기간 분석 (표 + 차트 이미지)
5. 성과물 유형 분석 (표 + 차트 이미지)
6. 주요 키워드 (워드클라우드 이미지)
7. 응답자 의견 발췌
8. 부록: 전체 응답 명단
"""

# from io import BytesIO
# from docx import Document
# from docx.shared import Pt, Cm, Inches
# from docx.enum.text import WD_ALIGN_PARAGRAPH
# import matplotlib.pyplot as plt


async def build_report() -> bytes:
    """전체 Word 보고서를 bytes로 반환.

    구현 메모:
    1. doc = Document()
    2. _add_cover(doc), _add_summary(doc), ...
    3. doc.save(BytesIO()) → .getvalue()

    스타일 가이드:
    - 한글 본문: 맑은 고딕 11pt
    - 제목: 맑은 고딕 14pt Bold
    - KICT 개조식 톤 (~임, ~함, ~됨)
    """
    raise NotImplementedError("다음 단계에서 구현 예정.")
