# src/pipeline/fetch_refs.py
from __future__ import annotations

from typing import Iterable, List

from src.config.settings import Settings
from src.models.reference import Reference
from src.clients.youtube_client import YouTubeClient


# Базовый список запросов под нишу "WB с нуля"
DEFAULT_YOUTUBE_QUERIES: List[str] = [
    "бизнес на вайлдберриз с нуля",
    "как начать продавать на вайлдберриз",
    "ошибки новичков вайлдберриз",
    "как выбрать товар на вайлдберриз",
    "юнит экономика вайлдберриз",
    "как настроить рекламу на вайлдберриз",
    "оформление карточки товара вайлдберриз",
    "анализ ниши вайлдберриз",
    "бизнес под ключ вайлдберриз",
]


def fetch_all_refs(settings: Settings) -> List[Reference]:
    """
    Пайплайн сбора референсов.
    
    Собирает данные из YouTube (в будущем TikTok/Instagram).
    Использует лимиты из settings.limits.
    """
    yt_client = YouTubeClient(settings)
    
    all_references: List[Reference] = []
    
    # Ограничиваем количество запросов
    max_queries = settings.limits.youtube_max_queries
    queries_to_run = DEFAULT_YOUTUBE_QUERIES[:max_queries]
    
    for query in queries_to_run:
        try:
            # Ограничиваем количество результатов на запрос
            references = yt_client.fetch_search_videos(
                query=query,
                max_results=settings.limits.youtube_max_results
            )
            all_references.extend(references)
        except Exception as e:
            print(f"Ошибка при сборе YouTube по запросу '{query}': {e}")

    return _deduplicate_by_url(all_references)


def fetch_reference_for_url(settings: Settings, url: str) -> Optional[Reference]:
    """
    Пытается найти Reference для конкретного URL среди результатов поиска.
    Не делает дополнительных API вызовов сверх fetch_all_refs.
    """
    print(f"Searching for specific URL: {url}...")
    refs = fetch_all_refs(settings)
    
    for ref in refs:
        if ref.url == url:
            print(f"Success! Found matching Reference: {ref.title}")
            return ref
            
    print(f"Reference for URL {url} not found in current search results ({len(refs)} items).")
    return None


def _deduplicate_by_url(refs: Iterable[Reference]) -> List[Reference]:
    """Удаляет дубликаты по URL."""
    seen = set()
    result: List[Reference] = []
    for ref in refs:
        if ref.url in seen:
            continue
        seen.add(ref.url)
        result.append(ref)
    return result
