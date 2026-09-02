# Cek Status dan Tanggal Sertifikat TTE BSrE via Google Sheets

Repositori ini berisi skrip Python untuk melakukan pengecekan massal (bulk check) terhadap status dan masa berlaku Sertifikat Elektronik (TTE) dari Balai Sertifikasi Elektronik (BSrE) berdasarkan Nomor Induk Kependudukan (NIK). Skrip ini terintegrasi langsung dengan Google Sheets untuk membaca NIK dan menuliskan hasil pengecekan.

## 🏢 Proses Bisnis (Alur Kerja)

1. **Pembacaan Data Tersaring (Filtered Data):** Skrip terhubung ke Google Sheets menggunakan *Service Account*. Skrip dirancang untuk **hanya membaca baris yang terlihat (visible rows)**. Baris yang disembunyikan secara manual (hidden) atau tersaring oleh fitur *Filter* Google Sheets akan diabaikan.
2. **Pengambilan NIK:** Mengambil nilai NIK yang berada pada kolom C (atau berdasarkan header "NIK") pada sheet yang dikonfigurasi.
3. **Pengecekan Paralel ke API BSrE:**
   Untuk setiap NIK yang valid, skrip akan melakukan pemanggilan ke dua endpoint BSrE:
   * `GET /api/user/status/{nik}`: Untuk mengetahui status pengguna (Registered/Not Registered) dan status sertifikat (Issue, Revoke, Renew, Expired).
   * `GET /api/user/profile/{nik}`: Untuk mengambil data detail sertifikat, mencari tanggal kedaluwarsa (`berlaku_sampai`) terbaru, lalu mengkalkulasi tanggal terbit (tanggal berakhir dikurangi 2 tahun).
4. **Pembaruan Data Otomatis (Batch Update):** Hasil dari API akan dikumpulkan dan ditulis kembali secara massal (batch update) ke spreadsheet yang sama pada kolom berikut:
   * **Kolom O:** Status Pengguna (contoh: *Verified*)
   * **Kolom P:** Status Sertifikat (contoh: *Issued*, *Expired*, *Revoke*)
   * **Kolom Q:** Tanggal Terbit
   * **Kolom R:** Tanggal Berakhir

## ✨ Fitur Utama

* **Smart Row Detection:** Hanya memproses baris yang sedang aktif/terlihat di Google Sheets, menghemat *resource* API jika hanya ingin memproses data tertentu yang sedang difilter.
* **Otomatisasi Kalkulasi Tanggal:** Secara otomatis mencari sertifikat paling baru jika pengguna memiliki lebih dari satu sertifikat TTE, lalu menghitung tanggal terbit berdasarkan durasi standar 2 tahun.
* **Batch Update:** Penulisan ke Google Sheets tidak dilakukan satu per satu per baris, melainkan digabung (batch), sehingga menghindari *Rate Limit/Quota Limit* dari Google Sheets API.
* **Progress Bar:** Dilengkapi dengan `tqdm` untuk menampilkan indikator progres dan estimasi waktu selesai di terminal.

## 🛠️ Persyaratan Sistem (Prerequisites)

* Python 3.7 atau lebih baru.
* Kredensial *Service Account* Google Cloud Platform (`google_credentials.json`) yang memiliki akses ke Google Sheets dan Google Drive API.
* Akun/Kredensial API BSrE (Base URL, Username, dan Password).

### Instalasi Library
Jalankan perintah berikut untuk menginstal semua dependensi yang dibutuhkan:

```bash
pip install gspread requests python-dotenv tqdm google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-dateutil
```

## ⚙️ Konfigurasi Environment (.env)
Buat sebuah file bernama .env di direktori yang sama dengan skrip Python Anda, lalu isi dengan konfigurasi berikut:

```env
# ==========================================
# KREDENSIAL API BSRE
# ==========================================
BSRE_BASE_URL=https://url-api-bsre-anda.go.id
BSRE_USERNAME=username_api_anda
BSRE_PASSWORD=password_api_anda

# ==========================================
# KONFIGURASI GOOGLE SHEETS
# ==========================================
# Nama file json dari Service Account GCP
GOOGLE_CREDENTIALS=google_credentials.json

# ID Spreadsheet (Diambil dari URL Google Sheets)
SPREADSHEET_ID="Nama Id Spreadsheet Anda"

# Nama Worksheet / Tab di dalam Spreadsheet
WORKSHEET_NAME="Nama Sheet Anda"
```

Catatan: Pastikan Service Account email (contoh: nama-bot@project-id.iam.gserviceaccount.com) sudah diundang (Share/Bagikan) sebagai Editor ke file Google Sheets Anda.


## 🚀 Cara Menjalankan
Setelah semua konfigurasi selesai dan dependensi terinstal, jalankan perintah:

```bash
python3 nama_file_anda.py
```
