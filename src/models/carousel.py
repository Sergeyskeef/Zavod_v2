# src/models/carousel.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class SlideType(str, Enum):
    HOOK = "hook"          # первый слайд, хук
    CONTENT = "content"    # основной контент
    CTA = "cta"            # призыв к действию


@dataclass
class Slide:
    """Один слайд карусели."""
    index: int
    type: SlideType
    title: str
    body: str
    # Короткая подсказка по визуалу (для будущего дизайнера/генератора)
    visual_hint: Optional[str] = None
    
    # Нужно ли показывать фото эксперта на этом слайде
    show_expert_photo: bool = False


@dataclass
class CarouselSpec:
    """
    Полная спецификация карусели под тему WB.

    - slides: последовательность слайдов (от 1 до 10).
    - main_angle: общий угол/тема карусели (заголовок).
    - content_type: тип контента (протягиваем из AnalyzedContent).
    """

    reference_url: str
    main_angle: str
    content_type: str

    slides: List[Slide]

    # Дополнительно: будущий caption и список хэштегов (опционально)
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None

    # Для какого бренда/эксперта это карусель
    brand_profile_id: Optional[str] = None
