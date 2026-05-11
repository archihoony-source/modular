"""제출 라우트 테스트 (다음 단계에서 구현).

테스트 항목 후보:
- POST /submit 정상 응답 → 303 리다이렉트
- 필수 필드 누락 시 422
- 개인정보 미동의 시 422
- 기술분류 모두 미선택 시 422
- 연구기간 범위 (0, 8) 시 422
- 이메일 형식 오류 시 422
"""

# import pytest
# from fastapi.testclient import TestClient
# from app.main import app
#
# client = TestClient(app)
#
#
# def test_submit_valid_response():
#     response = client.post("/submit", data={...})
#     assert response.status_code == 303
