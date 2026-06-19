# Panduan Struktur Folder & Fungsi Berkas

Dokumen ini menjelaskan struktur direktori (folder) dan fungsi dari masing-masing berkas di dalam project **ta-scrapper-x** untuk mempermudah pemahaman kode program dan penulisan skripsi/laporan Tugas Akhir Anda.

---

## 1. Pohon Struktur Folder

```text
ta-scrapper-x/
├── config/
│   ├── settings.json         # Konfigurasi parameter umum project
│   ├── credentials.json      # Akun login X/Twitter (dibuat manual)
│   └── cookies.json          # Sesi login aktif dari browser (bypass Cloudflare)
├── data/
│   ├── database.sqlite       # Database lokal SQLite (otomatis dibuat)
│   ├── positive.tsv          # Kamus positif InSet Lexicon (otomatis diunduh)
│   └── negative.tsv          # Kamus negatif InSet Lexicon (otomatis diunduh)
├── results/
│   ├── comparison_results.csv# Tabel metrik performa model (Accuracy, F1, dll.)
│   ├── comparison_plot.png   # Grafik batang perbandingan Naive Bayes vs SVM
│   ├── nb_confusion_matrix.png# Confusion Matrix untuk model Naive Bayes
│   ├── svm_confusion_matrix.png# Confusion Matrix untuk model SVM
│   └── evaluation_summary.txt# Laporan analisis performa tekstual otomatis
├── src/
│   ├── database/
│   │   └── db_manager.py     # Pengelola koneksi, migrasi, dan kueri SQLite
│   ├── preprocess/
│   │   ├── text_cleaner.py   # Pembersih teks tweet & Stemming Sastrawi
│   │   └── lexicon_labeler.py# Pelabel sentimen otomatis menggunakan InSet Lexicon
│   ├── scraper/
│   │   ├── base_scraper.py   # Interface cetak biru scraper
│   │   ├── mock_scraper.py   # Generator tweet simulasi offline
│   │   └── twikit_scraper.py # Scraper X asli (real-time) via twifork
│   └── models/
│       └── classifier_pipeline.py # TF-IDF, pembagian dataset, NB/SVM training & evaluasi
├── main.py                   # Controller utama (CLI Orchestrator)
├── setup_env.py              # Script otomatisasi instalasi virtualenv & patch library
├── requirements.txt          # Daftar pustaka (dependencies) Python dasar
├── README.md                 # Panduan instalasi dan penggunaan program
└── structure_guide.md        # Panduan penjelasan struktur folder (File ini)
```

---

## 2. Penjelasan Fungsi Folder & Berkas

### A. Folder `config/`
Digunakan untuk menyimpan konfigurasi dan file otentikasi login:
*   **`settings.json`**: Menyimpan kata kunci pencarian (keywords), lokasi penyimpanan database, rasio pembagian data latih/uji (*test_split*), dan jumlah fitur maksimal TF-IDF.
*   **`credentials.json`**: Berkas rahasia berisi *username*, *email*, dan *password* Twitter Anda untuk proses masuk ke sistem scraping Twitter asli.
*   **`cookies.json`**: Menyimpan berkas *cookies* berformat JSON hasil ekspor dari browser Chrome/Firefox Anda untuk memintas pengamanan Cloudflare di X.com.

### B. Folder `data/`
Tempat penyimpanan database lokal dan berkas penunjang:
*   **`database.sqlite`**: File database SQLite tempat menyimpan seluruh tweet terunduh (beserta tautan URL aslinya), teks hasil pembersihan Sastrawi, skor sentimen, dan label akhirnya.
*   **`positive.tsv` & `negative.tsv`**: Kamus kata sentimen bahasa Indonesia (**InSet Lexicon**) berisi daftar ribuan kata beserta bobot polaritasnya (nilai $+1$ s.d $+5$ untuk positif, dan $-1$ s.d $-5$ untuk negatif).

### C. Folder `results/`
Folder keluaran (*output*) hasil evaluasi model Machine Learning:
*   **`comparison_results.csv`**: File data tabel berisi angka presisi, recall, akurasi, F1, dan AUC-ROC dari model Naive Bayes dan SVM untuk keperluan olah data grafik.
*   **`comparison_plot.png`**: Grafik visualisasi perbandingan metrik performa kedua model.
*   **`nb_confusion_matrix.png` & `svm_confusion_matrix.png`**: Gambar grafik *Confusion Matrix* yang memetakan tebakan benar (*True Positive/Negative*) dan tebakan salah (*False Positive/Negative*) dari masing-masing model.
*   **`evaluation_summary.txt`**: Laporan ringkas otomatis dalam format teks biasa yang menjelaskan cara membaca metrik klasifikasi dan menyimpulkan performa model Anda.

### D. Folder `src/` (Source Code)
Berisi seluruh logika pemrograman modular yang terbagi menjadi sub-modul:
1.  **`src/database/`**:
    *   **`db_manager.py`**: Mengurusi semua kueri SQL. Berkas ini bertanggung jawab membuat tabel database secara otomatis, menghapus data ganda buzzer/spam secara real-time, memperbarui teks bersih, dan mengambil data latih.
2.  **`src/preprocess/`**:
    *   **`text_cleaner.py`**: Melakukan pembersihan teks (*case folding*, pembersihan URL/mention/emoji) serta penyuntingan kata dasar bahasa Indonesia (*stemming*) dengan Sastrawi.
    *   **`lexicon_labeler.py`**: Melakukan unduhan berkas InSet Lexicon dari GitHub secara otomatis pada jalannya program pertama, lalu melakukan perhitungan skor sentimen dan pelabelan otomatis.
3.  **`src/scraper/`**:
    *   **`base_scraper.py`**: Menjadi standarisasi *interface* kode scraper.
    *   **`mock_scraper.py`**: Menghasilkan tweet simulasi offline bertopik MBG untuk pengujian pipeline program tanpa koneksi internet/login.
    *   **`twikit_scraper.py`**: Melakukan koneksi penambangan data tweet asli dari X.com secara *asynchronous* menggunakan metode otentikasi cookies.
4.  **`src/models/`**:
    *   **`classifier_pipeline.py`**: Membagi data secara *stratified*, melakukan transformasi teks numerik TF-IDF (N-gram 1,2), melatih model Naive Bayes & Linear SVM, serta mengekspor hasil ke folder `results/`.

### E. Berkas Utama di Direktori Root
*   **`main.py`**: Pengendali utama seluruh jalannya program. Menerima instruksi parameter argumen CLI seperti `--mode scrape`, `--mode preprocess`, `--mode label`, `--mode train`, atau `--mode run-all` (dan flag pendukung `--live` / `--limit`).
*   **`setup_env.py`**: Utilitas untuk membantu Anda memulai project di komputer lain secara instan dengan otomatisasi pembuatan lingkungan virtual dan *patching* library.
*   **`requirements.txt`**: Daftar pustaka dasar Python yang wajib terinstall.
*   **`README.md`**: Buku panduan utama yang berisi ringkasan, diagram arsitektur, dan instruksi lengkap penggunaan program.
