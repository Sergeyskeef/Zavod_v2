# scripts/run_analyze_sample.py
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.config.settings import Settings  # noqa: E402
from src.clients.llm_client import LlmClient  # noqa: E402
from src.pipeline.fetch_refs import fetch_all_refs  # noqa: E402
from src.pipeline.analyze_content import analyze_reference, create_dummy_analysis  # noqa: E402


def main() -> None:
    # Загружаем переменные окружения
    load_dotenv()

    settings = Settings.from_env()
    
    print(f"App mode: {settings.app_mode}")
    print(f"YouTube queries per run: {settings.limits.youtube_max_queries}")
    print(f"YouTube results per query: {settings.limits.youtube_max_results}")
    print(f"LLM enabled: {settings.limits.llm_enabled}")
    print(f"LLM analyses per run: {settings.limits.llm_max_analyses_per_run}")
    print("-" * 40)

    try:
        llm_client = LlmClient() if settings.limits.llm_enabled else None
    except RuntimeError as e:
        print(f"Ошибка инициализации LLM: {e}")
        print("Убедитесь, что OPENAI_API_KEY установлен в .env")
        return

    print("Сбор референсов для анализа...")
    refs = fetch_all_refs(settings)
    
    if not refs:
        print("Референсы не найдены. Проверьте настройки или API токен.")
        return

    # Ограничиваем количество анализов
    limit = settings.limits.llm_max_analyses_per_run
    refs_to_analyze = refs[:limit]
    
    print(f"Найдено {len(refs)} референсов. Анализируем {len(refs_to_analyze)}...")

    analyzed_count = 0
    for idx, ref in enumerate(refs_to_analyze, start=1):
        print(f"\n=== Анализ референса #{idx} ===")
        print(f"URL: {ref.url}")
        print(f"Title: {ref.title}")
        
        try:
            if not settings.limits.llm_enabled:
                analyzed = create_dummy_analysis(ref)
                print("(Dry-run: использована заглушка вместо вызова LLM)")
            else:
                analyzed = analyze_reference(ref, llm_client)

            print("\nРезультат анализа:")
            output = {
                "summary": analyzed.summary,
                "content_type": analyzed.content_type.value,
                "target_audience_score": analyzed.target_audience_score,
                "usefulness_score": analyzed.usefulness_score,
                "suggested_carousel_angle": analyzed.suggested_carousel_angle,
                "key_points_count": len(analyzed.key_points),
                "key_points": analyzed.key_points,
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
            analyzed_count += 1
            
        except Exception as e:
            print(f"Ошибка при анализе референса: {e}")
        
        print("-" * 40)

    print(f"\nВсего проанализировано референсов: {analyzed_count}")


if __name__ == "__main__":
    main()
