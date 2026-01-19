# src/models/reference.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class Platform(str, Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"


@dataclass
class EngagementMetrics:
    views: int
    likes: int
    comments: int
    shares: int = 0

    @property
    def engagement_rate(self) -> float:
        """Простейший ER: (likes + comments + shares) / views."""
        if self.views <= 0:
            return 0.0
        return (self.likes + self.comments + self.shares) / self.views


@dataclass
class Reference:
    """
    Унифицированный референс из YT/TikTok/IG.
    
    МИНИМАЛЬНЫЙ КОНТРАКТ ДАННЫХ:
    - url: ссылка на контент.
    - title: заголовок видео/поста (hook).
    - author: автор/канал (Optional).
    - publish_date: дата публикации.
    - metrics.views: количество просмотров (для скоринга).
    - duration_sec: длительность в секундах (Optional).
    - caption_or_description: описание или текст поста (фактура для анализа).
    - tags: список тегов/хэштегов.
    - raw: оригинальный ответ источника (Dict).
    """

    platform: Platform
    url: str
    title: str
    author: Optional[str]
    publish_date: datetime

    metrics: EngagementMetrics

    duration_sec: Optional[int] = None
    caption_or_description: Optional[str] = None
    tags: List[str] = None

    # сюда можно класть сырой ответ источника
    raw: Dict[str, Any] = None

    # дальше под скоринг
    topic_score: Optional[float] = None
    popularity_score: Optional[float] = None
    final_score: Optional[float] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.raw is None:
            self.raw = {}

    def is_recent(self, max_age_days: int = 90, now: Optional[datetime] = None) -> bool:
        """Проверка на свежесть (по умолчанию <= 90 дней)."""
        now = now or datetime.utcnow()
        age = now - self.publish_date
        return age.days <= max_age_days
