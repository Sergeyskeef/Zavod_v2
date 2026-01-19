# scripts/run_worker_once.py
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.worker_service import process_one_pending_task  # noqa: E402


def main() -> None:
    # Загружаем переменные окружения
    load_dotenv()
    
    print("Starting worker to process one pending task...")
    try:
        task = process_one_pending_task(ROOT)
        if task is None:
            print("No pending tasks found.")
        else:
            print(f"Successfully processed task {task.id} (Status: {task.status.value})")
    except Exception as e:
        print(f"Error during task processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
