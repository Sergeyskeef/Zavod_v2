from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"


@dataclass
class GenerationTask:
    """
    Задача на генерацию карусели.

    Минимальный контракт:
    - id: уникальный идентификатор задачи.
    - source_url: ссылка на видео (пока YouTube).
    - platform: платформа ("youtube" и т.п.).
    - status: статус задачи.
    - error: текст ошибки, если FAILED.
    """

    id: str
    source_url: str
    platform: str

    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    # ID PersistedRun, если задача успешно отработала
    run_id: Optional[str] = None

    # краткий текст ошибки, если статус FAILED
    error: Optional[str] = None

    @classmethod
    def new(cls, source_url: str, platform: str = "youtube") -> "GenerationTask":
        now = datetime.utcnow()
        return cls(
            id=str(uuid4()),
            source_url=source_url,
            platform=platform,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

    def to_serializable_dict(self) -> Dict[str, Any]:
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
