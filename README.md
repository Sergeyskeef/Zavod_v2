# WB Content Pipeline

Пайплайн для сбора и анализа контента (YouTube, TikTok, Instagram Reels) по ключевым словам Wildberries.

## Установка

1. Склонируйте репозиторий.
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Создайте файл `.env` в корне проекта и добавьте переменные окружения:
   ```env
   APIFY_TOKEN=ваш_токен_здесь
   OPENAI_API_KEY=ваш_openai_api_key
   BLOTATO_API_KEY=ваш_blotato_api_key
   APP_MODE=dev
   EXPERT_PHOTO_URL=
   BLOTATO_TEMPLATE_ID=base/slides/tutorial-carousel
   ```
   (Также поддерживается переменная `APIFY_API_TOKEN`).

## Структура проекта

- `src/config/`: Настройки проекта.
- `src/models/`: Pydantic/Dataclass модели данных.
- `src/clients/`: Клиенты для внешних API (Apify, YouTube и т.д.).
- `src/pipeline/`: Логика обработки данных.
- `src/storage/`: Работа с базой данных.
- `scripts/`: Скрипты для запуска модулей.

## Этапы разработки

1. **Этап 1**: Каркас проекта (текущий).
2. **Этап 2**: Интеграция YouTube через Apify.
3. **Этап 3**: Интеграция TikTok.
4. **Этап 4**: Интеграция Instagram Reels.
5. **Этап 5**: Скоринг (метрики + LLM).
6. **Этап 6**: Сохранение в хранилище.
