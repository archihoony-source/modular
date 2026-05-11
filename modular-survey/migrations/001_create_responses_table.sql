-- ============================================================================
-- 차세대 모듈러 건축 핵심기술 수요조사 - 응답 저장 테이블
--
-- 사용법: Supabase Dashboard > SQL Editor에 이 파일 전체를 붙여넣고 RUN
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS responses (
    -- 식별 / 메타
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submission_status           VARCHAR(20) NOT NULL DEFAULT 'submitted',
    client_ip_hash              VARCHAR(64),

    -- 과제 정보
    project_title               TEXT NOT NULL,
    keywords                    TEXT,

    -- 기술 분류 (다중 체크)
    tech_cat_rc_competitive     BOOLEAN NOT NULL DEFAULT FALSE,
    tech_cat_zero_fatality      BOOLEAN NOT NULL DEFAULT FALSE,
    tech_cat_marketability      BOOLEAN NOT NULL DEFAULT FALSE,
    tech_cat_scaleup            BOOLEAN NOT NULL DEFAULT FALSE,
    tech_cat_other              BOOLEAN NOT NULL DEFAULT FALSE,
    tech_cat_other_text         TEXT,

    -- 기술 내용
    tech_overview               TEXT NOT NULL,
    tech_necessity              TEXT,
    research_content            TEXT,
    final_outcome               TEXT,

    -- 기대효과
    impact_socioeconomic        TEXT,
    impact_scientific           TEXT,

    -- 연구기간 (1~7년)
    research_period_years       SMALLINT CHECK (research_period_years BETWEEN 1 AND 7),

    -- 제안자 정보
    proposer_name               VARCHAR(100) NOT NULL,
    proposer_organization       VARCHAR(200) NOT NULL,
    proposer_position           VARCHAR(100),
    proposer_phone              VARCHAR(50),
    proposer_email              VARCHAR(200) NOT NULL,

    -- 성과물 유형 (다중 체크)
    output_type_system          BOOLEAN NOT NULL DEFAULT FALSE,
    output_type_method          BOOLEAN NOT NULL DEFAULT FALSE,
    output_type_material        BOOLEAN NOT NULL DEFAULT FALSE,
    output_type_software        BOOLEAN NOT NULL DEFAULT FALSE,
    output_type_equipment       BOOLEAN NOT NULL DEFAULT FALSE,
    output_type_standard        BOOLEAN NOT NULL DEFAULT FALSE,

    -- 동의 (개인정보 수집)
    privacy_consent             BOOLEAN NOT NULL DEFAULT FALSE
);

-- 인덱스: 통계 집계 시 자주 사용되는 컬럼
CREATE INDEX IF NOT EXISTS idx_responses_created_at      ON responses (created_at);
CREATE INDEX IF NOT EXISTS idx_responses_period          ON responses (research_period_years);
CREATE INDEX IF NOT EXISTS idx_responses_organization    ON responses (proposer_organization);

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_responses_updated_at ON responses;
CREATE TRIGGER trg_responses_updated_at
    BEFORE UPDATE ON responses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- (선택) 통계용 뷰
-- 관리자 대시보드에서 빠른 집계용
-- ============================================================================

CREATE OR REPLACE VIEW v_tech_category_counts AS
SELECT
    'RC 동등 이상 경쟁력' AS category, COUNT(*) FILTER (WHERE tech_cat_rc_competitive) AS cnt FROM responses
UNION ALL SELECT '사망사고 제로',         COUNT(*) FILTER (WHERE tech_cat_zero_fatality) FROM responses
UNION ALL SELECT '상품성 확보',           COUNT(*) FILTER (WHERE tech_cat_marketability) FROM responses
UNION ALL SELECT '산업 스케일업',         COUNT(*) FILTER (WHERE tech_cat_scaleup) FROM responses
UNION ALL SELECT '기타',                  COUNT(*) FILTER (WHERE tech_cat_other) FROM responses;

CREATE OR REPLACE VIEW v_output_type_counts AS
SELECT
    '시스템'      AS output_type, COUNT(*) FILTER (WHERE output_type_system) AS cnt FROM responses
UNION ALL SELECT '공법·기법',     COUNT(*) FILTER (WHERE output_type_method)    FROM responses
UNION ALL SELECT '재료·자재',     COUNT(*) FILTER (WHERE output_type_material)  FROM responses
UNION ALL SELECT '소프트웨어',    COUNT(*) FILTER (WHERE output_type_software)  FROM responses
UNION ALL SELECT '장비·장치',     COUNT(*) FILTER (WHERE output_type_equipment) FROM responses
UNION ALL SELECT '기준·지침',     COUNT(*) FILTER (WHERE output_type_standard)  FROM responses;

CREATE OR REPLACE VIEW v_research_period_counts AS
SELECT
    research_period_years AS years,
    COUNT(*) AS cnt
FROM responses
WHERE research_period_years IS NOT NULL
GROUP BY research_period_years
ORDER BY research_period_years;
