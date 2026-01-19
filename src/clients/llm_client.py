# src/clients/llm_client.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict

import httpx


@dataclass
class LlmResponse:
    raw: Dict[str, Any]
    parsed: Dict[str, Any]


class LlmClientError(Exception):
    ...


class LlmClient:
    """
    Минимальный клиент для вызова LLM, возвращающего строго JSON.

    По умолчанию — OpenAI Chat Completions API совместимые эндпоинты.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY env var is required for LlmClient")

        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model
        self._client = httpx.Client(timeout=timeout)

    def complete_json(self, system_prompt: str, user_prompt: str) -> LlmResponse:
        """
        Отправляет запрос к модели и ожидает, что она вернёт валидный JSON в message.content.
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }

        try:
            resp = self._client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LlmClientError(f"LLM HTTP error: {exc}") from exc

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LlmClientError(f"Unexpected LLM response structure: {data}") from exc

        # Очищаем от ```json ... ``` (на всякий случай, хотя response_format должен гарантировать JSON)
        if "```" in content:
            parts = content.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("{") and part.endswith("}"):
                    content = part
                    break
        elif "```json" in content:
             content = content.split("```json")[1].split("```")[0].strip()

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LlmClientError(f"Failed to parse LLM JSON: {content}") from exc

        return LlmResponse(raw=data, parsed=parsed)
