# src/services/export_service.py
from __future__ import annotations

def run_to_markdown(run_dict: dict) -> str:
    """
    Преобразует данные прогона в текстовый формат Markdown.
    """
    ref = run_dict.get("reference", {})
    analyzed = run_dict.get("analyzed", {})
    carousel = run_dict.get("carousel", {})
    
    title = carousel.get("main_angle") or ref.get("title") or "Без названия"
    url = ref.get("url", "Нет ссылки")
    
    md = [
        f"# {title}",
        "",
        f"**Источник:** [{ref.get('title', 'Видео')}]({url})",
        "",
        "## Резюме анализа",
        analyzed.get("summary", "Нет резюме"),
        "",
        "## Слайды карусели",
        ""
    ]
    
    slides = carousel.get("slides", [])
    for slide in slides:
        idx = slide.get("index", "?")
        stype = slide.get("type", "content").upper()
        stitle = slide.get("title", "")
        body = slide.get("body", "")
        hint = slide.get("visual_hint", "Нет подсказки")
        expert = "Да" if slide.get("show_expert_photo") else "Нет"
        
        md.append(f"### Слайд {idx} — {stype}: {stitle}")
        md.append(body)
        md.append("")
        md.append(f"**Визуал:** {hint}")
        md.append(f"**Фото эксперта:** {expert}")
        md.append("")
        md.append("---")
        md.append("")

    if carousel.get("caption"):
        md.append("## Текст поста (Caption)")
        md.append(carousel.get("caption"))
        md.append("")
        if carousel.get("hashtags"):
            md.append(" ".join(carousel.get("hashtags")))
            
    return "\n".join(md)
