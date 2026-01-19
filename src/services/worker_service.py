# src/services/worker_service.py
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from src.config.settings import Settings
from src.clients.llm_client import LlmClient
from src.models.task import TaskStatus, GenerationTask
from src.models.persisted_run import PersistedRun
from src.pipeline.fetch_refs import fetch_reference_for_url
from src.pipeline.analyze_content import analyze_reference
from src.pipeline.generate_carousel import generate_carousel_spec
from src.storage.json_storage import JsonStorage
from src.storage.task_storage import TaskStorage


class NoPendingTasks(Exception):
    """Исключение, если нет задач в очереди."""
    pass


def process_one_pending_task(root: Path) -> Optional[GenerationTask]:
    """
    Берёт одну pending-задачу, прогоняет её через весь конвейер
    и обновляет статус задачи + сохраняет PersistedRun.

    Возвращает обработанную задачу или None, если pending задач нет.
    """
    load_dotenv()
    settings = Settings.from_env()
    
    try:
        llm_client = LlmClient()
    except RuntimeError as e:
        # Если LLM не настроен, это критическая ошибка для воркера
        raise RuntimeError(f"LLM client initialization failed: {e}")

    tasks_path = root / "data" / "tasks.jsonl"
    runs_path = root / "data" / "runs.jsonl"

    task_storage = TaskStorage(tasks_path)
    storage = JsonStorage(runs_path)

    task = task_storage.fetch_next_pending()
    if task is None:
        return None

    task.status = TaskStatus.IN_PROGRESS
    task_storage.update_task(task)

    try:
        print(f"Worker service: processing task {task.id} for {task.source_url}")
        ref = fetch_reference_for_url(settings, task.source_url)
        if ref is None:
            raise RuntimeError(f"No Reference found for URL: {task.source_url}. Check if it matches search queries.")

        analyzed = analyze_reference(ref, llm_client)
        spec = generate_carousel_spec(analyzed, llm_client)

        run = PersistedRun(
            created_at=datetime.utcnow(),
            reference=ref,
            analyzed=analyzed,
            carousel=spec,
        )
        storage.append_run(run)

        task.status = TaskStatus.DONE
        task.run_id = run.created_at.isoformat()
        task_storage.update_task(task)
        print(f"Worker service: task {task.id} completed successfully")
        return task

    except Exception as exc:
        print(f"Worker service: task {task.id} failed: {exc}")
        task.status = TaskStatus.FAILED
        task.error = str(exc)
        task_storage.update_task(task)
        raise
