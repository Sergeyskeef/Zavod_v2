# src/pipeline/fetch_refs.py
from __future__ import annotations

from typing import Iterable, List, Optional
from urllib.parse import parse_qs, urlparse, urlunparse

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
    yt_client = YouTubeClient(settings)
    normalized_target = _normalize_youtube_url(url)

    # Сначала пробуем прямой fetch по URL
    direct_ref = yt_client.fetch_video_by_url(url)
    if direct_ref:
        if _normalize_youtube_url(direct_ref.url) == normalized_target:
            print(f"Success! Found via direct fetch: {direct_ref.title}")
            return direct_ref
        # Если Apify вернул другое видео, все равно продолжаем искать
        print("Direct fetch returned non-matching URL, fallback to search.")

    refs = fetch_all_refs(settings)
    
    for ref in refs:
        if _normalize_youtube_url(ref.url) == normalized_target:
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


def _normalize_youtube_url(url: str) -> str:
    """
    Нормализует YouTube URL для сравнения:
    - youtu.be/<id> -> youtube.com/watch?v=<id>
    - удаляет лишние query-параметры, оставляя v
    """
    if not url:
        return ""
    parsed = urlparse(url)

    if "youtu.be" in parsed.netloc:
        video_id = parsed.path.strip("/")
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

    if "youtube.com" in parsed.netloc:
        qs = parse_qs(parsed.query)
        video_id = (qs.get("v") or [""])[0]
        if video_id:
            normalized = parsed._replace(path="/watch", query=f"v={video_id}", fragment="")
            return urlunparse(normalized)

    # fallback: убираем query/fragment
    normalized = parsed._replace(query="", fragment="")
    return urlunparse(normalized).rstrip("/")
