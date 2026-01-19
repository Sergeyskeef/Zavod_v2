# src/pipeline/analyze_content.py
from __future__ import annotations

from typing import Optional

from src.clients.llm_client import LlmClient
from src.models.analyzed_content import AnalyzedContent, ContentType
from src.models.reference import Reference


SYSTEM_PROMPT = """
Ты — эксперт по маркетингу и запуску бизнеса на маркетплейсе Wildberries.
Твоя задача — анализировать русскоязычные видео и превращать их содержание
в основу для обучающих каруселей в соцсетях для НОВИЧКОВ на WB.

Отвечай строго в формате JSON, без пояснений, без дополнительного текста.
""".strip()


def _build_user_prompt(ref: Reference) -> str:
    title = ref.title or ""
    desc = ref.caption_or_description or ""
    transcript = ""
    raw_transcript = None
    if ref.raw:
        # Пытаемся найти транскрипт в разных полях
        raw_transcript = ref.raw.get("transcript") or ref.raw.get("subtitle") or ref.raw.get("captions")

    if isinstance(raw_transcript, str):
        transcript = raw_transcript

    text_block = "\n\n".join(
        part for part in [f"Заголовок: {title}", f"Описание: {desc}", f"Транскрипт: {transcript}"] if part.strip()
    )

    return f"""
Проанализируй следующий контент (видео с YouTube про Wildberries):

{text_block}

Нужен результат в следующем JSON-формате:

{{
  "summary": "краткое резюме видео (2-3 предложения, на русском)",
  "key_points": [
    "тезис 1 (для отдельного слайда карусели, кратко и понятно)",
    "тезис 2",
    "тезис 3"
  ],
  "content_type": "guide | mistakes | case | strategy | other",
  "target_audience_score": 0.0,
  "usefulness_score": 0.0,
  "suggested_carousel_angle": "формулировка для карусели, например: '7 ошибок новичка на Wildberries'"
}}

Требования:
- Думай о ЦА: человек, который хочет запустить бизнес на Wildberries с нуля.
- target_audience_score — от 0 до 1, где 1 — максимально полезно для такого новичка.
- usefulness_score — общая полезность контента, от 0 до 1.
- key_points должны быть 6–12 штук, каждый — отдельная мысль для слайда.
- content_type выбери один из перечисленных вариантов.
- Ответ верни ТОЛЬКО как валидный JSON.
""".strip()


def analyze_reference(ref: Reference, llm_client: LlmClient) -> AnalyzedContent:
    """
    Анализирует один Reference и возвращает структурированное описание контента
    под карусель.

    Предполагается, что ref caption_or_description уже заполнено,
    а транскрипт (если есть) лежит в ref.raw["transcript"].
    """
    user_prompt = _build_user_prompt(ref)
    llm_resp = llm_client.complete_json(SYSTEM_PROMPT, user_prompt)
    data = llm_resp.parsed

    summary = data.get("summary", "").strip()
    key_points = [kp.strip() for kp in data.get("key_points", []) if isinstance(kp, str) and kp.strip()]
    ctype_raw = (data.get("content_type") or "other").lower()

    try:
        content_type = ContentType(ctype_raw)
    except ValueError:
        content_type = ContentType.OTHER

    try:
        target_audience_score = float(data.get("target_audience_score") or 0.0)
    except (TypeError, ValueError):
        target_audience_score = 0.0

    try:
        usefulness_score = float(data.get("usefulness_score") or 0.0)
    except (TypeError, ValueError):
        usefulness_score = 0.0

    suggested_angle = data.get("suggested_carousel_angle", "").strip()

    return AnalyzedContent(
        reference_url=ref.url,
        title=ref.title,
        summary=summary,
        key_points=key_points,
        content_type=content_type,
        target_audience_score=target_audience_score,
        usefulness_score=usefulness_score,
        suggested_carousel_angle=suggested_angle,
        raw_llm_output=llm_resp.parsed,
    )


def create_dummy_analysis(ref: Reference) -> AnalyzedContent:
    """Создает заглушку анализа для dry-run режима."""
    return AnalyzedContent(
        reference_url=ref.url,
        title=ref.title,
        summary="LLM disabled (dry-run).",
        key_points=[],
        content_type=ContentType.OTHER,
        target_audience_score=0.0,
        usefulness_score=0.0,
        suggested_carousel_angle="Dry-run angle"
    )
