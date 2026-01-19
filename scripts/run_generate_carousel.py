# scripts/run_generate_carousel.py
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.config.settings import Settings  # noqa: E402
from src.clients.llm_client import LlmClient  # noqa: E402
from src.pipeline.fetch_refs import fetch_all_refs  # noqa: E402
from src.pipeline.analyze_content import analyze_reference  # noqa: E402
from src.pipeline.generate_carousel import generate_carousel_spec  # noqa: E402
from src.models.persisted_run import PersistedRun  # noqa: E402
from src.storage.json_storage import JsonStorage  # noqa: E402


def main() -> None:
    # Загружаем переменные окружения
    load_dotenv()
    
    settings = Settings.from_env()
    
    try:
        llm_client = LlmClient()
    except RuntimeError as e:
        print(f"Ошибка инициализации LLM: {e}")
        return

    print(f"App mode: {settings.app_mode}")
    print(f"YouTube queries per run: {settings.limits.youtube_max_queries}")
    print(f"YouTube results per query: {settings.limits.youtube_max_results}")
    print(f"LLM enabled: {settings.limits.llm_enabled}")
    print(f"LLM analyses per run: {settings.limits.llm_max_analyses_per_run}")
    print("----------------------------------------")

    print("Сбор референсов...")
    refs = fetch_all_refs(settings)
    if not refs:
        print("Референсы не найдены.")
        return

    # Берем первый найденный референс
    ref = refs[0]
    print(f"\nБудем строить карусель по видео:\nURL: {ref.url}\nTitle: {ref.title}\n")

    print("Анализ контента (модуль 2)...")
    if not settings.limits.llm_enabled:
        print("LLM выключен в настройках. Невозможно сгенерировать карусель.")
        return
        
    analyzed = analyze_reference(ref, llm_client)

    print("Генерация структуры карусели (модуль 3)...")
    spec = generate_carousel_spec(analyzed, llm_client)

    print("\n=== РЕЗУЛЬТАТ КАРУСЕЛИ ===")
    carousel_data = {
        "main_angle": spec.main_angle,
        "content_type": spec.content_type,
        "slides": [
            {
                "index": s.index,
                "type": s.type.value,
                "title": s.title,
                "body": s.body,
                "visual_hint": s.visual_hint,
            }
            for s in spec.slides
        ],
        "caption": spec.caption,
        "hashtags": spec.hashtags,
    }
    print(json.dumps(carousel_data, ensure_ascii=False, indent=2))

    # Сохранение результатов
    run = PersistedRun(
        created_at=datetime.utcnow(),
        reference=ref,
        analyzed=analyzed,
        carousel=spec,
    )

    storage_path = Path(ROOT) / "data" / "runs.jsonl"
    storage = JsonStorage(storage_path)
    storage.append_run(run)

    print(f"\nРезультат карусели сохранён в {storage_path}")


if __name__ == "__main__":
    main()
