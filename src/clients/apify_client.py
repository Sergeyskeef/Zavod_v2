# src/clients/apify_client.py
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

import httpx

from src.config.settings import Settings


class ApifyClientError(Exception):
    """Базовое исключение для ошибок ApifyClient."""
    pass


class ApifyClient:
    """HTTP-клиент для работы с Apify API v2."""

    def __init__(self, settings: Settings, *, timeout: float = 60.0) -> None:
        self._settings = settings
        self._timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    @property
    def token(self) -> str:
        return self._settings.apify.api_token

    @property
    def base_url(self) -> str:
        return self._settings.apify.base_url

    def start_actor(self, actor_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Запускает актор и возвращает данные о запуске (Run object)."""
        url = f"{self.base_url}/acts/{actor_id}/runs"
        params = {"token": self.token}
        try:
            resp = self._client.post(url, params=params, json=input_payload)
            resp.raise_for_status()
            return resp.json()["data"]
        except Exception as e:
            raise ApifyClientError(f"Не удалось запустить актор {actor_id}: {e}")

    def get_run(self, run_id: str) -> Dict[str, Any]:
        """Получает актуальную информацию о запуске."""
        url = f"{self.base_url}/actor-runs/{run_id}"
        params = {"token": self.token}
        try:
            resp = self._client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()["data"]
        except Exception as e:
            raise ApifyClientError(f"Не удалось получить статус запуска {run_id}: {e}")

    def get_dataset_items(self, dataset_id: str) -> List[Dict[str, Any]]:
        """Получает элементы из датасета."""
        url = f"{self.base_url}/datasets/{dataset_id}/items"
        params = {"token": self.token}
        try:
            resp = self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else []
        except Exception as e:
            raise ApifyClientError(f"Не удалось получить данные из датасета {dataset_id}: {e}")

    def wait_for_run(self, run_id: str, timeout_sec: int = 300, polling_interval: int = 10) -> Dict[str, Any]:
        """Ожидает завершения запуска."""
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            run = self.get_run(run_id)
            status = run["status"]
            if status == "SUCCEEDED":
                return run
            if status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                raise ApifyClientError(f"Запуск {run_id} завершился с ошибкой: {status}")
            
            time.sleep(polling_interval)
        
        raise ApifyClientError(f"Превышено время ожидания завершения запуска {run_id}")
