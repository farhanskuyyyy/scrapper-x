<?php
// ============================================================
// koneksi.php
// File ini bertugas membuat koneksi ke database SQLite.
// File lain tinggal memanggil: require 'koneksi.php';
// lalu memakai variabel $koneksi untuk query.
// ============================================================

// Lokasi folder utama project (satu tingkat di atas folder webapp-php)
$folder_project = dirname(__DIR__);

// Lokasi file database SQLite
$lokasi_database = $folder_project . '/data/database.sqlite';

// Membuat koneksi ke database menggunakan PDO
$koneksi = new PDO('sqlite:' . $lokasi_database);

// Jika ada error query, tampilkan sebagai Exception (agar mudah dilacak)
$koneksi->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

// Tunggu maksimal 10 detik jika database sedang dipakai proses Python
$koneksi->setAttribute(PDO::ATTR_TIMEOUT, 10);
