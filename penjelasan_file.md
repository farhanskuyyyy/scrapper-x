# Penjelasan Proses & Tanggung Jawab Per File

Panduan singkat untuk memahami tugas setiap file dalam project — cukup baca file ini untuk bisa menjelaskan cara kerja program.

## Alur Besar Program

```
[1. SCRAPE]           [2. PREPROCESS]       [3. LABEL]             [4. TRAIN]
twikit_scraper.py --> text_cleaner.py  -->  lexicon_labeler.py --> classifier_pipeline.py
(ambil tweet dari X)  (bersihkan teks)      (label otomatis)       (latih & banding NB vs SVM)
        \                   |                    |                      /
         └──────────── db_manager.py — SQLite (data/database.sqlite) ──┘
                                   ↑
                    main.py (pengatur semua fase, via --mode)
```

Semua fase membaca/menulis ke satu database SQLite. Bisa dijalankan satu-satu (`--mode scrape`) atau semua sekaligus (`--mode run-all`).

---

## File Utama (root)

### `main.py` — Pengatur Utama (Orkestrator)
Pintu masuk program. Membaca argumen CLI (`--mode`, `--limit`, `--live`), memuat `config/settings.json`, lalu menjalankan fase yang diminta secara berurutan. Tidak berisi logika bisnis — semua kerja didelegasikan ke modul `src/`. Fase 2 & 3 hanya memproses baris yang belum diproses (cek kolom `NULL` di database), jadi aman dijalankan berulang.

### `view_db.py` — Pengintip Database
Alat bantu melihat isi database dari terminal: total tweet, distribusi sentimen, dan pratinjau data (bisa filter `--label negative`, `--limit 20`, `--only-replies`). Kolom `tweet_url` bisa dibuka di browser untuk membuktikan data asli.

### `setup_env.py` — Installer Otomatis
Menyiapkan project di komputer baru: buat `venv/`, upgrade pip, install semua `requirements.txt`, dan cek twikit (kalau rusak, fallback install twifork dari GitHub). Deteksi otomatis Windows vs Mac/Linux.

---

## Folder `src/` (Kode Inti)

### `src/database/db_manager.py` — Pengelola SQLite
Satu-satunya file yang menyentuh SQL; modul lain lewat class `DBManager`.
- Membuat tabel `tweets` otomatis kalau belum ada (database terhapus → schema dibuat ulang sendiri).
- **Anti-duplikat 2 lapis**: primary key `tweet_id` + unique index pada `raw_text` — tweet copy-paste buzzer hanya tersimpan sekali (`INSERT OR IGNORE`).
- Menyediakan query per fase: `get_raw_tweets()` (belum dibersihkan), `get_unlabeled_tweets()` (belum dilabel), `get_ml_dataset()` (data training; default tanpa kelas netral, mengikuti penelitian acuan).

### `src/scraper/base_scraper.py` — Kontrak Scraper
Class abstrak: semua scraper wajib punya `search_tweets(query, limit)` dengan format keluaran seragam. Karena itu `main.py` bisa gonta-ganti MockScraper ↔ TwikitScraper tanpa ubah kode.

### `src/scraper/twikit_scraper.py` — Scraper X Asli
Mengambil tweet sungguhan dari X memakai library `twikit`:
1. **Autentikasi**: coba `config/cookies.json` dulu (export dari browser); gagal → login username/password dari `credentials.json`. Catatan: pesan "Authentication successful via cookies" hanya berarti file terbaca, belum tentu sesi valid.
2. **Pencarian**: `search_tweet()` + pagination sampai limit, jeda 2 detik antar halaman (jaga rate limit).
3. **Retry anti bot-check**: X kadang menyajikan halaman bot-check → error `Couldn't get KEY_BYTE indices`. Solusi di kode: reset cache transaksi twikit + dedup cookie yang bentrok (`__cf_bm`), ulangi maksimal 5×.

Kenapa tidak pakai API resmi X? Berbayar dan tier gratisnya terlalu dibatasi untuk pengumpulan data penelitian.

