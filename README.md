# Cek Status dan Tanggal Sertifikat Elektronik BSrE via Google Sheets

Repository ini berisi script Python untuk melakukan pengecekan massal status pengguna dan Sertifikat Elektronik BSrE berdasarkan **NIK** yang tersimpan pada Google Sheets.

Script dirancang untuk memproses **hanya row yang terlihat** pada Google Sheets. Row yang tersembunyi karena filter maupun disembunyikan manual tidak diproses.

Selain melakukan pengecekan ke API BSrE, script menggunakan mekanisme **differential update**: hanya cell pada kolom **O, P, Q, atau R yang benar-benar berubah** yang akan ditulis kembali ke Google Sheets.

---

## Fitur Utama

- Memproses hanya row yang terlihat pada Google Sheets.
- Mengabaikan row yang:
  - tersembunyi oleh filter (`hiddenByFilter`);
  - disembunyikan manual (`hiddenByUser`).
- Membaca NIK berdasarkan header `NIK`.
- Mengakses dua endpoint BSrE:
  - status pengguna/sertifikat;
  - profile sertifikat.
- Memilih sertifikat dengan tanggal berakhir terbaru.
- Menghitung tanggal terbit berdasarkan tanggal berakhir dikurangi 2 tahun.
- Membandingkan data baru dengan data yang sudah ada pada Google Sheets.
- Hanya meng-update cell yang benar-benar berubah.
- Menormalisasi format tanggal sebelum dibandingkan.
- Menggunakan batch update untuk mengurangi write request ke Google Sheets API.
- Menampilkan progress menggunakan `tqdm`.
- Membuat file log otomatis untuk setiap eksekusi.
- Menampilkan statistik jumlah row, perubahan per kolom, status sertifikat, profile/tanggal, error, dan NIK kosong.
- Menyediakan `test_koneksi.py` untuk menguji koneksi Google Sheets dan BSrE.

---

## Alur Kerja

```text
Google Sheets
    |
    |-- Ambil seluruh data
    |
    |-- Deteksi row terlihat
    |      |
    |      |-- hiddenByFilter = true  -> SKIP
    |      |-- hiddenByUser   = true  -> SKIP
    |      `-- visible row            -> PROSES
    |
    |-- Ambil NIK
    |
    |-- GET /api/user/status/{nik}
    |
    |-- GET /api/user/profile/{nik}
    |
    |-- Bandingkan hasil API dengan O/P/Q/R
    |      |
    |      |-- nilai sama     -> SKIP WRITE
    |      `-- nilai berbeda  -> UPDATE CELL
    |
    `-- Batch Update Google Sheets
```

---

## Kolom Google Sheets

| Kolom | Isi |
|---|---|
| C / header `NIK` | Nomor Induk Kependudukan |
| O | Status Pengguna |
| P | Status Sertifikat |
| Q | Tanggal terbit |
| R | Tanggal berakhir |

Posisi NIK dideteksi berdasarkan header `NIK`. Jika header tersebut tidak berada pada kolom C, script tetap menggunakan posisi header yang ditemukan dan menampilkan peringatan.

---

## Proses API BSrE

### 1. Status Pengguna dan Sertifikat

```http
GET /api/user/status/{nik}
```

Mapping status:

| Status API | Nilai Google Sheets |
|---|---|
| `ISSUE` | `Issued` |
| `REVOKE` | `Revoke` |
| `RENEW` | `Renew` |
| `NO_CERTIFICATE` | `New` |
| `EXPIRED` | `Expired` |

Untuk status yang dikenali, `Status Pengguna` diisi `Verified`.

Status `NOT_REGISTERED` tidak menyebabkan kolom O/P dihapus atau ditimpa.

### 2. Profile Sertifikat

```http
GET /api/user/profile/{nik}
```

Jika terdapat lebih dari satu sertifikat, script memilih sertifikat dengan nilai `berlaku_sampai` paling baru.

---

## Perhitungan Tanggal Sertifikat

Tanggal berakhir diambil dari field `berlaku_sampai`.

Tanggal terbit dihitung dengan:

```text
Tanggal Terbit = Tanggal Berakhir - 2 Tahun
```

Contoh:

```text
Tanggal berakhir : 12-08-2028
Tanggal terbit   : 12-08-2026
```

> Catatan: mekanisme ini mengikuti asumsi masa berlaku sertifikat selama dua tahun. Jika API BSrE menyediakan tanggal penerbitan secara eksplisit atau kebijakan masa berlaku berubah, logika tersebut sebaiknya disesuaikan.

---

## Differential Update

Script tidak menulis ulang seluruh kolom O:R pada setiap eksekusi. Sebelum melakukan update, hasil API dibandingkan dengan nilai yang sudah tersedia di spreadsheet.

Contoh:

```text
Data Google Sheets:
O125 = Verified
P125 = Issued
Q125 = 12-Agu-2024
R125 = 12-Agu-2026

