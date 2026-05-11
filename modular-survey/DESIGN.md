# 설계 결정 문서 (Design Decisions)

본 문서는 차세대 모듈러 수요조사 시스템 구축 시 내린 주요 설계 결정과 그 근거를 기록한다.

## 1. 호스팅 플랫폼 선정

| 옵션 | 결과 | 근거 |
|---|---|---|
| **Render + Supabase** | ✅ 채택 | 카드 등록 없음, 영구 무료, DB 만료 없음 |
| Railway | ❌ | 2023년부터 영구 무료 티어 폐지 |
| Fly.io | ❌ | 카드 등록 필수, 신규 무료 티어 종료 |
| Hugging Face Spaces | △ | 영구 저장소 유료 |
| Render + Render Postgres | △ | Render 무료 Postgres는 30일 만료 |
| 자체 서버(KICT 내부) | △ | 망 분리·SSL 설정 부담 |

## 2. 아키텍처: 단일 서비스 vs 분리

**결정: 단일 FastAPI 서비스로 폼·관리자·API·내보내기 통합**

- 응답자 폼(SSR)·관리자 페이지(SSR)·제출 엔드포인트·내보내기 라우트를 한 FastAPI 인스턴스에서 처리
- Render Static Site와 Web Service를 분리하지 않음

**근거**:
- 응답자 수가 적음(예상 50~200명) → cold start는 첫 응답자 1회만 ~30초 영향
- CORS·도메인 분리 관리 부담 제거
- 단일 코드베이스로 유지보수 단순화
- Render 무료 Web Service의 750시간/월은 단일 서비스만 운영하면 여유

## 3. DB 선정: Supabase Postgres

- **Render Postgres 대신 Supabase**: 30일 만료 회피
- **Supabase 무료**: 500MB · 영구 (1주일 무접속 시 일시 휴면, 다음 접속 시 자동 복구)
- **표준 PostgreSQL**: 일반 psycopg / SQLAlchemy 등 표준 클라이언트 모두 호환
- **Region**: `ap-northeast-2 (Seoul)` 선택 → 한국 응답자 latency 최소

## 4. ORM: 사용하지 않음

**결정: `psycopg` v3 + 원시 SQL 사용**

- 스키마가 단일 테이블로 단순 → ORM 추상화 불필요
- 통계 집계는 raw SQL이 더 명확
- 의존성 최소화 (SQLAlchemy 미사용)

## 5. 프론트엔드: SSR + CDN 라이브러리

| 요소 | 선택 | 근거 |
|---|---|---|
| 폼 페이지 | Jinja2 SSR | SEO 불필요, JS 프레임워크 오버킬 |
| 관리자 페이지 | Jinja2 SSR + Plotly.js | 인터랙티브 차트가 필요한 부분만 클라이언트 JS |
| CSS | Tailwind CSS (CDN) | 빌드 단계 없음, KICT 정체성 유지 |
| 차트 라이브러리 | Plotly.js (CDN) | 한국어 라벨·인터랙션·다운로드 기본 지원 |
| 폼 검증 | 브라우저 native + Pydantic | 별도 검증 라이브러리 불필요 |

## 6. 데이터 모델 (PDF 양식 매핑)

PDF 첨부 양식 기반 단일 테이블 `responses`:

### 식별·메타
- `id`: UUID primary key
- `created_at`, `updated_at`: timestamp
- `submission_status`: 'submitted' (현재는 단일 상태)
- `client_ip_hash`: 중복 방지 및 비식별화 (선택)

### 과제 정보
- `project_title`: text — 과제명(기술명)
- `keywords`: text — 키워드 (쉼표 구분)

### 기술 분류 (다중 체크)
- `tech_cat_rc_competitive`: boolean — RC 동등 이상 가격·성능 경쟁력
- `tech_cat_zero_fatality`: boolean — 사망사고 제로 지향
- `tech_cat_marketability`: boolean — 모듈러 건축 상품성 확보
- `tech_cat_scaleup`: boolean — 모듈러 건축산업 스케일업 기반조성
- `tech_cat_other`: boolean — 기타
- `tech_cat_other_text`: text — 기타 내용

### 기술 내용
- `tech_overview`: text — 기술 개요(정의·개념)
- `tech_necessity`: text — 기술 필요성
- `research_content`: text — 연구내용
- `final_outcome`: text — 최종 성과물

### 기대효과
- `impact_socioeconomic`: text — 경제사회적 관점
- `impact_scientific`: text — 과학기술적 관점

### 연구기간
- `research_period_years`: integer (1~7)

### 제안자 정보
- `proposer_name`: text
- `proposer_organization`: text
- `proposer_position`: text
- `proposer_phone`: text
- `proposer_email`: text

### 성과물 유형 (다중 체크)
- `output_type_system`: boolean — 시스템
- `output_type_method`: boolean — 공법·기법
- `output_type_material`: boolean — 재료·자재
- `output_type_software`: boolean — 소프트웨어
- `output_type_equipment`: boolean — 장비·장치
- `output_type_standard`: boolean — 기준·지침