### `src/scraper/mock_scraper.py` — Tweet Sintetis (Uji Coba)
Menghasilkan tweet buatan bertopik MBG dari template (±85% positif, 10% negatif, 5% netral) tanpa internet/login. Hanya untuk menguji pipeline saat pengembangan — bukan data penelitian.

### `src/preprocess/text_cleaner.py` — Pembersih Teks
Pipeline 3 tahap (urutan penting):
1. **`clean_text`** — huruf kecil semua (case folding), hapus URL/mention/hashtag/emoji/angka.
2. **`remove_stopwords`** — buang kata umum (Sastrawi) + slang Twitter ("yg", "bgt", "kalo") + kata kunci topik ("mbg", "makan bergizi gratis" — muncul di semua tweet, tidak membedakan sentimen).
3. **`stem_text`** — stemming Sastrawi: kata berimbuhan → kata dasar ("kekhawatiran" → "khawatir").

Contoh: `"Sangat setuju dgn program MBG! 👍 @jokowi"` → `"sangat tuju program"`. Sastrawi dipakai karena stemmer khusus bahasa Indonesia (imbuhan me-/di-/ke-an tidak bisa ditangani stemmer bahasa Inggris).

### `src/preprocess/lexicon_labeler.py` — Pelabel Sentimen Otomatis
Memberi label awal (ground truth) memakai kamus **InSet Lexicon** (kamus sentimen Indonesia: kata positif berbobot +1..+5, negatif −1..−5; diunduh otomatis dari GitHub saat pertama jalan).
Proses: jumlahkan bobot semua kata tweet yang ada di kamus → total > 0 = `positive`, < 0 = `negative`, = 0 = `neutral`.
Keterbatasan (wajar disebut di laporan): tidak paham konteks/negasi — "tidak bagus" bisa terhitung positif dari kata "bagus".

### `src/models/classifier_pipeline.py` — Training & Evaluasi (Inti Penelitian)
Alur `run_training_pipeline()`:
1. Ambil dataset positive/negative saja (netral dikecualikan, ikut metodologi acuan).
2. Split 80:20 **stratified** (proporsi kelas terjaga) dengan `random_state=42` (hasil reprodusibel).
3. **TF-IDF** unigram+bigram, maksimal 5000 fitur — fit hanya di data latih (cegah data leakage).
4. Latih **Multinomial Naive Bayes** dan **SVM linear**, hitung Accuracy/Precision/Recall/F1/AUC-ROC.
5. Ekspor: confusion matrix PNG per model, `comparison_results.csv`, `comparison_plot.png`.
6. Prediksi seluruh dataset dengan kedua model → kesimpulan sentimen publik terhadap MBG.
7. Tulis laporan `results/evaluation_summary.txt` — section 1a & 6 menjawab tujuan 1 (kecenderungan sentimen), section 3 menjawab tujuan 2 & 3 (penerapan NB & SVM), section 5 menjawab tujuan 4 (algoritma paling efektif).

Catatan: kalau Precision/Recall/F1 = 0, artinya data terlalu sedikit/timpang sehingga model menebak semua data uji sebagai negatif (True Positive = 0) — solusinya tambah data, bukan bug.

---

## Folder Pendukung

| Folder/File | Isi |
|---|---|
| `config/settings.json` | Keyword pencarian, path database, rasio split, jumlah fitur TF-IDF |
| `config/cookies.json` | Sesi login X hasil export browser (dipakai scraper) |
| `config/credentials.json` | Username/password X (fallback kalau cookies gagal) |
| `data/database.sqlite` | Seluruh tweet + hasil tiap fase (dibuat otomatis) |
| `data/positive.tsv`, `negative.tsv` | Kamus InSet Lexicon (diunduh otomatis) |
| `results/` | Semua output evaluasi: CSV, grafik, confusion matrix, laporan teks |
| `requirements.txt` | Daftar library Python (Sastrawi, scikit-learn, twikit, dll.) |
| `debug_twikit.py` | Alat diagnosa kalau scraper error (cek versi, koneksi, langkah gagal) |
