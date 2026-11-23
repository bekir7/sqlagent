"""Örnek kanatlı hayvancılık ekipmanları ERP benzeri SQLite veritabanı oluşturur."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

from app.db import DB_PATH

SCHEMA = """
DROP TABLE IF EXISTS siparis_kalemleri;
DROP TABLE IF EXISTS siparisler;
DROP TABLE IF EXISTS stoklar;
DROP TABLE IF EXISTS uretim_emirleri;
DROP TABLE IF EXISTS uretim_hatlari;
DROP TABLE IF EXISTS urunler;
DROP TABLE IF EXISTS musteriler;

CREATE TABLE musteriler (
    musteri_id INTEGER PRIMARY KEY,
    firma_adi TEXT NOT NULL,
    ulke TEXT NOT NULL,
    segment TEXT NOT NULL,  -- Broiler / Yumurta / Parent Stock
    bolge TEXT NOT NULL
);

CREATE TABLE urunler (
    urun_id INTEGER PRIMARY KEY,
    urun_kodu TEXT NOT NULL UNIQUE,
    urun_adi TEXT NOT NULL,
    kategori TEXT NOT NULL,  -- Yemlik, Suluk, Havalandırma, Kafes, Konveyör
    birim TEXT NOT NULL,
    birim_fiyat REAL NOT NULL
);

