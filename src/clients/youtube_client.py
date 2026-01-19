# src/clients/youtube_client.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.clients.apify_client import ApifyClient, ApifyClientError
from src.config.settings import Settings
from src.models.reference import EngagementMetrics, Platform, Reference


class YouTubeClient:
    """
    Клиент для работы с Apify actor'ом streamers/youtube-scraper через поллинг.
    """

    ACTOR_ID = "streamers~youtube-scraper"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._apify = ApifyClient(settings)

    def fetch_search_videos(
        self,
        query: str,
        *,
        max_results: Optional[int] = None,
        max_age_days: Optional[int] = None,
    ) -> List[Reference]:
        """Ищет видео и ждет завершения работы актора."""
        fetch_cfg = self._settings.fetch
        max_results = max_results or self._settings.limits.youtube_max_results
        max_age_days = max_age_days or fetch_cfg.max_age_days

        input_payload: Dict[str, Any] = {
            "searchKeywords": query,
            "maxResults": max_results,
            "postsFromDate": f"{max_age_days} days ago",
        }

        print(f"--- YouTube Search ---")
        print(f"Query: {query}")
        
        try:
            run = self._apify.start_actor(self.ACTOR_ID, input_payload)
            run_id = run["id"]
            print(f"Actor started. Run ID: {run_id}")
            
            print("Waiting for completion (polling)...")
            final_run = self._apify.wait_for_run(run_id, timeout_sec=600)
            
            ds_id = final_run["defaultDatasetId"]
            items = self._apify.get_dataset_items(ds_id)
            
            print(f"DEBUG: Apify returned {len(items)} items before filtering.")

        except ApifyClientError as e:
            print(f"YouTube search failed: {e}")
            return []

        references: List[Reference] = []
        for i, item in enumerate(items):
            ref = self._map_item_to_reference(item)
            if not ref:
                # В dev-режиме выведем ключи, если маппинг не удался
                if self._settings.app_mode == "dev" and i < 2:
                    print(f"DEBUG item[{i}] keys: {list(item.keys())}")
                continue
            
            if self._settings.app_mode == "dev":
                references.append(ref)
            else:
                if ref.is_recent(max_age_days=max_age_days):
                    references.append(ref)

        print(f"DEBUG: Returning {len(references)} Reference objects.")
        return references

    def _map_item_to_reference(self, item: Dict[str, Any]) -> Optional[Reference]:
        """Мапит элемент ответа в Reference согласно контракту данных."""
        try:
            url = item.get("url") or item.get("videoUrl")
            if not url: return None

            title = item.get("title") or "No title"
            author = item.get("channelName") or item.get("author") or "Unknown"

            # Дата (расширенный поиск)
            raw_date = (
                item.get("uploadDate") 
                or item.get("publishedAt") 
                or item.get("publishDate")
                or item.get("date")
            )
            publish_date = self._parse_publish_date(raw_date)
            
            # В dev-режиме подставляем текущую дату, если парсинг не удался
            if not publish_date and self._settings.app_mode == "dev":
                publish_date = datetime.now()
            
            if not publish_date:
                return None

            # Фактура
            description = item.get("description") or item.get("text") or ""
            tags = item.get("hashtags") or item.get("tags") or []
            
            # Длительность (с поддержкой HH:MM:SS)
            duration_raw = item.get("durationSeconds") or item.get("duration")
            duration_sec = self._parse_duration(duration_raw)

            # Метрики (с защитой от строк типа "35,369")
            def to_int(val: Any) -> int:
                if not val: return 0
                if isinstance(val, int): return val
                try:
                    s = str(val).replace(",", "").replace(" ", "").split(".")[0]
                    return int(s)
                except (ValueError, TypeError):
                    return 0

            metrics = EngagementMetrics(
                views=to_int(item.get("viewCount") or item.get("views")),
                likes=to_int(item.get("likeCount") or item.get("likes")),
                comments=to_int(item.get("commentCount") or item.get("comments")),
            )

            return Reference(
                platform=Platform.YOUTUBE,
                url=url,
                title=title,
                author=author,
                publish_date=publish_date,
                metrics=metrics,
                duration_sec=duration_sec,
                caption_or_description=description,
                tags=tags,
                raw=item
            )
        except Exception as e:
            if self._settings.app_mode == "dev":
                print(f"DEBUG Mapping error: {e}")
            return None

    @staticmethod
    def _parse_duration(raw: Any) -> Optional[int]:
        """Парсит длительность из секунд (int) или формата HH:MM:SS (str)."""
        if not raw: return None
        if isinstance(raw, int): return raw
        if isinstance(raw, (float, str)):
            s = str(raw).strip()
            if ":" in s:
                parts = s.split(":")
                try:
                    if len(parts) == 3: # HH:MM:SS
                        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    elif len(parts) == 2: # MM:SS
                        return int(parts[0]) * 60 + int(parts[1])
                except (ValueError, TypeError):
                    return None
            try:
                return int(float(s))
            except (ValueError, TypeError):
                return None
        return None

    @staticmethod
    def _parse_publish_date(raw: Any) -> Optional[datetime]:
        if not raw: return None
        try:
            if isinstance(raw, str):
                clean_raw = raw.replace("Z", "+00:00")
                try:
                    return datetime.fromisoformat(clean_raw)
                except ValueError:
                    if len(raw) >= 10:
                        try:
                            return datetime.strptime(raw[:10], "%Y-%m-%d")
                        except ValueError:
                            pass
            if isinstance(raw, (int, float)):
                return datetime.fromtimestamp(raw)
        except Exception:
            return None
        return None
