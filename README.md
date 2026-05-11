# 차세대 모듈러 건축 핵심기술 수요조사 시스템

KICT(한국건설기술연구원) 차세대 모듈러 건축 핵심기술 기획연구 수요조사를 위한 웹 기반 응답 수집 및 자동 통계 시스템입니다.

## 시스템 개요

- **목적**: PDF 양식 기반 수요조사를 디지털화하여 응답 수집·집계·통계·보고서 출력까지 자동화
- **호스팅**: Render(웹서비스) + Supabase(Postgres) — 카드 등록 없이 영구 무료
- **백엔드**: FastAPI(Python 3.11)
- **DB**: PostgreSQL (Supabase 무료 500MB)
- **프론트엔드**: 서버 렌더링(Jinja2) + Tailwind CSS(CDN) + Plotly.js(CDN)

## 디렉터리 구조

```
modular-survey/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 진입점
│   ├── config.py                  # 환경변수 로딩
│   ├── database.py                # Supabase Postgres 연결
│   ├── models.py                  # Pydantic 모델 (PDF 양식 필드)
│   ├── routers/
│   │   ├── survey.py              # /, /submit, /thank-you
│   │   ├── admin.py               # /admin (관리자 대시보드)
│   │   └── export.py              # /admin/export/excel, /admin/export/word
│   ├── services/
│   │   ├── statistics.py          # 응답 집계 로직
│   │   ├── excel_export.py        # Excel 보고서 생성
│   │   └── word_export.py         # Word 보고서 생성
│   ├── templates/
│   │   ├── base.html              # 공통 레이아웃
│   │   ├── survey_form.html       # 설문 폼 페이지
│   │   ├── thank_you.html         # 제출 완료 페이지
│   │   └── admin_dashboard.html   # 관리자 통계 페이지
│   └── static/
│       ├── css/style.css          # 추가 스타일
│       └── js/form.js             # 클라이언트 검증
├── migrations/
│   └── 001_create_responses_table.sql   # 테이블 스키마
├── tests/
│   ├── test_submit.py
│   └── test_statistics.py
├── .env.example                   # 환경변수 템플릿
├── .gitignore
├── .python-version                # Python 3.11
├── DESIGN.md                      # 설계 결정 문서
├── README.md
├── render.yaml                    # Render Blueprint 배포 설정
└── requirements.txt               # Python 의존성
```

## 빠른 시작 (로컬 개발)

### 1. 사전 준비

- Python 3.11 이상
- Git
- Supabase 계정 (https://supabase.com — 무료, 카드 불필요)

### 2. Supabase 프로젝트 생성

1. https://supabase.com 가입 후 "New Project" 클릭
2. 프로젝트 이름: `modular-survey`, Region: `Northeast Asia (Seoul)` 선택
3. 데이터베이스 비밀번호 설정 후 생성 (3~5분 소요)
4. 좌측 메뉴 → "SQL Editor" → 새 쿼리 생성
5. `migrations/001_create_responses_table.sql` 내용을 붙여넣고 RUN
6. 좌측 메뉴 → "Project Settings" → "Database" → "Connection string" → URI 복사
   (예: `postgresql://postgres.xxx:[YOUR-PASSWORD]@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres`)

### 3. 로컬 실행

```bash
git clone <레포-URL> modular-survey
cd modular-survey

# Python 가상환경 생성
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 열어 DATABASE_URL과 ADMIN_PASSWORD 입력

# 개발 서버 실행
uvicorn app.main:app --reload --port 8000
```

브라우저에서 http://localhost:8000 접속.
관리자 페이지: http://localhost:8000/admin

## Render 배포

### 1. GitHub 레포 푸시

```bash
git init
git add .
git commit -m "Initial scaffold"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Render 배포

1. https://render.com 가입 (카드 불필요)
2. Dashboard → "New +" → "Blueprint"
3. GitHub 레포 연결 → `render.yaml` 자동 감지
4. 환경변수 설정 화면에서 다음 입력:
   - `DATABASE_URL`: Supabase에서 복사한 connection string
   - `ADMIN_PASSWORD`: 관리자 페이지 접근 비밀번호 (임의 설정)
5. "Apply" 클릭 → 자동 배포 (3~5분)
6. 배포 완료 후 URL 확인 (예: `https://modular-survey.onrender.com`)

### 3. 배포 후 점검

- `/` 페이지에서 설문 폼 정상 표시 확인
- 테스트 응답 1건 제출 → Supabase Table Editor에서 `responses` 테이블에 데이터 확인
- `/admin` 접속 → ADMIN_PASSWORD로 로그인 → 통계 페이지 확인
- `/admin/export/excel`, `/admin/export/word` 다운로드 확인

## 환경변수

| 변수명 | 설명 | 예시 |
|---|---|---|
| `DATABASE_URL` | Supabase Postgres 연결 문자열 | `postgresql://postgres.xxx:password@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres` |
| `ADMIN_PASSWORD` | 관리자 페이지 비밀번호 | (임의 설정) |
| `SURVEY_TITLE` | 설문 제목 (선택) | `차세대 모듈러 건축 핵심기술 수요조사` |
| `SURVEY_DEADLINE` | 마감일 표시용 (선택, YYYY-MM-DD) | `2026-06-30` |

## 운영 흐름

1. **수요조사 개시**: Render에서 배포 완료 → URL을 KICT 관계자에게 배포
2. **응답 수집**: 응답자가 폼 작성·제출 → Supabase에 즉시 저장
3. **실시간 모니터링**: 관리자는 `/admin`에서 응답 현황·통계 차트 확인
4. **수요조사 종료**: 관리자가 `/admin/export/excel` 또는 `/admin/export/word` 클릭 → 보고서 다운로드
5. **데이터 보관**: Supabase에서 raw data 영구 보관 (또는 .sql dump로 백업)

## 비용

- Render Web Service: **무료** (750시간/월, 카드 불필요)
- Supabase Postgres: **무료** (500MB, 영구)
- 합계: **월 0원**

## 라이선스 / 활용

KICT 내부 연구 목적. 외부 배포 시 별도 검토 필요.
