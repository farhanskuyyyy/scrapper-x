<?php
// ============================================================
// api.php  (kompatibel PHP 7.4 ke atas)
//
// File ini adalah "jembatan" antara tampilan web (HTML/JavaScript)
// dengan database SQLite dan program Python.
//
// Ada 3 perintah (dipilih lewat parameter ?action= di URL):
//   1. ?action=data           -> mengambil semua data untuk ditampilkan
//   2. ?action=run&phase=...  -> menjalankan program Python (scrape/preprocess/label/train)
//   3. ?action=upload-cookies -> menyimpan file cookies X ke config/cookies.json
//
// Cara menjalankan (dari folder utama project):
//   php -S localhost:8000 -t webapp-php
// ============================================================

// ---------- PERSIAPAN ----------

// Lokasi folder utama project
$folder_project = dirname(__DIR__);

// Cek apakah komputer ini Windows atau Mac/Linux,
// karena lokasi python di dalam venv berbeda
if (stripos(PHP_OS, 'WIN') === 0) {
    $python = $folder_project . '\\venv\\Scripts\\python.exe';
} else {
    $python = $folder_project . '/venv/bin/python';
}

// Semua jawaban dari file ini berbentuk JSON
header('Content-Type: application/json; charset=utf-8');

// Fungsi bantu: kirim jawaban JSON lalu berhenti
function kirim_jawaban($kode_http, $data)
{
    http_response_code($kode_http);
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

// Ambil perintah dari URL, contoh: api.php?action=data
if (isset($_GET['action'])) {
    $action = $_GET['action'];
} else {
    $action = '';
}


// ============================================================
// PERINTAH 1: ?action=data
// Mengambil semua data dari database untuk ditampilkan di web
// ============================================================
if ($action == 'data') {

    // Buka koneksi database (menghasilkan variabel $koneksi)
    require 'koneksi.php';

    // ---------- 1a. Hitung jumlah tweet per label sentimen ----------
    $jumlah_positif = 0;
    $jumlah_negatif = 0;
    $jumlah_netral  = 0;

    $hasil = $koneksi->query("SELECT label, COUNT(*) AS jumlah FROM tweets WHERE label IS NOT NULL GROUP BY label");
    foreach ($hasil as $baris) {
        if ($baris['label'] == 'positive') {
            $jumlah_positif = (int) $baris['jumlah'];
        } elseif ($baris['label'] == 'negative') {
            $jumlah_negatif = (int) $baris['jumlah'];
        } elseif ($baris['label'] == 'neutral') {
            $jumlah_netral = (int) $baris['jumlah'];
        }
    }

    $total_berlabel = $jumlah_positif + $jumlah_negatif + $jumlah_netral;
    $total_semua    = (int) $koneksi->query("SELECT COUNT(*) FROM tweets")->fetchColumn();

    // Hitung persentase tiap label (dibulatkan 1 angka di belakang koma)
    if ($total_berlabel > 0) {
        $persen_positif = round($jumlah_positif / $total_berlabel * 100, 1);
        $persen_negatif = round($jumlah_negatif / $total_berlabel * 100, 1);
        $persen_netral  = round($jumlah_netral / $total_berlabel * 100, 1);
    } else {
        $persen_positif = 0;
        $persen_negatif = 0;
        $persen_netral  = 0;
    }

    $statistik = array(
        'total_tweets'  => $total_semua,
        'total_labeled' => $total_berlabel,
        'positive'      => $jumlah_positif,
        'negative'      => $jumlah_negatif,
        'neutral'       => $jumlah_netral,
        'positive_pct'  => $persen_positif,
        'negative_pct'  => $persen_negatif,
        'neutral_pct'   => $persen_netral,
    );

    // ---------- 1b. Word cloud: hitung kata terbanyak per label ----------
    $word_cloud = array();
    $daftar_label = array('positive', 'negative', 'neutral');

    foreach ($daftar_label as $label) {
        // Ambil semua teks bersih untuk label ini
        $query = $koneksi->prepare("SELECT cleaned_text FROM tweets WHERE label = ? AND cleaned_text IS NOT NULL");
        $query->execute(array($label));

        // Hitung frekuensi tiap kata
        $frekuensi_kata = array();
        foreach ($query->fetchAll(PDO::FETCH_COLUMN) as $teks) {
            $daftar_kata = preg_split('/\s+/', trim($teks));
            foreach ($daftar_kata as $kata) {
                // Hanya hitung kata dengan panjang minimal 3 huruf
                if (mb_strlen($kata) >= 3) {
                    if (isset($frekuensi_kata[$kata])) {
                        $frekuensi_kata[$kata] = $frekuensi_kata[$kata] + 1;
                    } else {
                        $frekuensi_kata[$kata] = 1;
                    }
                }
            }
        }

        // Urutkan dari frekuensi terbesar, ambil 30 kata teratas
        arsort($frekuensi_kata);
        $kata_teratas = array();
        $nomor = 0;
        foreach ($frekuensi_kata as $kata => $jumlah) {
            if ($nomor >= 30) {
                break;
            }
            $kata_teratas[] = array('term' => $kata, 'count' => $jumlah);
            $nomor = $nomor + 1;
        }
        $word_cloud[$label] = $kata_teratas;
    }

    // ---------- 1c. Status pipeline (untuk layar scraping & preprocessing) ----------

    // Baca kata kunci dari config/settings.json
    $kata_kunci = array('Makan Bergizi Gratis', 'MBG');
    $lokasi_settings = $folder_project . '/config/settings.json';
    if (file_exists($lokasi_settings)) {
        $isi_settings = json_decode(file_get_contents($lokasi_settings), true);
        if (isset($isi_settings['keywords'])) {
            $kata_kunci = $isi_settings['keywords'];
        }
    }

    // Jumlah tweet per kata kunci
    $per_kata_kunci = array();
    $hasil = $koneksi->query("SELECT keyword, COUNT(*) AS jumlah FROM tweets GROUP BY keyword ORDER BY jumlah DESC");
    foreach ($hasil as $baris) {
        $per_kata_kunci[$baris['keyword']] = (int) $baris['jumlah'];
    }

    $status_pipeline = array(
        'cookies_exists'     => file_exists($folder_project . '/config/cookies.json'),
        'keywords'           => $kata_kunci,
        'per_keyword'        => $per_kata_kunci,
        // Tweet yang belum dibersihkan (antrian preprocessing)
        'pending_preprocess' => (int) $koneksi->query("SELECT COUNT(*) FROM tweets WHERE cleaned_text IS NULL")->fetchColumn(),
        // Tweet bersih yang belum diberi label (antrian labeling)
        'pending_label'      => (int) $koneksi->query("SELECT COUNT(*) FROM tweets WHERE cleaned_text IS NOT NULL AND label IS NULL")->fetchColumn(),
    );

    // ---------- 1d. Daftar tweet untuk tabel ----------

    // 50 tweet mentah terbaru (untuk layar scraping)
    $tweet_mentah = $koneksi->query(
        "SELECT username, raw_text, keyword, created_at, tweet_url, tweet_id
         FROM tweets ORDER BY scraped_at DESC LIMIT 50"
    )->fetchAll(PDO::FETCH_ASSOC);

    // 50 tweet berlabel terbaru (untuk layar preprocessing)
    $tweet_berlabel = $koneksi->query(
        "SELECT username, raw_text, cleaned_text, sentiment_score, label, created_at, tweet_url, tweet_id
         FROM tweets WHERE label IS NOT NULL ORDER BY scraped_at DESC LIMIT 50"
    )->fetchAll(PDO::FETCH_ASSOC);

    // ---------- 1e. Hasil training NB & SVM ----------
    // File ini ditulis oleh Python (classifier_pipeline.py) setiap kali training
    $hasil_training = null;
    $lokasi_hasil = $folder_project . '/results/ml_results.json';
    if (file_exists($lokasi_hasil)) {
        $hasil_training = json_decode(file_get_contents($lokasi_hasil), true);
    }

    // ---------- 1f. Kirim semua data sebagai JSON ----------
    kirim_jawaban(200, array(
        'generated_at' => date('Y-m-d H:i:s'),
        'stats'        => $statistik,
        'wordclouds'   => $word_cloud,
        'pipeline'     => $status_pipeline,
        'raw_tweets'   => $tweet_mentah,
        'tweets'       => $tweet_berlabel,
        'ml'           => $hasil_training,
    ));
}


// ============================================================
// PERINTAH 2: ?action=run&phase=...
// Menjalankan program Python: main.py --mode <fase>
// ============================================================
if ($action == 'run') {

    // Daftar fase yang boleh dijalankan (selain ini ditolak)
    $fase_yang_diizinkan = array('scrape', 'preprocess', 'label', 'train');

    if (isset($_GET['phase'])) {
        $fase = $_GET['phase'];
    } else {
        $fase = '';
    }

    if (!in_array($fase, $fase_yang_diizinkan)) {
        kirim_jawaban(404, array('ok' => false, 'message' => 'Fase tidak dikenal.'));
    }

    // Pastikan python di dalam venv ada
    if (!file_exists($python)) {
        kirim_jawaban(500, array(
            'ok' => false,
            'message' => 'Python venv tidak ditemukan di ' . $python . '. Jalankan setup_env.py terlebih dahulu.',
        ));
    }

    // Ambil jumlah tweet per keyword dari body request (khusus fase scrape)
    $body = json_decode(file_get_contents('php://input'), true);
    $limit = 20;
    if (isset($body['limit'])) {
        $limit = (int) $body['limit'];
        // Batasi antara 1 sampai 200
        if ($limit < 1) {
            $limit = 1;
        }
        if ($limit > 200) {
            $limit = 200;
        }
    }

    // Scraping bisa memakan waktu lama, matikan batas waktu eksekusi PHP
    set_time_limit(0);

    // Pindah ke folder utama project supaya main.py menemukan config & database
    chdir($folder_project);

    // Susun perintah yang akan dijalankan
    // escapeshellarg() = pengaman agar path dengan spasi tidak merusak perintah
    $perintah = escapeshellarg($python) . ' main.py --mode ' . $fase;
    if ($fase == 'scrape') {
        $perintah = $perintah . ' --live --limit ' . $limit;
    }

    // Jalankan perintah, tangkap semua outputnya (2>&1 = ikutkan pesan error)
    $output = shell_exec($perintah . ' 2>&1');

    if ($output === null) {
        kirim_jawaban(500, array(
            'ok' => false,
            'message' => 'shell_exec gagal / dinonaktifkan pada konfigurasi PHP ini.',
        ));
    }

    // Jika di output ada "Traceback", berarti program Python error
    if (strpos($output, 'Traceback (most recent call last)') === false) {
        $berhasil = true;
    } else {
        $berhasil = false;
    }

    // Kirim potongan akhir output (maksimal 4000 karakter) untuk ditampilkan di web
    kirim_jawaban(200, array('ok' => $berhasil, 'log' => mb_substr($output, -4000)));
}


// ============================================================
// PERINTAH 3: ?action=upload-cookies
// Menyimpan file cookies X (JSON) ke config/cookies.json
// ============================================================
if ($action == 'upload-cookies') {

    // Baca isi file yang dikirim dari form web
    $isi_kiriman = file_get_contents('php://input');
    $cookies = json_decode($isi_kiriman, true);

    // Validasi: harus berupa JSON array/object dan tidak kosong
    if (!is_array($cookies) || count($cookies) == 0) {
        kirim_jawaban(400, array(
            'ok' => false,
            'message' => 'Gagal: format cookies tidak dikenali (harus JSON list export browser atau object).',
        ));
    }

    // Simpan ke config/cookies.json
    $lokasi_cookies = $folder_project . '/config/cookies.json';
    $berhasil_simpan = file_put_contents(
        $lokasi_cookies,
        json_encode($cookies, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)
    );

    if ($berhasil_simpan === false) {
        kirim_jawaban(500, array('ok' => false, 'message' => 'Gagal menulis config/cookies.json (cek permission).'));
    }

    kirim_jawaban(200, array('ok' => true, 'message' => 'cookies.json tersimpan (' . count($cookies) . ' entri).'));
}


// Jika action tidak dikenal
kirim_jawaban(404, array('ok' => false, 'message' => 'Endpoint tidak ditemukan.'));