CREATE TABLE uretim_hatlari (
    hat_id INTEGER PRIMARY KEY,
    hat_adi TEXT NOT NULL,
    lokasyon TEXT NOT NULL,
    kapasite_gunluk INTEGER NOT NULL,
    aktif INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE stoklar (
    stok_id INTEGER PRIMARY KEY,
    urun_id INTEGER NOT NULL REFERENCES urunler(urun_id),
    depo TEXT NOT NULL,
    miktar INTEGER NOT NULL,
    kritik_seviye INTEGER NOT NULL,
    son_sayim_tarihi TEXT NOT NULL
);

CREATE TABLE siparisler (
    siparis_id INTEGER PRIMARY KEY,
    musteri_id INTEGER NOT NULL REFERENCES musteriler(musteri_id),
    siparis_tarihi TEXT NOT NULL,
    teslim_tarihi TEXT,
    durum TEXT NOT NULL,  -- Açık / Üretimde / Sevk Edildi / İptal
    para_birimi TEXT NOT NULL DEFAULT 'EUR'
);

CREATE TABLE siparis_kalemleri (
    kalem_id INTEGER PRIMARY KEY,
    siparis_id INTEGER NOT NULL REFERENCES siparisler(siparis_id),
    urun_id INTEGER NOT NULL REFERENCES urunler(urun_id),
    miktar INTEGER NOT NULL,
    birim_fiyat REAL NOT NULL
);

CREATE TABLE uretim_emirleri (
    emir_id INTEGER PRIMARY KEY,
    urun_id INTEGER NOT NULL REFERENCES urunler(urun_id),
    hat_id INTEGER NOT NULL REFERENCES uretim_hatlari(hat_id),
    planlanan_miktar INTEGER NOT NULL,
    uretilen_miktar INTEGER NOT NULL DEFAULT 0,
    baslangic_tarihi TEXT NOT NULL,
    bitis_tarihi TEXT,
    durum TEXT NOT NULL  -- Planlandı / Devam / Tamamlandı / Durduruldu
);
"""


def _d(days_ago: int) -> str:
    return (date.today() - timedelta(days=days_ago)).isoformat()


def seed(db_path: Path | None = None) -> Path:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)

    musteriler = [
        (1, "Anadolu Broiler A.Ş.", "Türkiye", "Broiler", "Marmara"),
        (2, "Ege Yumurta Koop.", "Türkiye", "Yumurta", "Ege"),
        (3, "Gulf Poultry Systems", "BAE", "Broiler", "Ortadoğu"),
        (4, "Nile Parent Stock", "Mısır", "Parent Stock", "Afrika"),
        (5, "Balkan Eggs Ltd.", "Bulgaristan", "Yumurta", "Avrupa"),
        (6, "Anatolia Layer Farms", "Türkiye", "Yumurta", "İç Anadolu"),
        (7, "Desert Broiler Co.", "Suudi Arabistan", "Broiler", "Ortadoğu"),
        (8, "Caspian Poultry", "Azerbaycan", "Broiler", "Kafkasya"),
    ]
    conn.executemany(
        "INSERT INTO musteriler VALUES (?,?,?,?,?)", musteriler
    )

    urunler = [
        (1, "YEM-360", "360° Pan Yemlik Sistemi", "Yemlik", "adet", 185.0),
        (2, "SUL-NIP", "Nipel Suluk Hattı", "Suluk", "metre", 42.5),
        (3, "HAV-TUN", "Tünel Havalandırma Fanı", "Havalandırma", "adet", 920.0),
        (4, "KAF-LAYER", "Katlı Yumurta Kafes Sistemi", "Kafes", "modül", 2450.0),
        (5, "KON-YUM", "Yumurta Toplama Konveyörü", "Konveyör", "metre", 78.0),
        (6, "YEM-ZINC", "Zincirli Yem Dağıtım Ünitesi", "Yemlik", "adet", 310.0),
        (7, "HAV-PAD", "Soğutma Pad Sistemi", "Havalandırma", "m2", 55.0),
        (8, "SUL-TANK", "Basınç Regülasyon Tankı", "Suluk", "adet", 140.0),
        (9, "KAF-BROIL", "Broiler Zemin Ekipman Seti", "Kafes", "set", 1680.0),
        (10, "KON-GUB", "Gübre Bant Konveyörü", "Konveyör", "metre", 95.0),
    ]
    conn.executemany(
        "INSERT INTO urunler VALUES (?,?,?,?,?,?)", urunler
    )

    hatlar = [
        (1, "Yemlik Montaj Hattı A", "Bursa", 120, 1),
        (2, "Suluk Montaj Hattı B", "Bursa", 200, 1),
        (3, "Havalandırma Üretim Hattı", "Tekirdağ", 40, 1),
        (4, "Kafes Kaynak Hattı", "Bursa", 25, 1),
        (5, "Konveyör Montaj Hattı", "Tekirdağ", 80, 1),
    ]
    conn.executemany(
        "INSERT INTO uretim_hatlari VALUES (?,?,?,?,?)", hatlar
    )

    # Stok: bazıları kritik seviyenin altında
    stoklar = [
        (1, 1, "Merkez Depo", 45, 50, _d(3)),      # kritik altı
        (2, 2, "Merkez Depo", 820, 300, _d(3)),
        (3, 3, "Merkez Depo", 12, 20, _d(2)),      # kritik altı
        (4, 4, "Merkez Depo", 8, 5, _d(5)),
        (5, 5, "Merkez Depo", 150, 100, _d(1)),
        (6, 6, "Yedek Parça Depo", 18, 25, _d(4)),  # kritik altı
        (7, 7, "Merkez Depo", 420, 200, _d(1)),
        (8, 8, "Yedek Parça Depo", 9, 15, _d(6)),   # kritik altı
        (9, 9, "Merkez Depo", 22, 10, _d(2)),
        (10, 10, "Merkez Depo", 60, 80, _d(3)),     # kritik altı
        (11, 1, "Yedek Parça Depo", 30, 20, _d(7)),
        (12, 3, "Yedek Parça Depo", 5, 8, _d(2)),   # kritik altı
    ]
    conn.executemany(
        "INSERT INTO stoklar VALUES (?,?,?,?,?,?)", stoklar
    )

    # Siparişler: son ~4 ay dağılımı
    siparisler = [
        (1, 1, _d(95), _d(70), "Sevk Edildi", "EUR"),
        (2, 3, _d(88), _d(60), "Sevk Edildi", "EUR"),
        (3, 2, _d(75), _d(50), "Sevk Edildi", "EUR"),
        (4, 5, _d(62), _d(40), "Sevk Edildi", "EUR"),
        (5, 7, _d(48), _d(25), "Sevk Edildi", "EUR"),
        (6, 4, _d(40), _d(15), "Sevk Edildi", "USD"),
        (7, 1, _d(35), _d(10), "Sevk Edildi", "EUR"),
        (8, 6, _d(28), None, "Üretimde", "EUR"),
        (9, 3, _d(22), None, "Üretimde", "EUR"),
        (10, 8, _d(18), None, "Açık", "EUR"),
        (11, 2, _d(12), None, "Açık", "EUR"),
        (12, 7, _d(8), None, "Açık", "EUR"),
        (13, 5, _d(5), None, "Açık", "EUR"),
        (14, 1, _d(2), None, "Açık", "EUR"),
        (15, 4, _d(110), _d(90), "Sevk Edildi", "USD"),
        (16, 6, _d(55), _d(30), "İptal", "EUR"),
    ]
    conn.executemany(
        "INSERT INTO siparisler VALUES (?,?,?,?,?,?)", siparisler
    )

    kalemler = [
        (1, 1, 1, 120, 185.0),
        (2, 1, 2, 400, 42.5),
        (3, 2, 3, 24, 920.0),
        (4, 2, 7, 300, 55.0),
        (5, 3, 4, 16, 2450.0),
        (6, 3, 5, 200, 78.0),
        (7, 4, 4, 10, 2450.0),
        (8, 4, 10, 150, 95.0),
        (9, 5, 9, 8, 1680.0),
        (10, 5, 3, 18, 920.0),
        (11, 6, 6, 40, 310.0),
        (12, 6, 8, 25, 140.0),
        (13, 7, 1, 200, 185.0),
        (14, 7, 2, 600, 42.5),
        (15, 8, 4, 12, 2450.0),
        (16, 8, 5, 180, 78.0),
        (17, 9, 3, 30, 920.0),
        (18, 9, 7, 250, 55.0),
        (19, 10, 1, 80, 185.0),
        (20, 10, 6, 20, 310.0),
        (21, 11, 2, 350, 42.5),
        (22, 11, 8, 15, 140.0),
        (23, 12, 9, 6, 1680.0),
        (24, 12, 3, 12, 920.0),
        (25, 13, 4, 8, 2450.0),
        (26, 13, 10, 100, 95.0),
        (27, 14, 1, 150, 185.0),
        (28, 14, 7, 180, 55.0),
        (29, 15, 9, 10, 1680.0),
        (30, 15, 3, 20, 920.0),
        (31, 16, 4, 5, 2450.0),  # iptal sipariş
    ]
    conn.executemany(
        "INSERT INTO siparis_kalemleri VALUES (?,?,?,?,?)", kalemler
    )

    emirler = [
        (1, 1, 1, 200, 200, _d(40), _d(32), "Tamamlandı"),
        (2, 3, 3, 40, 40, _d(35), _d(28), "Tamamlandı"),
        (3, 4, 4, 20, 18, _d(25), None, "Devam"),
        (4, 2, 2, 500, 320, _d(20), None, "Devam"),
        (5, 5, 5, 200, 90, _d(15), None, "Devam"),
        (6, 9, 4, 10, 0, _d(10), None, "Planlandı"),
        (7, 6, 1, 60, 45, _d(12), None, "Devam"),
        (8, 7, 3, 300, 300, _d(50), _d(42), "Tamamlandı"),
        (9, 10, 5, 120, 0, _d(5), None, "Planlandı"),
        (10, 3, 3, 25, 10, _d(8), None, "Durduruldu"),
    ]
    conn.executemany(
        "INSERT INTO uretim_emirleri VALUES (?,?,?,?,?,?,?,?)", emirler
    )

    conn.commit()
    conn.close()
    return path


if __name__ == "__main__":
    out = seed()
    print(f"Veritabanı oluşturuldu: {out}")
