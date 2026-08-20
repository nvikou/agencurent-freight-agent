"""API FastAPI — AgenCurent (нейро-аналитик конкурентов)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import services
from app.schemas import (
    ChatRequest,
    ChatResponse,
    CollectResponse,
    HealthResponse,
    QuoteOut,
)
from db.connection import default_db_path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("agencurent")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    load_dotenv()
    services.ensure_database()
    logger.info("DB ready: %s", default_db_path())
    yield


app = FastAPI(
    title="AgenCurent API",
    description=(
        "Нейро-аналитик конкурентов: Dellin vs ПЭК vs Baikal "
        "(только транспорт базы, тариф Стандарт)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="agencurent-backend",
        database=str(default_db_path()),
    )


@app.post("/api/chat", response_model=ChatResponse)
def post_chat(body: ChatRequest) -> ChatResponse:
    try:
        reply = services.chat(body.session_id, body.message.strip())
    except KeyError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration manquante: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("chat failed")
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
    return ChatResponse(reply=reply, session_id=body.session_id)


@app.get("/api/chat/history")
def get_history(
    session_id: str = Query(default="default"),
    limit: int = Query(default=40, ge=1, le=200),
) -> list[dict]:
    return services.chat_history(session_id, limit=limit)


@app.delete("/api/chat/history")
def delete_history(
    session_id: str = Query(default="default"),
) -> dict[str, str]:
    services.reset_chat(session_id)
    return {"status": "cleared", "session_id": session_id}


@app.get("/api/quotes", response_model=list[QuoteOut])
def get_quotes(
    latest_only: bool = Query(default=True),
) -> list[QuoteOut]:
    rows = services.list_quotes(latest_only=latest_only)
    return [QuoteOut(**row) for row in rows]


@app.post("/api/collect", response_model=CollectResponse)
def post_collect() -> CollectResponse:
    try:
        data = services.run_collect()
    except Exception as exc:
        logger.exception("collect failed")
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
    return CollectResponse(**data)
