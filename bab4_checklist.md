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
| Use Case Diagram | Aktor tunggal: **Peneliti**. Use case: Scraping Tweet (include: Autentikasi X), Preprocessing Teks, Pelabelan Otomatis, Training & Evaluasi Model, Melihat Isi Database, Melihat Laporan Hasil |
| Use Case Description | Satu tabel per use case (6 tabel), format sama seperti template (scenario, triggering event, actors, precondition, flow of activity) — trigger-nya perintah CLI, bukan tombol |
| Class Diagram | **Bisa dibuat akurat dari kode nyata**: `DBManager`, `BaseScraper` (abstract) ← `MockScraper`/`TwikitScraper`, `TextCleaner`, `LexiconLabeler`, `ClassifierPipeline` + atribut & method masing-masing (lihat `penjelasan_file.md`) |
| Activity Diagram | 4 diagram, satu per fase: scrape (dengan decision cookies valid/tidak, retry bot-check), preprocess, label, train |
| Sequence Diagram | 4 diagram: `main.py` → scraper → X.com → `DBManager`; main → `TextCleaner` → DB; main → `LexiconLabeler` → DB; main → `ClassifierPipeline` → results/ |
| Object Diagram | Contoh instance: satu objek tweet nyata dengan nilai atribut (raw_text, cleaned_text, score, label) |
| Deployment Diagram | Sederhana: Laptop peneliti (Python venv + SQLite + hasil) ↔ HTTPS ↔ Server X.com; + GitHub (unduh InSet Lexicon) |

### 2. Rancangan Layar → **Rancangan Keluaran (adaptasi)**
Project ini CLI, tidak punya GUI. Ganti dengan:
- ⚠️ Rancangan keluaran terminal per mode (format output scraping/preprocess/label/train)
- ⚠️ Rancangan struktur laporan `evaluation_summary.txt` (6 section)
- ⚠️ Rancangan grafik (comparison plot, confusion matrix)

> Alternatif kalau dosen mewajibkan "layar": bisa ditambah dashboard web sederhana (misal Streamlit) untuk menampilkan hasil — perlu pengembangan baru.

### 3. Tampilan Layar → **Tampilan Keluaran Program (screenshot)**
- ⚠️ Screenshot terminal: `--mode scrape` (berhasil ambil tweet), `--mode preprocess`, `--mode label`, `--mode train` (tabel perbandingan)
- ⚠️ Screenshot `view_db.py` (distribusi sentimen + pratinjau data + bukti tweet_url)
- ✅ Gambar hasil: `comparison_plot.png`, `nb_confusion_matrix.png`, `svm_confusion_matrix.png`
- ✅ Isi `evaluation_summary.txt`

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
