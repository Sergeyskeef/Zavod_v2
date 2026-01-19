# src/clients/blotato_client.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from src.models.blotato_payload import BlotatoCreateVideoPayload


class BlotatoClientError(Exception):
    """Custom exception for Blotato client errors."""
    pass


@dataclass
class BlotatoClient:
    """
    Минимальный клиент для Blotato API.

    Документация:
    - Quickstart: https://help.blotato.com/api/start
    - Create video: https://help.blotato.com/api/api-reference/create-video

    Важно:
    - Никаких автоматических циклов.
    - Один вызов = одно намеренное создание визуала.
    """

    api_key: str
    base_url: str = "https://backend.blotato.com"
    timeout: float = 60.0
    dry_run: bool = True  # по умолчанию НИЧЕГО не отправляем, только печатаем payload

    def __post_init__(self) -> None:
        self._client = httpx.Client(timeout=self.timeout)

    @classmethod
    def from_env(cls, dry_run: bool = True) -> "BlotatoClient":
        api_key = os.getenv("BLOTATO_API_KEY")
        if not api_key:
            # В режиме dry_run ключ не обязателен, но для реальности лучше проверить
            if not dry_run:
                raise RuntimeError("BLOTATO_API_KEY env var is required for BlotatoClient")
            api_key = "dummy-key-for-dry-run"
            
        return cls(api_key=api_key, dry_run=dry_run)

    def create_video_from_template(
        self,
        payload: BlotatoCreateVideoPayload,
    ) -> Dict[str, Any]:
        """
        Создаёт видео/карусель на основе templateId и inputs.

        Если dry_run=True, только печатает JSON и возвращает фиктивный ответ.
        """
        body = payload.to_request_body()

        if self.dry_run:
            print("[BlotatoClient] DRY RUN: not sending request. Payload:")
            print(json.dumps(body, ensure_ascii=False, indent=2))
            # Возвращаем фейковый ответ, чтобы код не падал
            return {"dry_run": True, "payload": body}

        url = f"{self.base_url}/v2/videos/from-templates"
        headers = {
            "Content-Type": "application/json",
            "blotato-api-key": self.api_key,
        }

        try:
            resp = self._client.post(url, headers=headers, json=body)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise BlotatoClientError(f"Blotato HTTP error: {exc}") from exc

        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            raise BlotatoClientError(f"Invalid JSON from Blotato: {resp.text}") from exc

        return data
