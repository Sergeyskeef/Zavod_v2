# scripts/run_blotato_create_from_last_run.py
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.models.brand_profile import BrandProfile  # noqa: E402
from src.clients.blotato_client import BlotatoClient  # noqa: E402
from src.pipeline.blotato_adapter import to_blotato_payload  # noqa: E402
from src.api.utils import reconstruct_analyzed_and_carousel  # noqa: E402


def load_last_run(path: Path) -> dict:
    if not path.exists():
        raise RuntimeError(f"runs file not found: {path}")
    last_line = None
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            last_line = line
    if last_line is None:
        raise RuntimeError("runs file is empty")
    return json.loads(last_line)


def main() -> None:
    load_dotenv()

    runs_path = ROOT / "data" / "runs.jsonl"
    try:
        run_dict = load_last_run(runs_path)
    except Exception as e:
        print(f"Error loading runs: {e}")
        return

    analyzed, carousel = reconstruct_analyzed_and_carousel(run_dict)

    # Пока используем один тестовый профиль бренда
    brand = BrandProfile(
        id="default",
        name="WB Expert",
        primary_color="#6C5CE7",
        secondary_color="#FFFFFF",
        font_family="Inter",
        expert_name="WB Expert",
        expert_photo_url=os.getenv("EXPERT_PHOTO_URL", ""),
        blotato_template_id=os.getenv("BLOTATO_TEMPLATE_ID", "base/slides/tutorial-carousel"),
        style_hint="Современный, чистый, минималистичный стиль для предпринимателей.",
    )

    payload = to_blotato_payload(carousel, analyzed, brand)

    # По умолчанию dry_run=True.
    dry_run_env = os.getenv("BLOTATO_DRY_RUN", "true").lower()
    dry_run = dry_run_env != "false"

    client = BlotatoClient.from_env(dry_run=dry_run)

    print(f"Blotato dry_run = {client.dry_run}")
    try:
        result = client.create_video_from_template(payload)
        print("Blotato response:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Blotato request failed: {e}")


if __name__ == "__main__":
    main()
