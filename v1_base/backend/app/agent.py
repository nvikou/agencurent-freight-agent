"""OpenAI agent — live + historique prix + historique dialogue."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
)

from baikal.tools import OPENAI_TOOLS as BAIKAL_TOOLS
from baikal.tools import execute_tool as execute_baikal_tool
from db.chat import (
    clear_chat_history,
    load_chat_history,
    save_chat_turn,
)
from db.connection import get_connection
from db.persist_live import persist_live_from_tool
from db.tools import OPENAI_TOOLS as DB_TOOLS
from db.tools import execute_tool as execute_db_tool
from dellin.tools import OPENAI_TOOLS as DELLIN_TOOLS
from dellin.tools import execute_tool as execute_dellin_tool
from pek.tools import OPENAI_TOOLS as PEK_TOOLS
from pek.tools import execute_tool as execute_pek_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Ты — нейро-аналитик конкурентов (Dellin vs ПЭК vs Baikal).
Продукт: AgenCurent.

ЖЁСТКОЕ ПРАВИЛО СРАВНЕНИЯ:
- Только транспорт базы, тариф Стандарт
- БЕЗ упаковки, документов, страховки и любых опций
- Параметры по умолчанию: 1 м³, 1 кг, 1 место
- Линии цен:
  • ПЭК — Автоперевозка
  • Dellin / Baikal — Межтерминальная перевозка

ОБЯЗАТЕЛЬНЫЙ ПОРЯДОК (каждый раз при сравнении):
1) Объяви пользователю шаги (что сейчас делаешь).
2) ВСЕГДА пересчитай LIVE всех трёх перевозчиков
   (calculate_dellin_shipping, calculate_pek_shipping,
   calculate_baikal_shipping) — даже если данные уже в БД.
   Это цена «сейчас» (момент t). После LIVE цена
   автоматически сохраняется в quotes (source=live).
3) ВСЕГДА загрузи историю цен из БД (load_quotes_from_db) —
   прошлые снимки с collected_at (collect и live).
4) В финальном ответе сравни LIVE vs ИСТОРИЯ цен.
5) Если tool вернул error — скажи и продолжай.

История диалога:
- Предыдущие реплики user/assistant уже в контексте messages
- Учитывай их (уточнения, прошлый маршрут и т.д.)

Формат ответа:
- Шаг 1… Шаг 2…
- LIVE цены
- ИСТОРИЯ цен (collected_at, source)
- Вывод / рекомендации по Dellin

Правила:
- Отвечай на русском
- Не предлагай упаковку и доп. услуги
- Города: Санкт-Петербург, Москва, Омск
- Не вызывай tools для приветствий и общих вопросов без расчёта
"""

OPENAI_TOOLS = (
    DB_TOOLS + BAIKAL_TOOLS + PEK_TOOLS + DELLIN_TOOLS
)

_GREETING_RE = re.compile(
    r"^(bonjour|salut|hello|hi|hey|привет|здравствуй|"
    r"добрый\s+(день|вечер|утро)|ку)\b",
    re.IGNORECASE,
)


