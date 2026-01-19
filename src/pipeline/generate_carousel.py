# src/pipeline/generate_carousel.py
from __future__ import annotations

from typing import List

from src.clients.llm_client import LlmClient
from src.models.analyzed_content import AnalyzedContent
from src.models.carousel import CarouselSpec, Slide, SlideType


SYSTEM_PROMPT = """
Ты — эксперт по созданию Instagram-каруселей для предпринимателей.
Твоя задача — по уже разобранному контенту (summary + key_points + angle)
создавать структуру карусели: слайды, заголовки, тексты и финальный CTA.

Фокус: новичок, который хочет запустить бизнес на Wildberries с нуля.
Все тексты пиши по-русски, просто и конкретно.

Важно:
- У нас есть эксперт (лицо бренда) с фото.
- Отмечай, на каких слайдах нужно показывать фото эксперта (обычно HOOK и CTA, иногда 1-2 ключевых контент-слайда).
Отвечай строго в формате JSON.
""".strip()


def build_carousel_prompt(ac: AnalyzedContent) -> str:
    """
    Формирует user‑prompt для генерации структуры карусели.
    """
    key_points_block = "\n".join(f"- {kp}" for kp in ac.key_points)

    return f"""
У тебя есть проанализированный контент видео про Wildberries.

Краткое резюме:
{ac.summary}

Ключевые тезисы:
{key_points_block}

Тип контента: {ac.content_type.value}
Рекомендуемый угол карусели: {ac.suggested_carousel_angle}

Нужно создать структуру Instagram-карусели (до 10 слайдов) для новичка на WB.

Требования к структуре:
- Слайд 1: сильный HOOK (зацепка). Короткий заголовок + подзаголовок, который обещает пользу.
- Слайды 2–N-1: CONTENT — раскрывают ключевые тезисы, один слайд = одна мысль.
- Последний слайд: CTA — чёткий призыв к действию (подписаться, сохранить, написать, перейти и т.п.).
- Всего 6–10 слайдов.
- Текст на слайдах — максимально конкретный, без воды, 1–3 короткие строки.
- Пиши понятным языком для новичка, который боится «сложного бизнеса».

Верни JSON строго в формате:

{{
  "main_angle": "общий заголовок/угол карусели",
  "slides": [
    {{
      "type": "hook" | "content" | "cta",
      "title": "краткий заголовок слайда",
      "body": "2-3 строки текста, раскрывающие идею слайда",
      "visual_hint": "краткая подсказка по визуалу (иконки, иллюстрации, композиция)",
      "show_expert_photo": true | false
    }}
  ],
  "caption": "предложенный текст для описания поста",
  "hashtags": ["#wildberries", "#бизнеснанолях", "..."]
}}

Требования:
- Слайд 1 (HOOK) почти всегда show_expert_photo = true.
- Последний слайд (CTA) часто show_expert_photo = true.
- Для остальных слайдов решай по здравому смыслу.

Очень важно:
- Соблюдай структуру JSON.
- Не используй Markdown, не оборачивай JSON в ```.
- Все тексты — на русском.
""".strip()


def generate_carousel_spec(ac: AnalyzedContent, llm_client: LlmClient) -> CarouselSpec:
    """
    Генерирует структуру карусели по результатам анализа контента.
    """
    user_prompt = build_carousel_prompt(ac)
    resp = llm_client.complete_json(SYSTEM_PROMPT, user_prompt)
    data = resp.parsed

    main_angle = data.get("main_angle") or ac.suggested_carousel_angle or ac.title

    slides_data = data.get("slides") or []
    slides: List[Slide] = []

    for idx, s in enumerate(slides_data, start=1):
        raw_type = (s.get("type") or "content").lower()
        try:
            slide_type = SlideType(raw_type)
        except ValueError:
            slide_type = SlideType.CONTENT

        title = s.get("title", "").strip()
        body = s.get("body", "").strip()
        visual_hint = (s.get("visual_hint") or "").strip() or None
        show_expert_photo = bool(s.get("show_expert_photo", False))

        # простая защита от пустых слайдов
        if not title and not body:
            continue

        slides.append(
            Slide(
                index=idx,
                type=slide_type,
                title=title,
                body=body,
                visual_hint=visual_hint,
                show_expert_photo=show_expert_photo,
            )
        )

    caption = (data.get("caption") or "").strip() or None
    hashtags_raw = data.get("hashtags") or []
    hashtags = [h.strip() for h in hashtags_raw if isinstance(h, str) and h.strip()] or None

    return CarouselSpec(
        reference_url=ac.reference_url,
        main_angle=main_angle,
        content_type=ac.content_type.value,
        slides=slides,
        caption=caption,
        hashtags=hashtags,
    )


def create_dummy_carousel_spec(ac: AnalyzedContent) -> CarouselSpec:
    """
    Заглушка карусели для dry-run режима без LLM.
    """
    main_angle = ac.suggested_carousel_angle or ac.title or "Полезные советы по Wildberries"

    slides: List[Slide] = []
    slides.append(
        Slide(
            index=1,
            type=SlideType.HOOK,
            title=main_angle,
            body="Коротко и понятно для новичка на WB.",
            visual_hint="Крупный заголовок, акцентный цвет",
            show_expert_photo=True,
        )
    )

    points = ac.key_points or []
    if not points and ac.summary:
        points = [ac.summary]
    if not points:
        points = ["Соберите ключевые шаги запуска и избегайте типичных ошибок."]

    max_content = min(len(points), 8)
    for i in range(max_content):
        slides.append(
            Slide(
                index=len(slides) + 1,
                type=SlideType.CONTENT,
                title=f"Тезис {i + 1}",
                body=points[i],
                visual_hint="Иконки + короткие строки текста",
                show_expert_photo=False,
            )
        )

    slides.append(
        Slide(
            index=len(slides) + 1,
            type=SlideType.CTA,
            title="Сохрани и подпишись",
            body="Чтобы не потерять и быстрее запустить продажи.",
            visual_hint="Фото эксперта + CTA кнопка",
            show_expert_photo=True,
        )
    )

    return CarouselSpec(
        reference_url=ac.reference_url,
        main_angle=main_angle,
        content_type=ac.content_type.value,
        slides=slides,
        caption=None,
        hashtags=None,
    )
