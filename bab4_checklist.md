# Checklist BAB IV — Analisis Sentimen MBG (mengikuti struktur template BAB IV sistem pakar)

Pemetaan: struktur BAB IV contoh (sistem pakar rakit komputer) → apa yang perlu dibuat untuk project analisis sentimen MBG. Tanda ✅ = bahan sudah ada di project, ⚠️ = perlu dibuat baru.

---

## A. Definisi Masalah dan Penyelesaian

| Sub | Isi untuk project MBG | Status |
|---|---|---|
| 1. Definisi Masalah | Opini publik tentang MBG di X sangat banyak, analisis manual tidak efektif; belum diketahui dominasi sentimen & algoritma terbaik | ✅ tinggal tulis ulang dari BAB I |
| 2. Penyelesaian Masalah | Pipeline analisis sentimen otomatis: scraping → preprocessing → pelabelan lexicon → klasifikasi NB vs SVM | ✅ sudah terimplementasi |

## B. Pembahasan Algoritma

| Sub template | Padanan MBG | Yang perlu dibuat |
|---|---|---|
| 1. Metode Pengumpulan Data (observasi/wawancara/browsing) | **Scraping media sosial X** | ⚠️ Tabel: keyword ("Makan Bergizi Gratis", "MBG", "Program MBG"), periode pengambilan, jumlah tweet per keyword, total data. Ambil dari `view_db.py` |
| 2a. Data Kategori (tabel kode) | **Tahapan preprocessing** | ⚠️ Tabel contoh 1 tweet melewati tiap tahap: teks asli → case folding → hapus URL/mention → hapus stopword → stemming (ambil contoh nyata dari database) |
| 2b. Data Rakitan | **Pelabelan InSet Lexicon** | ⚠️ Tabel contoh perhitungan skor: kata per kata + bobotnya + total skor + label. Plus tabel distribusi hasil pelabelan (positif/negatif/netral) — ada di `evaluation_summary.txt` section 1a |
| 2c. Rule Based (IF-THEN) | **Rumus & cara kerja algoritma** | ⚠️ (1) Rumus TF-IDF + contoh perhitungan kecil; (2) rumus Naive Bayes (teorema Bayes) + contoh perhitungan manual 2-3 tweet; (3) konsep SVM (hyperplane, margin, kernel linear) + ilustrasi |
| 2d. Pohon Keputusan | **Flowchart pipeline** | ⚠️ Flowchart alur: scraping → preprocessing → labeling → split 80:20 → TF-IDF → training NB & SVM → evaluasi |
| 2e. Implementasi | **Hasil eksekusi program** | ✅ `results/`: tabel metrik, confusion matrix, comparison plot, evaluation_summary — tinggal ditempel + dianalisis |

## C. Pemodelan Perangkat Lunak

### 1. UML (semua perlu dibuat baru ⚠️)

| Diagram | Isi untuk project MBG |
|---|---|
| Use Case Diagram | Aktor: **Pengguna/Peneliti**. Use case (berbasis aplikasi web `webapp-php/`): Login, Impor Cookies X, Scraping Tweet, Preprocessing Teks, Pelabelan Otomatis, Latih Model NB & SVM, Melihat Hasil Evaluasi |
| Use Case Description | Satu tabel per use case (7 tabel), format sama seperti template (scenario, triggering event, actors, precondition, flow of activity) — trigger tombol di aplikasi web |
| Class Diagram | **Bisa dibuat akurat dari kode nyata**: `DBManager`, `BaseScraper` (abstract) ← `MockScraper`/`TwikitScraper`, `TextCleaner`, `LexiconLabeler`, `ClassifierPipeline` + atribut & method masing-masing (lihat `penjelasan_file.md`) |
| Activity Diagram | 4 diagram, satu per fase: scrape (dengan decision cookies valid/tidak, retry bot-check), preprocess, label, train |
| Sequence Diagram | 4 diagram: `main.py` → scraper → X.com → `DBManager`; main → `TextCleaner` → DB; main → `LexiconLabeler` → DB; main → `ClassifierPipeline` → results/ |
| Object Diagram | Contoh instance: satu objek tweet nyata dengan nilai atribut (raw_text, cleaned_text, score, label) |
| Deployment Diagram | Sederhana: Laptop peneliti (Python venv + SQLite + hasil) ↔ HTTPS ↔ Server X.com; + GitHub (unduh InSet Lexicon) |

### 2. Rancangan Layar (wireframe)
Aplikasi web sudah ada di `webapp-php/` — rancangan layar tinggal digambar versi sketsa/wireframe dari 5 layar yang sudah jadi (pakai draw.io/Figma/Balsamiq, gaya kotak-kotak seperti contoh):
- ⚠️ Rancangan Layar Login
- ⚠️ Rancangan Layar Dashboard (kartu statistik + donut chart)
- ⚠️ Rancangan Layar Scraping (form impor cookies + tombol proses + tabel)
- ⚠️ Rancangan Layar Preprocessing & Labeling (tabel before/after + word cloud)
- ⚠️ Rancangan Layar Hasil NB vs SVM (tabel metrik + grafik + confusion matrix)

### 3. Tampilan Layar (screenshot aplikasi web)
Jalankan `php -S localhost:8000 -t webapp-php`, isi data sampai cukup, lalu screenshot:
- ✅ Layar Login → Dashboard → Scraping → Preprocessing & Labeling → Hasil Model (5 gambar, aplikasi sudah jadi)
- ✅ Word cloud positif/negatif/netral + narasi otomatis (sudah tampil di halaman)
- Pendukung dari `results/`: `comparison_plot.png`, confusion matrix PNG, `evaluation_summary.txt`
- Opsional: screenshot terminal `view_db.py` sebagai bukti data (kolom `tweet_url` bisa diklik ke tweet asli)

> Deskripsi tiap use case web untuk tabel Use Case Scenario: Login, Impor Cookies, Scraping,
> Preprocessing, Pelabelan, Latih Model, Lihat Hasil Evaluasi — cocokkan dengan format Tabel 4.2-4.7 contoh.

## D. (Tambahan khas penelitian ML — tidak ada di template sistem pakar)
- ⚠️ Tabel hasil evaluasi lengkap (Accuracy, Precision, Recall, F1, AUC-ROC) + pembahasan per metrik — data dari `comparison_results.csv`
- ⚠️ Pembahasan confusion matrix per model (TP/TN/FP/FN) — data dari summary section 3
- ⚠️ Analisis perbandingan & jawaban rumusan masalah 1-4 — data dari summary section 5-6
- ⚠️ Keterbatasan penelitian (class imbalance, lexicon tidak paham negasi, jumlah data)

---

## Prioritas Pengerjaan
1. **Kumpulkan data dulu sampai cukup** (ratusan tweet) — semua tabel & screenshot hasil bergantung data final
2. Diagram UML (use case, class, activity, sequence) — paling banyak dikerjakan
3. Tabel contoh perhitungan (preprocessing, lexicon, TF-IDF, NB)
4. Screenshot semua mode + hasil akhir
5. Tulis narasi analisis dari `evaluation_summary.txt`
