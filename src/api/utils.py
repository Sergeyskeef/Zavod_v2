# src/api/utils.py
from __future__ import annotations

from src.models.analyzed_content import AnalyzedContent, ContentType
from src.models.carousel import CarouselSpec, Slide, SlideType


def reconstruct_analyzed_and_carousel(run_dict: dict) -> tuple[AnalyzedContent, CarouselSpec]:
    """
    Восстанавливает объекты AnalyzedContent и CarouselSpec из словаря.
    """
    analyzed_dict = run_dict["analyzed"]
    carousel_dict = run_dict["carousel"]

    analyzed = AnalyzedContent(
        reference_url=analyzed_dict["reference_url"],
        title=analyzed_dict["title"],
        summary=analyzed_dict["summary"],
        key_points=analyzed_dict["key_points"],
        content_type=ContentType(analyzed_dict["content_type"]),
        target_audience_score=analyzed_dict["target_audience_score"],
        usefulness_score=analyzed_dict["usefulness_score"],
        suggested_carousel_angle=analyzed_dict["suggested_carousel_angle"],
        raw_llm_output=analyzed_dict.get("raw_llm_output"),
    )

    slides: list[Slide] = []
    for s in carousel_dict["slides"]:
        slides.append(
            Slide(
                index=s["index"],
                type=SlideType(s["type"]),
                title=s["title"],
                body=s["body"],
                visual_hint=s.get("visual_hint"),
                show_expert_photo=s.get("show_expert_photo", False),
            )
        )

    carousel = CarouselSpec(
        reference_url=carousel_dict["reference_url"],
        main_angle=carousel_dict["main_angle"],
        content_type=carousel_dict["content_type"],
        slides=slides,
        caption=carousel_dict.get("caption"),
        hashtags=carousel_dict.get("hashtags"),
        brand_profile_id=carousel_dict.get("brand_profile_id"),
    )

    return analyzed, carousel
