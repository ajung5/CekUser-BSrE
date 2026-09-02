import gspread
import requests
import time
import os

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from tqdm import tqdm
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


# ============================================================
# KONFIGURASI
# ============================================================

load_dotenv()


# ============================================================
# BSrE API
# ============================================================

BASE_URL = os.getenv("BSRE_BASE_URL")
USERNAME = os.getenv("BSRE_USERNAME")
PASSWORD = os.getenv("BSRE_PASSWORD")


# # ============================================================
# # GOOGLE SHEETS
# # ============================================================

# GOOGLE_CREDENTIALS = "google_credentials.json"

# SPREADSHEET_ID = "1LPavesE0NYbdrLZ-h5em1loc-b5foIHRWbGQ_1uP1nQ"


# # ============================================================
# # WORKSHEET
# # ============================================================

# WORKSHEET_NAME = "Data ASN Merge"

# ============================================================
# GOOGLE SHEETS & SPREADSHEET KONFIGURASI
# ============================================================

GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")


# ============================================================
# MAPPING STATUS API
# ============================================================

STATUS_MAPPING = {
    "ISSUE": "Issued",
    "REVOKE": "Revoke",
    "RENEW": "Renew",
    "NO_CERTIFICATE": "New",
    "EXPIRED": "Expired",
}


# ============================================================
# DELAY API
# ============================================================

REQUEST_DELAY = 0.1


# ============================================================
# KONEKSI GOOGLE
# ============================================================

