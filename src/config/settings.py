# src/config/settings.py
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ApifySettings:
    api_token: str
    base_url: str = "https://api.apify.com/v2"


@dataclass
class FetchSettings:
    # общий горизонт свежести
    max_age_days: int = 90

    # лимиты по количеству результатов (наследуются из LimitsSettings в пайплайне)
    youtube_max_results: int = 50
    tiktok_max_results: int = 50
    instagram_max_results: int = 50


@dataclass
class LimitsSettings:
    # сколько поисковых запросов к YouTube можно делать за один запуск
    youtube_max_queries: int = 1
    # максимум результатов на один запрос (YouTube)
    youtube_max_results: int = 2

    # сколько референсов максимум за запуск можно отправить в LLM
    llm_max_analyses_per_run: int = 1

    # флаг включения LLM (для dry-run)
    llm_enabled: bool = True


@dataclass
class Settings:
    apify: ApifySettings
    fetch: FetchSettings
    limits: LimitsSettings
    app_mode: str = "dev"

    @classmethod
    def from_env(cls) -> "Settings":
        api_token = os.getenv("APIFY_TOKEN") or os.getenv("APIFY_API_TOKEN")
        if not api_token:
            raise RuntimeError("APIFY_TOKEN env var is required")

        app_mode = os.getenv("APP_MODE", "dev").lower()
        
        if app_mode == "prod":
            limits = LimitsSettings(
                youtube_max_queries=5,
                youtube_max_results=10,
                llm_max_analyses_per_run=20,
                llm_enabled=True
            )
        else:
            # dev mode или любое другое значение
            app_mode = "dev"
            limits = LimitsSettings(
                youtube_max_queries=1,
                youtube_max_results=2,
                llm_max_analyses_per_run=1,
                llm_enabled=True
            )

        return cls(
            apify=ApifySettings(api_token=api_token),
            fetch=FetchSettings(),
            limits=limits,
            app_mode=app_mode
        )
