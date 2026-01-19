# src/storage/task_storage.py
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.models.task import GenerationTask, TaskStatus


class TaskStorage:
    """
    Примитивное хранилище задач в JSONL-файле.

    Упрощение: при каждом изменении состояния задачи файл перезаписывается целиком.
    Для текущих объёмов это ок.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load_all(self) -> List[GenerationTask]:
        if not self.path.exists():
            return []
        tasks: List[GenerationTask] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    task = self._from_dict(obj)
                    tasks.append(task)
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"Warning: Failed to parse task line: {e}")
                    continue
        return tasks

    def _save_all(self, tasks: List[GenerationTask]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            for task in tasks:
                line = json.dumps(task.to_serializable_dict(), ensure_ascii=False)
                f.write(line + "\n")

    @staticmethod
    def _from_dict(obj: dict) -> GenerationTask:
        status = TaskStatus(obj["status"])
        created_at = datetime.fromisoformat(obj["created_at"])
        updated_at = datetime.fromisoformat(obj["updated_at"])
        return GenerationTask(
            id=obj["id"],
            source_url=obj["source_url"],
            platform=obj["platform"],
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            run_id=obj.get("run_id"),
            error=obj.get("error"),
        )

    def add_task(self, task: GenerationTask) -> None:
        tasks = self._load_all()
        tasks.append(task)
        self._save_all(tasks)

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[GenerationTask]:
        tasks = self._load_all()
        if status is None:
            return tasks
        return [t for t in tasks if t.status == status]

    def get_task(self, task_id: str) -> Optional[GenerationTask]:
        tasks = self._load_all()
        for t in tasks:
            if t.id == task_id:
                return t
        return None

    def update_task(self, task: GenerationTask) -> None:
        tasks = self._load_all()
        updated: List[GenerationTask] = []
        found = False
        for t in tasks:
            if t.id == task.id:
                task.updated_at = datetime.utcnow()
                updated.append(task)
                found = True
            else:
                updated.append(t)
        if not found:
            updated.append(task)
        self._save_all(updated)

    def fetch_next_pending(self) -> Optional[GenerationTask]:
        tasks = self._load_all()
        for task in tasks:
            if task.status == TaskStatus.PENDING:
                return task
        return None
