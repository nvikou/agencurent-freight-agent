# AgenCurent

Нейро-аналитик конкурентов для сравнения тарифов **Dellin**, **ПЭК** и **Baikal**.  
Финальная версия дипломного проекта (GPT Engineer): веб-приложение с агентом на базе LLM, калькуляторами перевозчиков и историей цен в SQLite.

## Возможности

- Диалог с нейро-агентом (LIVE-пересчёт и сравнение с историей)
- Сохранение снимков цен в базу (`collect` / `live`)
- Веб-интерфейс: чат и таблица Quotes
- Запуск через Docker Compose

## Структура проекта

```
v1_base/
├── backend/              # FastAPI, агент, калькуляторы, SQLite
│   ├── app/              # API и бизнес-логика
│   ├── dellin/           # калькулятор Dellin
│   ├── pek/              # калькулятор ПЭК
│   ├── baikal/           # калькулятор Baikal
│   ├── db/               # схема БД, quotes, chat
│   └── scripts/          # init_db, collect, отчёты, CLI
├── frontend/             # веб-интерфейс (nginx)
├── data/                 # database.db (том Docker)
├── reports/              # отчёты Markdown
├── docker-compose.yml
└── .env.example
```

## Как работает система

1. Агент запрашивает актуальные цены у трёх перевозчиков (LIVE).
2. Успешный LIVE-расчёт сохраняется в таблицу `quotes`.
3. Из БД загружается история снимков (`collected_at`).
4. LLM формирует сравнение и рекомендации по Dellin.

## Быстрый старт (Docker)

1. Создайте файл `.env` в корне проекта (можно скопировать `.env.example`)
   и укажите ключ:

```env
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
```

2. Запустите:

```powershell
docker compose up --build -d
```

3. Откройте интерфейс:

- UI: http://localhost:3000  
- API (Swagger): http://localhost:8000/docs  

Первичный сбор цен — кнопка **«Собрать цены»** в интерфейсе или команда:

```powershell
docker compose exec backend python scripts/collect_quotes.py
```

Остановка:

```powershell
docker compose down
```

## Локальная разработка (без Docker)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:PYTHONPATH = (Get-Location).Path
$env:DATABASE_PATH = "..\data\database.db"

python scripts/init_db.py
python scripts/collect_quotes.py
uvicorn app.main:app --reload --port 8000
```

Фронтенд удобнее запускать через Docker (`frontend` в `docker-compose.yml`), либо через статический сервер с проксированием `/api` на порт `8000`.

## API

| Метод | Маршрут | Описание |
|-------|---------|----------|
| `GET` | `/api/health` | Проверка состояния сервиса |
| `POST` | `/api/chat` | Диалог с агентом |
| `GET` | `/api/chat/history` | История диалога |
| `DELETE` | `/api/chat/history` | Очистка диалога |
| `GET` | `/api/quotes` | Котировки (`latest_only`) |
| `POST` | `/api/collect` | Пакетный сбор цен в БД |

## Источники данных

| Перевозчик | Источник |
|------------|----------|
| Dellin | локальный справочник `dellin/resources.py` |
| ПЭК | API pecom.ru |
| Baikal | API request.baikalsr.ru |

## Требования

- Docker Desktop (рекомендуется)
- либо Python 3.11+
- ключ OpenAI API в файле `.env`
