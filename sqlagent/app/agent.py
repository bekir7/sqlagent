"""Doğal dil → SQL → çalıştır → yönetim özeti agent'ı."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from app.db import get_connection, get_schema_ddl, run_query
from app.prompts import (
    SQL_SYSTEM,
    SUMMARY_SYSTEM,
    sql_user_message,
    summary_user_message,
)

load_dotenv()


@dataclass
class AgentResult:
    question: str
    sql: str
    dataframe: pd.DataFrame
    summary: str
    error: str | None = None


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY bulunamadı. .env dosyasını .env.example'dan kopyalayıp anahtar ekleyin."
        )
    kwargs: dict[str, Any] = {"api_key": api_key}
    base = os.getenv("OPENAI_BASE_URL")
    if base:
        kwargs["base_url"] = base
    return OpenAI(**kwargs)


def _model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _chat(system: str, user: str) -> str:
    client = _client()
    resp = client.chat.completions.create(
        model=_model(),
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return (resp.choices[0].message.content or "").strip()


def _extract_sql(text: str) -> str:
    """Markdown kod bloğu varsa içini al; yoksa metni temizle."""
    fence = re.search(r"```(?:sql)?\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    if fence:
        return fence.group(1).strip().rstrip(";")
    return text.strip().rstrip(";")


def generate_sql(question: str, schema: str) -> str:
    raw = _chat(
        SQL_SYSTEM.format(today=date.today().isoformat()),
        sql_user_message(question, schema),
    )
    return _extract_sql(raw)


def summarize(question: str, sql: str, df: pd.DataFrame) -> str:
    if df.empty:
        preview = "(sonuç boş — eşleşen kayıt yok)"
    else:
        preview = df.head(30).to_markdown(index=False)
    return _chat(SUMMARY_SYSTEM, summary_user_message(question, sql, preview))


def ask(question: str) -> AgentResult:
    """Soru → SQL → DataFrame → özet pipeline."""
    conn = get_connection()
    try:
        schema = get_schema_ddl(conn)
        sql = generate_sql(question, schema)
        try:
            df = run_query(conn, sql)
            summary = summarize(question, sql, df)
            return AgentResult(question=question, sql=sql, dataframe=df, summary=summary)
        except Exception as exc:  # noqa: BLE001 — UI'ye hatayı göster
            return AgentResult(
                question=question,
                sql=sql,
                dataframe=pd.DataFrame(),
                summary="",
                error=str(exc),
            )
    finally:
        conn.close()