def _parse_args(arguments: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(arguments, str):
        if not arguments.strip():
            return {}
        return json.loads(arguments)
    return dict(arguments or {})


def execute_tool(name: str, arguments: str | dict[str, Any]) -> str:
    """Exécute un tool et persiste les calculs LIVE."""
    args = _parse_args(arguments)

    if name == "load_quotes_from_db":
        return execute_db_tool(name, args)
    if name == "calculate_baikal_shipping":
        result = execute_baikal_tool(name, args)
    elif name == "calculate_pek_shipping":
        result = execute_pek_tool(name, args)
    elif name == "calculate_dellin_shipping":
        result = execute_dellin_tool(name, args)
    else:
        raise ValueError(f"Unknown tool: {name}")

    conn = get_connection()
    try:
        saved = persist_live_from_tool(conn, name, args, result)
        if saved:
            logger.info("LIVE saved: %s", saved)
    finally:
        conn.close()
    return result


class ShippingAgent:
    """Agent: live + historique prix + historique dialogue."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        verbose: bool = True,
        session_id: str = "default",
        history_limit: int = 20,
    ) -> None:
        load_dotenv()
        self.model = model or os.environ.get(
            "OPENAI_CHAT_MODEL",
            "gpt-4o-mini",
        )
        self.verbose = verbose
        self.session_id = session_id
        self.history_limit = history_limit
        self.client = OpenAI(
            api_key=api_key or os.environ["OPENAI_API_KEY"],
            timeout=120.0,
        )
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        self._load_dialogue_into_messages()

    def _load_dialogue_into_messages(self) -> None:
        conn = get_connection()
        try:
            history = load_chat_history(
                conn,
                session_id=self.session_id,
                limit=self.history_limit,
            )
        finally:
            conn.close()
        for item in history:
            self.messages.append(
                {"role": item["role"], "content": item["content"]}
            )
        if self.verbose and history:
            print(
                f"[dialog] chargé {len(history)} messages "
                f"(session={self.session_id})"
            )

    def reset(self, clear_db: bool = False) -> None:
        if clear_db:
            conn = get_connection()
            try:
                clear_chat_history(conn, session_id=self.session_id)
            finally:
                conn.close()
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        if not clear_db:
            self._load_dialogue_into_messages()

    def _greeting_reply(self, user_message: str) -> str | None:
        text = user_message.strip()
        if len(text) > 40:
            return None
        if not _GREETING_RE.match(text):
            return None
        return (
            "Здравствуйте! Я нейро-аналитик AgenCurent. "
            "Сравниваю Dellin, ПЭК и Baikal только по "
            "транспорту базы (тариф Стандарт, без опций). "
            "Назовите маршрут — например: "
            "Санкт-Петербург → Москва."
        )

    def chat(self, user_message: str, max_tool_rounds: int = 10) -> str:
        conn = get_connection()
        try:
            save_chat_turn(
                conn,
                session_id=self.session_id,
                role="user",
                content=user_message,
            )
        finally:
            conn.close()

        greeting = self._greeting_reply(user_message)
        if greeting:
            self.messages.append(
                {"role": "user", "content": user_message}
            )
            self.messages.append(
                {"role": "assistant", "content": greeting}
            )
            conn = get_connection()
            try:
                save_chat_turn(
                    conn,
                    session_id=self.session_id,
                    role="assistant",
                    content=greeting,
                )
            finally:
                conn.close()
            return greeting

        self.messages.append({"role": "user", "content": user_message})
        step = 0

        for _ in range(max_tool_rounds):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    tools=OPENAI_TOOLS,
                )
            except (APIConnectionError, APITimeoutError) as exc:
                return (
                    "Не удалось связаться с OpenAI API. "
                    f"Detail: {exc}"
                )
            except APIStatusError as exc:
                return (
                    "Ошибка OpenAI API "
                    f"({exc.status_code}). Проверьте ключ/квоту."
                )
            message = response.choices[0].message
            self.messages.append(
                message.model_dump(exclude_none=True)
            )

            if not message.tool_calls:
                reply = message.content or ""
                conn = get_connection()
                try:
                    save_chat_turn(
                        conn,
                        session_id=self.session_id,
                        role="assistant",
                        content=reply,
                    )
                finally:
                    conn.close()
                return reply

            for tool_call in message.tool_calls:
                step += 1
                name = tool_call.function.name
                args = tool_call.function.arguments
                if self.verbose:
                    print(f"\n[Шаг {step}] Вызываю tool: {name}")
                    print(f"         args: {args}")
                tool_result = execute_tool(name, args)
                if self.verbose:
                    preview = tool_result[:240].replace("\n", " ")
                    print(f"         результат: {preview}...")
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )

        return "Ошибка: слишком много вызовов инструментов."