Hasil API BSrE:
O125 = Verified
P125 = Expired
Q125 = 2024-08-12
R125 = 2026-08-12
```

Hasil:

```text
O -> sama      -> SKIP
P -> berbeda   -> UPDATE
Q -> sama      -> SKIP
R -> sama      -> SKIP
```

Sehingga hanya `P125` yang ditulis ulang.

Keuntungan:

- mengurangi write operation;
- mengurangi penggunaan quota Google Sheets API;
- menghindari rewrite data yang tidak perlu;
- statistik perubahan lebih akurat;
- lebih efisien untuk dataset besar.

---

## Normalisasi Tanggal

Tanggal dinormalisasi menjadi `YYYY-MM-DD` sebelum dibandingkan.

Format berikut dianggap sebagai tanggal yang sama:

```text
2026-08-12
12-08-2026
12/08/2026
12-Agu-2026
12-Aug-2026
12 Agustus 2026
12 August 2026
```

Dengan demikian, perbedaan format tampilan tidak menyebabkan update yang tidak diperlukan.

---

## Struktur Repository

```text
CekUser-BSrE/
|
|-- cek_nik_bsre_spreadseheet_merge.py
|-- test_koneksi.py
|-- README.md
|-- .gitignore
|-- .env
|-- google_credentials.json
`-- logs/
```

File sensitif seperti `.env`, `google_credentials.json`, dan file log sebaiknya tidak di-commit.

---

## Persyaratan Sistem

Direkomendasikan:

- Python 3.10+
- Windows, Linux, atau macOS
- akses internet ke Google API
- akses ke endpoint BSrE
- Google Service Account
- credential API BSrE yang valid

Virtual environment direkomendasikan, tetapi tidak wajib.

---

## Instalasi

### Clone Repository

```bash
git clone https://github.com/ajung5/CekUser-BSrE.git
cd CekUser-BSrE
```

### Opsional: Virtual Environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependency

```bash
pip install gspread requests python-dotenv tqdm google-auth google-api-python-client python-dateutil
```

Atau:

```powershell
python -m pip install gspread requests python-dotenv tqdm google-auth google-api-python-client python-dateutil
```

---

## Konfigurasi `.env`

Buat file `.env` pada root repository:

```env
# BSrE API
BSRE_BASE_URL=https://example-bsre-api
BSRE_USERNAME=your_username
BSRE_PASSWORD=your_password

# Google Sheets
GOOGLE_CREDENTIALS=google_credentials.json
SPREADSHEET_ID=your_google_spreadsheet_id
WORKSHEET_NAME=Nama Worksheet
```

Jangan menyimpan credential asli ke repository publik.

---

## Google Service Account

Simpan file credential Service Account pada root repository, misalnya:

```text
google_credentials.json
```

Pastikan `.env` berisi:

```env
GOOGLE_CREDENTIALS=google_credentials.json
```

Kemudian cari `client_email` pada file credential dan share Google Spreadsheet ke email tersebut dengan permission `Editor`.

---

## Test Koneksi

Repository menyediakan `test_koneksi.py`.

Windows:

```powershell
python test_koneksi.py
```

Linux/macOS:

```bash
python3 test_koneksi.py
```

Test ini memeriksa koneksi Google Spreadsheet, keberadaan worksheet, dan akses ke server/API BSrE.

---

## Menjalankan Script

Windows:

```powershell
python cek_nik_bsre_spreadseheet_merge.py
```

Dengan virtual environment tanpa aktivasi:

```powershell
.\venv\Scripts\python.exe .\cek_nik_bsre_spreadseheet_merge.py
```

Linux/macOS:

```bash
python3 cek_nik_bsre_spreadseheet_merge.py
```

---

## Cara Menggunakan Filter

Contoh:

```text
18.000 row total
        |
        |-- Filter OPD = Dinas Komunikasi dan Informatika
        |
        `-- 450 row terlihat
