# src/storage/json_storage.py
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from src.models.persisted_run import PersistedRun


class JsonStorage:
    """
    Хранит результаты прогонов пайплайна в одном JSONL‑файле:
    одна строка = один PersistedRun.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append_run(self, run: PersistedRun) -> None:
        data = run.to_serializable_dict()
        line = json.dumps(data, ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def load_runs(self, limit: int | None = None) -> List[dict]:
        """
        Простой reader на будущее. Возвращает сырые dict.
        """
        runs: List[dict] = []
        if not self.path.exists():
            return runs
        with self.path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if limit is not None and i >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                runs.append(obj)
        return runs
