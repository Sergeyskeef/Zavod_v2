# src/models/blotato_payload.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class BlotatoSceneInput:
    """
    Описание одного слайда/сцены для шаблона Blotato.

    Конкретные поля зависят от выбранного шаблона.
    Здесь мы делаем абстрактный формат:
    - text_title, text_body — текстовые блоки.
    - visual_hint — подсказка для стиля картинки.
    - use_expert_photo — флаг, нужно ли подставить фото эксперта.
    """
    text_title: str
    text_body: str
    visual_hint: Optional[str] = None
    use_expert_photo: bool = False


@dataclass
class BlotatoCreateVideoPayload:
    """
    Payload под эндпоинт Blotato `/v2/videos/from-templates`.

    Документация:
    - URL: https://backend.blotato.com/v2/videos/from-templates
    - Метод: POST
    - Заголовок: blotato-api-key: <API_KEY>
    """

    template_id: str
    script: str
    caption: Optional[str]
    scenes: List[BlotatoSceneInput]
    style: Optional[str] = None  # tone/style hint

    def to_request_body(self) -> Dict[str, Any]:
        """
        Конвертация в JSON-структуру, похожую на реальный Blotato payload.

        Пример целевого формата (упрощённый):

        {
          "templateId": "base/slides/tutorial-carousel",
          "inputs": {
            "script": "...",
            "caption": "...",
            "scenes": [
              { "title": "...", "body": "...", "visualHint": "...", "useExpertPhoto": true }
            ],
            "style": "..."
          },
          "render": true
        }
        """
        return {
            "templateId": self.template_id,
            "inputs": {
                "script": self.script,
                "caption": self.caption,
                "scenes": [
                    {
                        "title": s.text_title,
                        "body": s.text_body,
                        "visualHint": s.visual_hint,
                        "useExpertPhoto": s.use_expert_photo,
                    }
                    for s in self.scenes
                ],
                "style": self.style,
            },
            "render": True,
        }
