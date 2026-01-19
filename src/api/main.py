# src/api/main.py
from __future__ import annotations

import sys
import json
import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Добавляем корень проекта в sys.path для импортов
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Загружаем переменные окружения
load_dotenv()

from src.models.task import GenerationTask, TaskStatus
from src.storage.task_storage import TaskStorage
from src.storage.json_storage import JsonStorage
from src.services.worker_service import process_one_pending_task
from src.services.export_service import run_to_markdown
from src.models.brand_profile import BrandProfile
from src.pipeline.blotato_adapter import to_blotato_payload
from src.clients.blotato_client import BlotatoClient
from src.api.utils import reconstruct_analyzed_and_carousel

app = FastAPI(title="Zavod Carousel API")

# Настройка шаблонов
templates = Jinja2Templates(directory=str(ROOT / "templates"))

# Инициализируем хранилища
tasks_path = ROOT / "data" / "tasks.jsonl"
runs_path = ROOT / "data" / "runs.jsonl"

# Создаем директорию data, если её нет
tasks_path.parent.mkdir(parents=True, exist_ok=True)

task_storage = TaskStorage(tasks_path)
run_storage = JsonStorage(runs_path)

def load_last_run_dict() -> dict | None:
    if not runs_path.exists():
        return None

    last_line = None
    try:
        with runs_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    last_line = line
    except Exception:
        return None
        
    if last_line is None:
        return None
    return json.loads(last_line)

# --- HTML Эндпоинты ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, status: Optional[str] = None):
    """Главная страница со списком задач и формой управления."""
    tasks = task_storage.list_tasks()
    if status:
        tasks = [t for t in tasks if t.status.value == status]
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "tasks": tasks,
            "status_filter": status,
        },
    )

@app.post("/tasks/create")
async def create_task_form(url: str = Form(...)):
    """Обработка формы создания задачи."""
    task = GenerationTask.new(source_url=url, platform="youtube")
    task_storage.add_task(task)
    return RedirectResponse(url="/", status_code=303)

@app.post("/tasks/process_one")
async def process_one_task():
    """Обрабатывает одну pending-задачу по кнопке."""
    try:
        task = process_one_pending_task(ROOT)
        if task is None:
            return RedirectResponse(url="/?msg=no_pending", status_code=303)
        return RedirectResponse(url=f"/?msg=processed&task_id={task.id}", status_code=303)
    except Exception as e:
        print(f"API Error processing task: {e}")
        return RedirectResponse(url="/?msg=error", status_code=303)

@app.post("/runs/latest/approve")
async def approve_latest_run():
    """Одобряет последнюю карусель и отправляет её в Blotato."""
    run_dict = load_last_run_dict()
    if run_dict is None:
        return RedirectResponse(url="/?msg=no_run", status_code=303)

    try:
        analyzed, carousel = reconstruct_analyzed_and_carousel(run_dict)

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
        
        # ВАЖНО: здесь dry_run=False для реальной отправки
        client = BlotatoClient.from_env(dry_run=False)
        result = client.create_video_from_template(payload)
        
        print(f"Blotato success: {result}")
        return RedirectResponse(url="/?msg=blotato_ok", status_code=303)
    except Exception as e:
        print(f"API Error approving run: {e}")
        return RedirectResponse(url="/?msg=blotato_error", status_code=303)

@app.get("/runs/latest/view", response_class=HTMLResponse)
async def view_latest_run(request: Request):
    """Страница просмотра последнего результата."""
    run_dict = load_last_run_dict()
    return templates.TemplateResponse(
        "run_view.html",
        {"request": request, "run": run_dict},
    )

@app.get("/runs/latest/markdown")
async def download_latest_markdown():
    """Скачивает последнюю карусель в формате Markdown."""
    run_dict = load_last_run_dict()
    if run_dict is None:
        return RedirectResponse(url="/?msg=no_run", status_code=303)
    
    md_content = run_to_markdown(run_dict)
    filename = "carousel-latest.md"
    
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


# --- JSON API Эндпоинты ---

class TaskCreate(BaseModel):
    url: str

class TaskResponse(BaseModel):
    id: str
    source_url: str
    status: str
    error: Optional[str] = None

@app.post("/tasks", response_model=TaskResponse)
def create_task_api(payload: TaskCreate):
    """API эндпоинт для создания задачи."""
    task = GenerationTask.new(payload.url)
    task_storage.add_task(task)
    return TaskResponse(
        id=task.id,
        source_url=task.source_url,
        status=task.status.value
    )

@app.get("/tasks", response_model=List[TaskResponse])
def list_tasks_api(status: Optional[str] = None):
    """API эндпоинт для получения списка задач."""
    tasks = task_storage.list_tasks()
    if status:
        tasks = [t for t in tasks if t.status.value == status]
    
    return [
        TaskResponse(
            id=t.id,
            source_url=t.source_url,
            status=t.status.value,
            error=t.error
        )
        for t in tasks
    ]

@app.get("/runs/latest")
def get_latest_run_api():
    """API эндпоинт для получения JSON последнего прогона."""
    runs = run_storage.load_runs()
    if not runs:
        raise HTTPException(status_code=404, detail="No runs found")
    
    last_run = runs[-1]
    return last_run.to_serializable_dict()
