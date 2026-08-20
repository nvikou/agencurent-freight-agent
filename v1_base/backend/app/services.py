"""Services métier pour l'API AgenCurent."""

from __future__ import annotations

import logging
from typing import Any

from app.agent import ShippingAgent
from db.chat import clear_chat_history, load_chat_history
from db.collect import collect_all
from db.connection import get_connection, init_schema
from db.quotes import load_all_quotes, load_latest_quotes
from db.seed import seed_reference_data

logger = logging.getLogger(__name__)

_agents: dict[str, ShippingAgent] = {}


def ensure_database() -> None:
    """Crée schéma + seed si besoin."""
    conn = get_connection()
    try:
        init_schema(conn)
        seed_reference_data(conn)
    finally:
        conn.close()


def get_agent(session_id: str) -> ShippingAgent:
    agent = _agents.get(session_id)
    if agent is None:
        agent = ShippingAgent(
            session_id=session_id,
            verbose=False,
        )
        _agents[session_id] = agent
    return agent


def chat(session_id: str, message: str) -> str:
    agent = get_agent(session_id)
    return agent.chat(message)


def list_quotes(*, latest_only: bool = True) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        if latest_only:
            return load_latest_quotes(conn)
        return load_all_quotes(conn, latest_only=False)
    finally:
        conn.close()


def run_collect() -> dict[str, Any]:
    conn = get_connection()
    try:
        results = collect_all(conn)
    finally:
        conn.close()
    ok = sum(1 for r in results if r.get("status") == "ok")
    err = len(results) - ok
    return {
        "ok_count": ok,
        "error_count": err,
        "results": results,
    }


def chat_history(session_id: str, limit: int = 40) -> list[dict]:
    conn = get_connection()
    try:
        return load_chat_history(
            conn,
            session_id=session_id,
            limit=limit,
        )
    finally:
        conn.close()


def reset_chat(session_id: str) -> None:
    agent = _agents.get(session_id)
    if agent is not None:
        agent.reset(clear_db=True)
    else:
        conn = get_connection()
        try:
            clear_chat_history(conn, session_id=session_id)
        finally:
            conn.close()