def koneksi_google():

    if not os.path.exists(GOOGLE_CREDENTIALS):
        raise FileNotFoundError(
            "\nFile 'google_credentials.json' tidak ditemukan.\n"
            "Pastikan file berada di folder yang sama "
            "dengan script Python."
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS,
        scopes=scopes
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

    sheets_service = build(
        "sheets",
        "v4",
        credentials=credentials,
        cache_discovery=False
    )

    return client, spreadsheet, worksheet, sheets_service


# ============================================================
# MENDAPATKAN ROW YANG TERLIHAT
# ============================================================

def ambil_row_terlihat(sheets_service, worksheet):

    sheet_name = worksheet.title

    response = (
        sheets_service
        .spreadsheets()
        .get(
            spreadsheetId=SPREADSHEET_ID,
            ranges=sheet_name,
            fields=(
                "sheets("
                    "properties(sheetId,title),"
                    "data("
                        "startRow,"
                        "rowMetadata(hiddenByFilter,hiddenByUser)"
                    ")"
                ")"
            )
        )
        .execute()
    )

    sheets = response.get("sheets", [])

    if not sheets:
        raise Exception("Metadata worksheet tidak ditemukan.")

    sheet_data = sheets[0].get("data", [])

    if not sheet_data:
        return []

    grid_data = sheet_data[0]
    start_row = grid_data.get("startRow", 0)
    row_metadata = grid_data.get("rowMetadata", [])

    row_terlihat = []

    for index, metadata in enumerate(row_metadata):
        nomor_baris = start_row + index + 1

        hidden_by_filter = metadata.get("hiddenByFilter", False)
        hidden_by_user = metadata.get("hiddenByUser", False)

        if hidden_by_filter or hidden_by_user:
            continue

        row_terlihat.append(nomor_baris)

    return row_terlihat


# ============================================================
# CEK PROFILE BSrE (TANGGAL)
# ============================================================

def cek_profile_sertifikat(nik):

    if not BASE_URL or not USERNAME or not PASSWORD:
        return None

    url = f"{BASE_URL}/api/user/profile/{nik}"

    try:
        response = requests.get(url, auth=(USERNAME, PASSWORD), timeout=10)

        if response.status_code == 200:
            data = response.json()
            success = data.get("success", False)

            if not success:
                return {"status": "NO_DATA", "tanggal_terbit": "", "tanggal_berakhir": ""}

            profile_data = data.get("data", {})
            certificates = profile_data.get("sertifikat", [])

            if not certificates:
                return {"status": "NO_CERTIFICATE", "tanggal_terbit": "", "tanggal_berakhir": ""}

            daftar_sertifikat_valid = []

            for certificate in certificates:
                berlaku_sampai = certificate.get("berlaku_sampai", "")
                if not berlaku_sampai:
                    continue
                try:
                    tanggal_expired = datetime.strptime(berlaku_sampai, "%d-%m-%Y")
                    daftar_sertifikat_valid.append({"tanggal": tanggal_expired, "data": certificate})
                except ValueError:
                    continue

            if not daftar_sertifikat_valid:
                return {"status": "NO_CERTIFICATE_DATE", "tanggal_terbit": "", "tanggal_berakhir": ""}

            daftar_sertifikat_valid.sort(key=lambda x: x["tanggal"], reverse=True)
            certificate_terbaru = daftar_sertifikat_valid[0]
            tanggal_expired = certificate_terbaru["tanggal"]
            tanggal_issue = tanggal_expired - relativedelta(years=2)

            tanggal_terbit = tanggal_issue.strftime("%d-%m-%Y")
            tanggal_berakhir = tanggal_expired.strftime("%d-%m-%Y")

            return {
                "status": "SUCCESS",
                "tanggal_terbit": tanggal_terbit,
                "tanggal_berakhir": tanggal_berakhir
            }

        elif response.status_code == 401:
            print(f"\nUNAUTHORIZED - NIK {nik} (Profile)")
            return None

        elif response.status_code == 404:
            return {"status": "NOT_FOUND", "tanggal_terbit": "", "tanggal_berakhir": ""}

        else:
            print(f"\nHTTP ERROR {response.status_code} - NIK {nik} (Profile)")
            return None

    except Exception as e:
        print(f"\nERROR PROFILE - NIK {nik}: {e}")
        return None


# ============================================================
# CEK STATUS SERTIFIKAT BSrE
# ============================================================

def cek_status_sertifikat(nik):

    if not BASE_URL or not USERNAME or not PASSWORD:
        return None

    url = f"{BASE_URL}/api/user/status/{nik}"

    try:
        response = requests.get(url, auth=(USERNAME, PASSWORD), timeout=10)

        if response.status_code == 200:
            data = response.json()
            status_api = str(data.get("status", "")).strip().upper()

            if status_api == "NOT_REGISTERED":
                return {"update": False, "status_api": status_api, "status_pengguna": None, "status_sertifikat": None}

            if status_api in STATUS_MAPPING:
                return {
                    "update": True,
                    "status_api": status_api,
                    "status_pengguna": "Verified",
                    "status_sertifikat": STATUS_MAPPING[status_api]
                }

            return {"update": False, "status_api": status_api, "status_pengguna": None, "status_sertifikat": None}

        elif response.status_code == 401:
            print(f"\nUNAUTHORIZED - NIK {nik} (Status)")
            return None

        else:
            print(f"\nHTTP ERROR {response.status_code} - NIK {nik} (Status)")
            return None

    except Exception as e:
        print(f"\nERROR STATUS - NIK {nik}: {e}")
        return None


# ============================================================
# PROSES GOOGLE SHEETS
# ============================================================

def proses_google_sheet():

    print("\n" + "=" * 70)
    print(" CEK STATUS DAN TANGGAL SERTIFIKAT ELEKTRONIK BSrE")
    print("=" * 70 + "\n")

    if not SPREADSHEET_ID or SPREADSHEET_ID == "ISI_ID_GOOGLE_SPREADSHEET":
        raise ValueError("\nSPREADSHEET_ID belum diisi.")

    print("Menghubungkan ke Google Spreadsheet...")
    client, spreadsheet, worksheet, sheets_service = koneksi_google()
    print("Berhasil terhubung.\n")

    print("Mengambil data spreadsheet...")
    data = worksheet.get_all_values()

    if not data:
        print("Spreadsheet kosong.")
        return

    header = data[0]

    try:
        kolom_nik_index = header.index("NIK") + 1
    except ValueError:
        raise ValueError("\nKolom 'NIK' tidak ditemukan.")

    if kolom_nik_index != 3:
        print(f"\nPERINGATAN: Kolom NIK ditemukan di posisi {kolom_nik_index}, bukan kolom C.\n")

    print("Memastikan nama header kolom...")
    worksheet.update(
        range_name="Q1:R1",
        values=[["Tanggal terbit", "Tanggal berakhir"]]
    )

    print("Mendeteksi row yang terlihat...")
    row_terlihat = ambil_row_terlihat(sheets_service, worksheet)
    row_terlihat_data = [row for row in row_terlihat if row >= 2]

    total_row = len(data) - 1
    total_terlihat = len(row_terlihat_data)
    total_hidden = total_row - total_terlihat

    print(f"\nTotal row data       : {total_row}")
    print(f"Row terlihat         : {total_terlihat}")
    print(f"Row hidden           : {total_hidden}\n")
    print("Hanya row terlihat yang akan dicek. Row hidden TIDAK akan diproses.\n")

    update_cells = []

    # Statistik Profile
    jumlah_sukses = 0
    jumlah_tidak_ada_sertifikat = 0
    jumlah_tidak_ditemukan = 0
    jumlah_tanggal_tidak_valid = 0

    # Statistik Status
    jumlah_issue = 0
    jumlah_revoke = 0
    jumlah_renew = 0
    jumlah_no_certificate = 0
    jumlah_expired = 0
    jumlah_not_registered = 0
    jumlah_tidak_diubah = 0

    jumlah_nik_kosong = 0
    jumlah_error = 0

    for nomor_baris in tqdm(row_terlihat_data, total=len(row_terlihat_data), desc="Checking NIK"):

        if nomor_baris > len(data):
            continue

        row = data[nomor_baris - 1]

        if len(row) >= kolom_nik_index:
            nik = str(row[kolom_nik_index - 1]).strip()
        else:
            nik = ""

        if not nik or nik.lower() == "nan" or nik.lower() == "none":
            jumlah_nik_kosong += 1
            continue

        # ====================================================
        # REQUEST KEDUA API
        # ====================================================
        hasil_status = cek_status_sertifikat(nik)
        hasil_profile = cek_profile_sertifikat(nik)

        if hasil_status is None or hasil_profile is None:
            jumlah_error += 1
            time.sleep(REQUEST_DELAY)
            continue

        # ====================================================
        # UPDATE STATUS (KOLOM O & P)
        # ====================================================
        if hasil_status["update"]:
            update_cells.append({"range": f"O{nomor_baris}", "values": [[hasil_status["status_pengguna"]]]})
            update_cells.append({"range": f"P{nomor_baris}", "values": [[hasil_status["status_sertifikat"]]]})
            
            status_api = hasil_status["status_api"]
            if status_api == "ISSUE": jumlah_issue += 1
            elif status_api == "REVOKE": jumlah_revoke += 1
            elif status_api == "RENEW": jumlah_renew += 1
            elif status_api == "NO_CERTIFICATE": jumlah_no_certificate += 1
            elif status_api == "EXPIRED": jumlah_expired += 1
        else:
            if hasil_status.get("status_api") == "NOT_REGISTERED":
                jumlah_not_registered += 1
            else:
                jumlah_tidak_diubah += 1

        # ====================================================
        # UPDATE PROFILE TANGGAL (KOLOM Q & R)
        # ====================================================
        status_prof = hasil_profile.get("status", "")
        if status_prof == "SUCCESS":
            update_cells.append({"range": f"Q{nomor_baris}", "values": [[hasil_profile["tanggal_terbit"]]]})
            update_cells.append({"range": f"R{nomor_baris}", "values": [[hasil_profile["tanggal_berakhir"]]]})
            jumlah_sukses += 1
        elif status_prof == "NO_CERTIFICATE":
            jumlah_tidak_ada_sertifikat += 1
            update_cells.append({"range": f"Q{nomor_baris}", "values": [[""]]})
            update_cells.append({"range": f"R{nomor_baris}", "values": [[""]]})
        elif status_prof == "NOT_FOUND":
            jumlah_tidak_ditemukan += 1
            update_cells.append({"range": f"Q{nomor_baris}", "values": [[""]]})
            update_cells.append({"range": f"R{nomor_baris}", "values": [[""]]})
        elif status_prof == "NO_CERTIFICATE_DATE":
            jumlah_tanggal_tidak_valid += 1

        time.sleep(REQUEST_DELAY)

    # ========================================================
    # UPDATE GOOGLE SHEETS BATCH
    # ========================================================
    print("\nMengupdate Google Spreadsheet...\n")

    if update_cells:
        worksheet.batch_update(update_cells)
        # Dibagi 4 jika semua sel (O, P, Q, R) di-update, dll. Kita hitung saja jumlah blok operasi.
        print(f"Berhasil mengupdate {len(update_cells)} cell operations.")
    else:
        print("Tidak ada data yang perlu diupdate.")

    # ========================================================
    # HASIL AKHIR
    # ========================================================
    print("\n" + "=" * 70)
    print(" HASIL PENGECEKAN")
    print("=" * 70 + "\n")

    print(f"Row terlihat             : {total_terlihat}")
    print(f"Row hidden               : {total_hidden}\n")
    
    print("--- STATISTIK STATUS ---")
    print(f"ISSUE              : {jumlah_issue}")
    print(f"EXPIRED            : {jumlah_expired}")
    print(f"REVOKE             : {jumlah_revoke}")
    print(f"RENEW              : {jumlah_renew}")
    print(f"NO_CERTIFICATE     : {jumlah_no_certificate}")
    print(f"NOT_REGISTERED     : {jumlah_not_registered}")
    print(f"Tidak diubah       : {jumlah_tidak_diubah}\n")

    print("--- STATISTIK TANGGAL ---")
    print(f"Tanggal ditemukan        : {jumlah_sukses}")
    print(f"Tidak ada sertifikat     : {jumlah_tidak_ada_sertifikat}")
    print(f"NIK tidak ditemukan      : {jumlah_tidak_ditemukan}")
    print(f"Tanggal tidak valid      : {jumlah_tanggal_tidak_valid}\n")

    print(f"NIK kosong               : {jumlah_nik_kosong}")
    print(f"Error gabungan           : {jumlah_error}\n")

    print("Kolom O = Status Pengguna")
    print("Kolom P = Status Sertifikat")
    print("Kolom Q = Tanggal terbit")
    print("Kolom R = Tanggal berakhir\n")
    print("Row hidden tidak diproses.\n")


if __name__ == "__main__":
    try:
        proses_google_sheet()
    except KeyboardInterrupt:
        print("\nProses dihentikan oleh pengguna.")
    except Exception as e:
        print("\n" + "=" * 70)
        print("ERROR")
        print("=" * 70 + "\n")
        print(str(e))
        print()