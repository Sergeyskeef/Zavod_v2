# scripts/create_task.py
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.models.task import GenerationTask  # noqa: E402
from src.storage.task_storage import TaskStorage  # noqa: E402


def main() -> None:
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python3 scripts/create_task.py <youtube_url>")
        sys.exit(1)

    url = sys.argv[1]
    task = GenerationTask.new(source_url=url, platform="youtube")

    storage = TaskStorage(Path(ROOT) / "data" / "tasks.jsonl")
    storage.add_task(task)

    print(f"Task created: {task.id}")
    print(f"Source URL: {task.source_url}")


if __name__ == "__main__":
    main()
