# scripts/print_blotato_payload.py
import json
import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.models.brand_profile import BrandProfile
from src.pipeline.blotato_adapter import to_blotato_payload
from src.storage.json_storage import JsonStorage


def main():
    runs_path = Path(ROOT) / "data" / "runs.jsonl"
    storage = JsonStorage(runs_path)
    runs = storage.load_runs()

    if not runs:
        print("No runs found in data/runs.jsonl. Run a pipeline first.")
        return

    # Берем последний прогон
    run = runs[-1]
    
    # Создаем фиктивный профиль бренда
    brand = BrandProfile(
        id="wb-expert-01",
        name="WB Guru",
        expert_name="Mark",
        expert_photo_url="https://example.com/expert.jpg",
        blotato_template_id="base/slides/tutorial-carousel",
        style_hint="Professional, encouraging, expert tone"
    )

    print(f"Generating Blotato payload for run from: {run.created_at}")
    print(f"Reference: {run.reference.title}")
    print("-" * 20)

    payload = to_blotato_payload(run.carousel, run.analyzed, brand)
    body = payload.to_request_body()

    print(json.dumps(body, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
