# src/storage/json_storage.py
from __future__ import annotations

import json
from pathlib import Path
from contextlib import contextmanager
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

    @staticmethod
    @contextmanager
    def _locked_open(path: Path, mode: str):
        """
        Открывает файл и, если доступно, ставит файловую блокировку.
        Нужна для защиты от гонок при параллельных записях/чтениях.
        """
        f = path.open(mode, encoding="utf-8")
        try:
            try:
                import fcntl
                lock_type = fcntl.LOCK_EX if "w" in mode or "a" in mode else fcntl.LOCK_SH
                fcntl.flock(f.fileno(), lock_type)
            except Exception:
                # Если блокировка недоступна, продолжаем без неё
                pass
            yield f
        finally:
            try:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            f.close()

    def append_run(self, run: PersistedRun) -> None:
        data = run.to_serializable_dict()
        line = json.dumps(data, ensure_ascii=False)
        with self._locked_open(self.path, "a") as f:
            f.write(line + "\n")

    def load_runs(self, limit: int | None = None) -> List[dict]:
        """
        Простой reader на будущее. Возвращает сырые dict.
        """
        runs: List[dict] = []
        if not self.path.exists():
            return runs
        with self._locked_open(self.path, "r") as f:
            for i, line in enumerate(f):
                if limit is not None and i >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                runs.append(obj)
        return runs
