# src/pipeline/blotato_adapter.py
from __future__ import annotations

from src.models.analyzed_content import AnalyzedContent
from src.models.carousel import CarouselSpec
from src.models.brand_profile import BrandProfile
from src.models.blotato_payload import BlotatoCreateVideoPayload, BlotatoSceneInput


def to_blotato_payload(
    carousel: CarouselSpec,
    analyzed: AnalyzedContent,
    brand: BrandProfile,
) -> BlotatoCreateVideoPayload:
    """
    Строит BlotatoCreateVideoPayload на основе карусели и профиля бренда.

    Пока без реального HTTP-запроса — только подготовка JSON.
    """
    scenes: list[BlotatoSceneInput] = []
    for slide in carousel.slides:
        scenes.append(
            BlotatoSceneInput(
                text_title=slide.title,
                text_body=slide.body,
                visual_hint=slide.visual_hint,
                use_expert_photo=slide.show_expert_photo,
            )
        )

    script = carousel.main_angle or analyzed.title
    style = brand.style_hint or ""

    return BlotatoCreateVideoPayload(
        template_id=brand.blotato_template_id or "base/slides/tutorial-carousel",
        script=script,
        caption=carousel.caption,
        scenes=scenes,
        style=style,
    )
