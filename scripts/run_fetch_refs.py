# scripts/run_fetch_refs.py
from __future__ import annotations

import json
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.config.settings import Settings  # noqa: E402
from src.pipeline.fetch_refs import fetch_all_refs  # noqa: E402


def main() -> None:
    # load_dotenv() вызывается автоматически при импорте из src/__init__.py
    
    try:
        settings = Settings.from_env()
        print(f"App mode: {settings.app_mode}")
        print(f"YouTube queries per run: {settings.limits.youtube_max_queries}")
        print(f"YouTube results per query: {settings.limits.youtube_max_results}")
        print("-" * 40)
        
        print(f"Запуск сбора референсов из YouTube...")
        
        refs = fetch_all_refs(settings)

        print(f"\nСобрано референсов: {len(refs)}")
        
        if refs:
            # Вывод первых результатов для проверки
            print("\nПримеры результатов:")
            for ref in refs:
                print(json.dumps(
                    {
                        "platform": ref.platform.value,
                        "url": ref.url,
                        "title": ref.title,
                        "views": ref.metrics.views,
                        "er": f"{ref.metrics.engagement_rate:.4f}",
                        "published": ref.publish_date.isoformat(),
                    },
                    ensure_ascii=False,
                    indent=2
                ))
                print("-" * 20)
            
    except RuntimeError as e:
        print(f"Ошибка конфигурации: {e}")
        print("Убедитесь, что APIFY_TOKEN установлен в .env или в переменных окружения.")
        sys.exit(1)
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
