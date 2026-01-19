# src/models/brand_profile.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class BrandProfile:
    """
    Профиль бренда/эксперта, чьи карусели мы генерируем.

    В будущем это может храниться в БД или YAML/JSON.
    Пока достаточно одного-двух профилей, зашитых в код/настройки.
    """

    id: str
    name: str

    # Брендовые настройки (минимально)
    primary_color: str = "#6C5CE7"
    secondary_color: str = "#FFFFFF"
    font_family: str = "Inter"

    # Эксперт
    expert_name: str = ""
    expert_photo_url: str = ""  # внешний URL аватара / портрета

    # Связка с Blotato
    blotato_template_id: Optional[str] = None  # id шаблона (tutorial carousel и т.п.)
    style_hint: Optional[str] = None           # текстовый hint для стиля (tone of voice)
