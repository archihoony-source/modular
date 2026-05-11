"""환경변수 기반 설정.

pydantic-settings로 .env 또는 시스템 환경변수를 자동 로드.
"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 필수
    database_url: str
    admin_password: str
    session_secret: str = "dev-secret-change-me"

    # 표시용
    survey_title: str = "차세대 모듈러 건축 핵심기술 수요조사"
    survey_deadline: str = ""

    @property
    def is_production(self) -> bool:
        return os.getenv("RENDER", "") == "true"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
