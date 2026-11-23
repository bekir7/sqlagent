"""SQLite bağlantısı, şema okuma ve güvenli sorgu çalıştırma."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tavsan_demo.db"

FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|ATTACH|"
    r"DETACH|PRAGMA|VACUUM|REINDEX|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Veritabanı bulunamadı: {path}\nÖnce çalıştırın: python -m app.seed_db"
        )
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_schema_ddl(conn: sqlite3.Connection) -> str:
    """CREATE TABLE ifadelerini ve örnek satır sayılarını döndürür."""
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    parts: list[str] = []
    for (name,) in tables:
        ddl = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        ).fetchone()[0]
        count = conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        parts.append(f"{ddl};\n-- satır sayısı: {count}")
    return "\n\n".join(parts)


def validate_select_only(sql: str) -> None:
    cleaned = sql.strip().rstrip(";")
    if not cleaned:
        raise ValueError("Boş SQL sorgusu.")
    if FORBIDDEN_SQL.search(cleaned):
        raise ValueError(
            "Güvenlik: yalnızca okuma (SELECT / WITH) sorgularına izin verilir."
        )
    # Çoklu statement engeli
    if ";" in cleaned:
        raise ValueError("Tek bir SQL ifadesi gönderilmelidir.")
    first = cleaned.lstrip().split(None, 1)[0].upper()
    if first not in {"SELECT", "WITH"}:
        raise ValueError("Sorgu SELECT veya WITH ile başlamalıdır.")


def run_query(conn: sqlite3.Connection, sql: str, limit: int = 200) -> pd.DataFrame:
    validate_select_only(sql)
    # LIMIT yoksa ekle (büyük sonuç riskini azalt)
    upper = sql.upper()
    if "LIMIT" not in upper:
        sql = f"{sql.rstrip().rstrip(';')} LIMIT {limit}"
    return pd.read_sql_query(sql, conn)


def sample_rows(conn: sqlite3.Connection, table: str, n: int = 3) -> list[dict[str, Any]]:
    df = pd.read_sql_query(f'SELECT * FROM "{table}" LIMIT {n}', conn)
    return df.to_dict(orient="records")
