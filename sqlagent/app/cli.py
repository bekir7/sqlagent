"""Komut satırından tek soru sor: python -m app.cli \"Kritik stokta ne var?\""""

from __future__ import annotations

import sys

from app.agent import ask
from app.db import DB_PATH
from app.seed_db import seed


def main() -> None:
    if not DB_PATH.exists():
        seed()
    if len(sys.argv) < 2:
        print('Kullanım: python -m app.cli "Geçen ay en çok hangi ekipman satıldı?"')
        sys.exit(1)
    question = " ".join(sys.argv[1:])
    result = ask(question)
    print("\n=== SQL ===")
    print(result.sql)
    if result.error:
        print("\n=== HATA ===")
        print(result.error)
        sys.exit(2)
    print("\n=== SONUÇ ===")
    print(result.dataframe.to_string(index=False) if not result.dataframe.empty else "(boş)")
    print("\n=== ÖZET ===")
    print(result.summary)


if __name__ == "__main__":
    main()
