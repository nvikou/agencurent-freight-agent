"""Schémas Pydantic pour l'API AgenCurent."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default="default", max_length=64)


class ChatResponse(BaseModel):
    reply: str
    session_id: str


class QuoteOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    task_id: int
    departure: str
    destination: str
    carrier_code: str
    carrier_name: str
    transport_price: float | None
    delivery_days: int | None
    status: str
    source: str | None = None
    collected_at: str
    error_message: str | None = None


class CollectResponse(BaseModel):
    ok_count: int
    error_count: int
    results: list[dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