```

Ketika script dijalankan:

```text
450 row terlihat -> DIPROSES
17.550 row hidden -> TIDAK DIPROSES
```

Script membaca metadata `hiddenByFilter` dan `hiddenByUser`. Row dilewati jika salah satunya bernilai `true`.

---

## Logging

Setiap eksekusi script otomatis menghasilkan file log di:

```text
logs/
```

Format nama file:

```text
cekNIK_BSrE_YYYY-MM-DD_HHMMSS.log
```

Contoh:

```text
logs/cekNIK_BSrE_2026-09-11_182630.log
```

Output penting tampil di terminal dan disimpan ke file log. Progress bar `tqdm` tetap hanya tampil di terminal.

Contoh footer sukses:

```text
End Time   : 11-Sep-2026_18:42:12
Duration   : 00:15:42
BSRE Sync SUCCESS : 2026-09-11 18:42:12
============================================================
```

Jika error:

```text
BSRE Sync ERROR : 2026-09-11 18:42:12
============================================================
```

Jika dihentikan manual:

```text
BSRE Sync INTERRUPTED : 2026-09-11 18:42:12
============================================================
```

---

## Statistik Eksekusi

Contoh:

```text
======================================================================
 HASIL PENGECEKAN
======================================================================

Total row data            : 18399
Total row diproses        : 1250
Row terlihat              : 1250
Row hidden                : 17149
Total row berubah         : 24
Total row tanpa perubahan : 1226
Total cell berubah        : 31

--- PERUBAHAN CELL ---
Status Pengguna (O)       : 2
Status Sertifikat (P)     : 15
Tanggal terbit (Q)        : 6
Tanggal berakhir (R)      : 8

--- STATISTIK STATUS ---
ISSUE                     : 1080
EXPIRED                   : 32
REVOKE                    : 4
RENEW                     : 5
NO_CERTIFICATE            : 43
NOT_REGISTERED            : 82
Tidak diubah              : 4

--- STATISTIK PROFILE ---
Tanggal ditemukan         : 1121
Tidak ada sertifikat      : 43
NIK tidak ditemukan       : 82
Tanggal tidak valid       : 1
Profile tanpa data        : 3

--- DATA LAINNYA ---
NIK kosong                : 0
Error gabungan            : 0
```

---

## Update Header

Script memastikan:

```text
Q1 = Tanggal terbit
R1 = Tanggal berakhir
```

Header hanya ditulis jika nilainya berbeda.

---

## Troubleshooting

### Credential Google Tidak Ditemukan

Pastikan `google_credentials.json` tersedia dan `.env` berisi:

```env
GOOGLE_CREDENTIALS=google_credentials.json
```

### `SPREADSHEET_ID` Belum Diisi

```env
SPREADSHEET_ID=xxxxxxxxxxxxxxxx
```

ID diperoleh dari URL Google Sheets:

```text
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```

### `WORKSHEET_NAME` Belum Diisi

```env
WORKSHEET_NAME=Nama Worksheet
```

### Google API Error 403

Pastikan spreadsheet sudah dibagikan ke `client_email` Service Account dengan permission `Editor`.

### BSrE 401 Unauthorized

Periksa `BSRE_USERNAME` dan `BSRE_PASSWORD` pada `.env`.

### Header `NIK` Tidak Ditemukan

Worksheet harus memiliki header bernama `NIK`.

### Tidak Ada Cell yang Di-update

Ini tidak selalu berarti error. Jika hasil API sama dengan data existing, script memang tidak melakukan write.

---

## Security

Rekomendasi `.gitignore`:

```gitignore
# Environment / Secrets
.env
*.env

# Google Service Account
google_credentials.json
*credentials*.json

# Logs
logs/
*.log

# Python
venv/
.venv/
__pycache__/
*.py[cod]

# OS
.DS_Store
Thumbs.db
```

Jika credential pernah masuk ke Git history, menghapus file saja tidak cukup. Credential tersebut sebaiknya segera di-rotate atau di-revoke.

Jika `.DS_Store` sudah terlanjur tracked:

```bash
git rm --cached .DS_Store
```

---

## Ringkasan Mode Operasi

```text
Mode  : ROW TERLIHAT / HASIL FILTER
Write : HANYA CELL O/P/Q/R YANG BERUBAH
```

Dengan mekanisme ini, pengguna dapat menentukan subset data yang diperiksa langsung melalui filter Google Sheets tanpa mengubah source code.
