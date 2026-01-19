# src/models/analyzed_content.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ContentType(str, Enum):
    GUIDE = "guide"          # пошаговый гайд / инструкция
    MISTAKES = "mistakes"    # ошибки, антирекомендации
    CASE = "case"            # кейс, история
    STRATEGY = "strategy"    # стратегия, подход, метод
    OTHER = "other"          # нельзя отнести однозначно


@dataclass
class AnalyzedContent:
    """
    Результат смыслового анализа одного референса под карусель WB.

    Минимальный контракт:
    - summary: краткое описание, о чём контент.
    - key_points: структурированные тезисы (будущие слайды).
    - content_type: тип контента (гайд/ошибки/кейс/стратегия/другое).
    - target_audience_score: насколько полезно новичку WB (0..1).
    - usefulness_score: общая полезность (0..1).
    - suggested_carousel_angle: формулировка угла для карусели.
    """

    reference_url: str
    title: str

    summary: str
    key_points: List[str]

    content_type: ContentType
    target_audience_score: float
    usefulness_score: float

    suggested_carousel_angle: str

    # Дополнительно, если захотим использовать дальше
    raw_llm_output: Optional[dict] = None