## 7. 라우트 구성

| 경로 | 메서드 | 용도 | 인증 |
|---|---|---|---|
| `/` | GET | 설문 폼 페이지 | 없음 |
| `/submit` | POST | 응답 저장 | 없음 |
| `/thank-you` | GET | 제출 완료 페이지 | 없음 |
| `/admin/login` | GET, POST | 관리자 로그인 | - |
| `/admin` | GET | 통계 대시보드 | 세션 |
| `/admin/responses` | GET | 응답 목록 (JSON) | 세션 |
| `/admin/statistics` | GET | 집계 결과 (JSON, Plotly용) | 세션 |
| `/admin/export/excel` | GET | Excel 다운로드 | 세션 |
| `/admin/export/word` | GET | Word 보고서 다운로드 | 세션 |

**관리자 인증**: 단순 비밀번호 기반 + FastAPI 세션 쿠키.
KICT 내부 활용이므로 OAuth·다중 사용자 미구현. 필요 시 차후 확장.

## 8. 통계 항목

PDF 양식의 모든 구조화된 필드를 자동 집계:

1. **응답 현황**: 총 응답 수, 일별 응답 추이 (라인 차트)
2. **기술 분류 분포**: 4개 카테고리 + 기타 빈도 (가로 막대 차트, 다중 체크 고려)
3. **연구기간 분포**: 1~7년 빈도 (세로 막대 차트)
4. **성과물 유형 분포**: 6종 빈도 (가로 막대 차트, 다중 체크 고려)
5. **제안자 소속 분포**: 산·학·연·관 추정 분류 (도넛 차트)
6. **키워드 빈도**: 쉼표 분리 후 상위 30개 (워드클라우드 또는 막대 차트)
7. **자유 텍스트 길이**: 응답자별 작성 분량 분포 (히스토그램, 응답 품질 지표)

## 9. 내보내기 형식

### Excel (`/admin/export/excel`)

multi-sheet 구조:
1. **`응답_원본`**: 모든 응답 raw data (행 = 응답자, 열 = 필드)
2. **`기술분류_집계`**: 카테고리별 빈도표
3. **`연구기간_집계`**: 연도별 빈도표
4. **`성과물유형_집계`**: 유형별 빈도표
5. **`제안자_명단`**: 이름·소속·직위·연락처만 별도 시트
6. **`요약통계`**: 주요 지표 요약

### Word (`/admin/export/word`)

KICT 보고서 양식 기반:
1. 표지: 제목·기간·응답 수
2. 응답 현황 요약 (텍스트)
3. 기술분류 분석 (표 + 차트 이미지)
4. 연구기간 분석 (표 + 차트 이미지)
5. 성과물 유형 분석 (표 + 차트 이미지)
6. 주요 키워드 (워드클라우드 이미지)
7. 응답자 의견 발췌 (자유 텍스트 일부)
8. 부록: 전체 응답 명단

## 10. 보안·개인정보

- **개인정보 항목**: 성명, 소속기관, 직위, 연락처, 이메일 (제안자 인적사항)
- **저장 위치**: Supabase Postgres (해외 호스팅, ap-northeast-2 서울 리전)
- **권장 조치**:
  - 응답자에게 사전 동의 문구 폼 첫 부분에 명시
  - HTTPS 강제 (Render 기본 제공)
  - 관리자 페이지 접근 비밀번호 강력하게 설정
  - 종료 후 raw data 백업 → Supabase 프로젝트 삭제 가능
- **KICT 공식 활용 시**: 정보화 부서 사전 협의 권장 (해외 클라우드 저장 검토)

## 11. 운영 시 알려진 제약

- **Cold start**: Render 무료 Web Service는 15분 무요청 시 휴면 → 다음 요청 시 ~30~60초 깨어남. 응답자에게 첫 화면 로딩 시 짧은 대기 발생할 수 있음. 마감일 임박 시 외부 모니터링(UptimeRobot 등)으로 5분마다 ping 보내 휴면 방지 가능.
- **750시간 제한**: 1개월 31일 × 24시간 = 744시간 < 750시간이므로 단일 서비스 전체 가동 시에도 한도 내. 여러 서비스 동시 가동 시에만 주의.
- **Supabase 1주일 무접속 휴면**: 주 1회 이상 관리자 페이지 접속하면 휴면 방지. 휴면 시 다음 요청 시 자동 복구.

## 12. 확장 로드맵 (선택)

수요조사가 성공적으로 운영된 이후 추가 가능한 기능:

- 응답 임시저장(draft) 기능 — DB에 status 컬럼 추가
- 응답자별 수정 링크 (이메일로 발송)
- 파일 첨부 (PDF·이미지) — Supabase Storage 활용
- 다국어 (영문 폼) — 해외 전문가 참여 시
- 관리자 다중 계정 — OAuth (Google Workspace 연동)
- 익명/실명 토글
