"""Streamlit arayüzü — SQL Yönetim Raporlama Agent'ı."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# `streamlit run app/streamlit_app.py` için proje kökünü path'e ekle
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent import ask
from app.db import DB_PATH, get_connection, get_schema_ddl
from app.seed_db import seed

st.set_page_config(
    page_title="Tavsan Demo · Yönetim Raporlama Agent",
    page_icon="📊",
    layout="wide",
)

EXAMPLE_QUESTIONS = [
    "Geçen ay en çok hangi ekipman satıldı?",
    "Kritik stok seviyesinin altında hangi parçalar var?",
    "Bu çeyrekte hangi müşteri en yüksek ciro getirdi?",
    "Hangi üretim hattında devam eden emirler var ve tamamlanma oranları nedir?",
    "Sevk edilmemiş açık siparişlerin toplam tutarı nedir?",
    "Kategori bazında son 90 günde satış adetlerini göster.",
]


def ensure_db() -> None:
    if not DB_PATH.exists():
        seed()


def sidebar_meta() -> None:
    st.sidebar.title("Yönetim Agent")
    st.sidebar.caption(
        "Doğal dil → SQL → özet\nKanatlı ekipman ERP demosu"
    )
    ensure_db()
    st.sidebar.success(f"DB hazır: `{DB_PATH.name}`")

    with st.sidebar.expander("Veritabanı şeması"):
        conn = get_connection()
        try:
            st.code(get_schema_ddl(conn), language="sql")
        finally:
            conn.close()

    if st.sidebar.button("Veritabanını yeniden oluştur", use_container_width=True):
        seed()
        st.sidebar.success("Seed tamamlandı.")
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Örnek sorular**")
    for q in EXAMPLE_QUESTIONS:
        if st.sidebar.button(q, key=f"ex_{hash(q)}", use_container_width=True):
            st.session_state["pending_question"] = q


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_message(role: str, payload: dict) -> None:
    with st.chat_message(role):
        if role == "user":
            st.markdown(payload["content"])
            return

        if payload.get("error"):
            st.error(payload["error"])
            if payload.get("sql"):
                st.markdown("**Üretilen SQL** (çalıştırılamadı)")
                st.code(payload["sql"], language="sql")
            return

        st.markdown(payload.get("summary", ""))
        if payload.get("sql"):
            with st.expander("Çalıştırılan SQL", expanded=False):
                st.code(payload["sql"], language="sql")
        df = payload.get("dataframe")
        if isinstance(df, pd.DataFrame) and not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        elif isinstance(df, pd.DataFrame):
            st.info("Sorgu sonuç döndürmedi.")


def handle_question(question: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.spinner("SQL üretiliyor, sorgu çalıştırılıyor ve özetleniyor..."):
        result = ask(question)
    st.session_state.messages.append(
        {
            "role": "assistant",
            "summary": result.summary,
            "sql": result.sql,
            "dataframe": result.dataframe,
            "error": result.error,
        }
    )


def main() -> None:
    init_state()
    sidebar_meta()

    st.title("SQL ile Konuşan Yönetim Raporlama Agent'ı")
    st.markdown(
        "Üretim, satış ve stok verilerine doğal dilde sorun. "
        "Agent sorguyu SQL'e çevirir, çalıştırır ve yönetici özeti üretir."
    )

    for msg in st.session_state.messages:
        render_message(msg["role"], msg)

    pending = st.session_state.pop("pending_question", None)
    typed = st.chat_input("Örn: Geçen ay en çok hangi ekipman satıldı ve kritik stokta ne var?")
    question = pending or typed
    if question:
        handle_question(question.strip())
        st.rerun()


if __name__ == "__main__":
    main()
