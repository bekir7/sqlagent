# SQL ile Konuşan Yönetim Raporlama Agent'ı

Türkçe doğal dil sorularını SQL sorgusuna çeviren, örnek bir üretim/satış veritabanında çalıştıran ve sonucu yönetici dilinde özetleyen **Python + LLM** demosu.

Kanatlı hayvancılık ekipmanları (yemlik, suluk, havalandırma, kafes, konveyör) senaryosuyla hazırlanmıştır. Amaç: ERP / SQL verisine dayalı **yapay zekâ destekli yönetim raporlama** yeteneğini göstermek.

---

## Ne iş yapar?

Yönetici SQL bilmeden soru sorar; agent cevabı üretir.

| Adım | Ne olur? |
|------|----------|
| 1 | Türkçe soruyu alırsın |
| 2 | LLM, veritabanı şemasına bakarak **yalnızca SELECT** SQL üretir |
| 3 | Sorgu SQLite üzerinde çalışır |
| 4 | Sonuç **tablo** + kısa **yönetim özeti** olarak gösterilir |

### Örnek sorular

- Geçen ay en çok hangi ekipman satıldı?
- Kritik stok seviyesinin altında hangi parçalar var?
- Bu çeyrekte hangi müşteri en yüksek ciro getirdi?
- Hangi üretim hattında devam eden emirler var?
- Sevk edilmemiş açık siparişlerin toplam tutarı nedir?

### Ne yapmaz?

- Gerçek CANIAS ERP’ye bağlı değildir (demo SQLite kullanır).
- Sıfırdan AI modeli eğitmez; mevcut LLM API (ChatGPT vb.) kullanır.
- Veriyi silmez / güncellemez; sadece okur.

---

## Proje yapısı

```
sqlagent/
├── README.md
├── requirements.txt
├── .env.example          ← şablon (Git'e gider)
├── .env                  ← sen oluşturursun (API key buraya; Git'e gitmez)
├── data/
│   └── tavsan_demo.db    ← seed sonrası oluşur
└── app/
    ├── seed_db.py        ← örnek ERP verisini oluşturur
    ├── db.py             ← bağlantı, şema, güvenli sorgu
    ├── prompts.py        ← LLM sistem promptları
    ├── agent.py          ← NL → SQL → özet pipeline
    ├── streamlit_app.py  ← web arayüzü
    └── cli.py            ← komut satırı kullanımı
```

### Veritabanı tabloları

| Tablo | İçerik |
|-------|--------|
| `musteriler` | Firma, ülke, segment, bölge |
| `urunler` | Ekipman kodu, kategori, birim fiyat |
| `siparisler` / `siparis_kalemleri` | Siparişler ve kalemler |
| `stoklar` | Depo miktarı + kritik seviye |
| `uretim_hatlari` / `uretim_emirleri` | Hat kapasitesi ve üretim emirleri |

---

## Gereksinimler

