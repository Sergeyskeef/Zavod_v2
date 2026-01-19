from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict

from src.models.reference import Reference
from src.models.analyzed_content import AnalyzedContent
from src.models.carousel import CarouselSpec


@dataclass
class PersistedRun:
    """
    Одна «сессия» пайплайна: от референса до готовой карусели.
    """

    created_at: datetime

    reference: Reference
    analyzed: AnalyzedContent
    carousel: CarouselSpec

    def to_serializable_dict(self) -> Dict[str, Any]:
        """
        Преобразует объект в JSON‑совместимый dict.
        Даты -> isoformat, Enum -> value.
        """
        def convert(obj: Any) -> Any:
            from enum import Enum
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, Enum):
                return obj.value
            if hasattr(obj, "__dataclass_fields__"):
                return {k: convert(v) for k, v in asdict(obj).items()}
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [convert(v) for v in obj]
            return obj

        return convert(self)
