# scripts/run_api.py
import sys
from pathlib import Path

import uvicorn

# Добавляем корень проекта в sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    print("Starting Zavod Carousel API...")
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