- **Python 3.10+** (tercihen 3.11 / 3.12)
- **OpenAI API anahtarı** ([platform.openai.com](https://platform.openai.com/api-keys))  
  veya OpenAI uyumlu başka bir servis (ör. OpenRouter)

---

## Kurulum (Windows / PowerShell)

Proje klasörüne gir:

```powershell
cd c:\Users\user\Desktop\sqlagent
```

### 1) Sanal ortam oluştur ve aktifleştir

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Aktifleşince satır başında `(.venv)` görünür.

### 2) Bağımlılıkları kur

```powershell
pip install -r requirements.txt
```

### 3) API anahtarını ayarla (önemli)

Şablonu kopyala:

```powershell
copy .env.example .env
```

`.env` dosyasını Notepad veya Cursor ile aç:

```powershell
notepad .env
```

İçeriği şöyle olmalı:

```env
OPENAI_API_KEY=sk-buraya-kendi-anahtarin

OPENAI_BASE_URL=https://api.openai.com/v1

OPENAI_MODEL=gpt-4o-mini
```

| Değişken | Zorunlu mu? | Açıklama |
|----------|-------------|----------|
| `OPENAI_API_KEY` | **Evet** | OpenAI (veya uyumlu servis) API anahtarın |
| `OPENAI_BASE_URL` | Hayır | Varsayılan OpenAI. OpenRouter için: `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL` | Hayır | Varsayılan `gpt-4o-mini`. İstersen `gpt-4o` yaz |

**Dikkat**

- Anahtarı `sk-...` diye **tırnaksız** yaz.
- `.env` dosyasını GitHub’a **yükleme** (`.gitignore` içinde; yine de kontrol et).
- Anahtarı README, ekran görüntüsü veya chat’e yapıştırma.

### 4) Örnek veritabanını oluştur

```powershell
python -m app.seed_db
```

Başarılıysa benzer bir satır görürsün:

```text
Veritabanı oluşturuldu: ...\data\tavsan_demo.db
```

Veriyi sıfırdan yeniden üretmek için aynı komutu tekrar çalıştırman yeterli.

---

## Kullanım

### A) Web arayüzü (önerilen demo)

```powershell
streamlit run app/streamlit_app.py
```

Tarayıcıda genelde `http://localhost:8501` açılır.

- Soldaki **örnek sorulara** tıkla veya alttaki kutuya kendi sorunu yaz.
- Cevapta sırayla: **yönetim özeti**, **SQL** (expander), **sonuç tablosu** görünür.
- Sidebar’dan şemayı inceleyebilir veya “Veritabanını yeniden oluştur” ile seed’i yenileyebilirsin.

### B) Komut satırı

```powershell
python -m app.cli "Kritik stok seviyesinin altında hangi parçalar var?"
```

Çıktı bölümleri:

```text
=== SQL ===
... üretilen sorgu ...

=== SONUÇ ===
... tablo ...

=== ÖZET ===
... yönetici dili özet ...
```

---

## Çalışıyor mu? Hızlı kontrol listesi

| Test | Komut / beklenen |
|------|------------------|
| Ortam aktif | Satırda `(.venv)` |
| Seed | `python -m app.seed_db` → `tavsan_demo.db` oluşur |
| API key | `.env` içinde `OPENAI_API_KEY=sk-...` dolu |
| CLI | `python -m app.cli "Kritik stokta ne var?"` → SQL + tablo + özet |
| UI | `streamlit run app/streamlit_app.py` → tarayıcıda sohbet |

### Sık hatalar

| Hata | Çözüm |
|------|--------|
| `OPENAI_API_KEY bulunamadı` | `.env` yok veya boş; proje kökünde olduğundan emin ol |
| `Veritabanı bulunamadı` | `python -m app.seed_db` çalıştır |
| `Incorrect API key` | Anahtar yanlış / süresi dolmuş; OpenAI panelinden yenile |
| Modül bulunamadı | `.venv` aktif mi? `pip install -r requirements.txt` tekrar |
| Streamlit açılmıyor | Aynı terminalde `streamlit run app/streamlit_app.py` |

---

## Mimari (kısa)

```
Kullanıcı sorusu (TR)
        │
        ▼
  LLM: şema + soru → SQL (SELECT)
        │
        ▼
  Güvenlik kontrolü (yalnızca okuma)
        │
        ▼
  SQLite çalıştır → DataFrame
        │
        ▼
  LLM: sonuç → Türkçe yönetim özeti
        │
        ▼
  Streamlit / CLI çıktısı
```

### Güvenlik

Agent yalnızca `SELECT` / `WITH` kabul eder.  
`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER` vb. reddedilir.

Bu proje **demo** amaçlıdır. Gerçek ERP entegrasyonunda ek olarak yetkilendirme, sorgu whitelist ve audit log gerekir.

---

## Teknolojiler

- **Python** — uygulama dili  
- **SQLite** — örnek ERP verisi  
- **Streamlit** — sohbet arayüzü  
- **OpenAI API** — NL→SQL ve özetleme  
- **pandas** — sorgu sonuçları  

---

## Başvuru / GitHub için kısa açıklama

> Üretim ve satış verilerine doğal dilde soru sorulmasını sağlayan AI agent.  
> LLM ile SQL üretir, güvenli şekilde çalıştırır ve yönetici özeti oluşturur.  
> Python, SQLite, Streamlit ve OpenAI API kullanır.

---

## Lisans / not

Portföy / iş başvurusu demosu olarak hazırlanmıştır. Gerçek şirket verisi içermez.
