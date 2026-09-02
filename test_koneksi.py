import os
import gspread
from google.oauth2.service_account import Credentials
import requests
from dotenv import load_dotenv

# Memuat variabel dari file .env
load_dotenv()

# Mengambil konfigurasi eSign (BSRe) dari .env
BSRE_BASE_URL = os.getenv('BSRE_BASE_URL')
BSRE_USERNAME = os.getenv('BSRE_USERNAME')
BSRE_PASSWORD = os.getenv('BSRE_PASSWORD')

# Mengambil konfigurasi Google Sheets dari .env
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
WORKSHEET_NAME = os.getenv('WORKSHEET_NAME')


def cek_koneksi_google_sheets():
    print("--- Memeriksa Koneksi Google Spreadsheet API ---")
    try:
        if not GOOGLE_CREDENTIALS or not SPREADSHEET_ID:
            raise ValueError("GOOGLE_CREDENTIALS atau SPREADSHEET_ID belum lengkap di file .env")
            
        scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS, scopes=scopes)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        print(f"[SUKSES] Berhasil terhubung ke Google Spreadsheet.")
        print(f"         Nama Dokumen: '{spreadsheet.title}'")
        
        # Cek ketersediaan worksheet jika ditentukan
        if WORKSHEET_NAME:
            try:
                worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
                print(f"[SUKSES] Worksheet '{WORKSHEET_NAME}' ditemukan (Total baris: {worksheet.row_count}).\n")
            except gspread.exceptions.WorksheetNotFound:
                print(f"[PERINGATAN] Worksheet '{WORKSHEET_NAME}' tidak ditemukan di dalam spreadsheet.\n")
    except Exception as e:
        print(f"[GAGAL] Gagal terhubung ke Google Spreadsheet.")
        print(f"        Detail Error: {e}\n")


def cek_koneksi_bsre():
    print("--- Memeriksa Koneksi eSign Client API (BSRe) ---")
    try:
        if not BSRE_BASE_URL:
            raise ValueError("BSRE_BASE_URL belum diatur di file .env")
            
        # Biasanya autentikasi BSRe menggunakan Basic Auth atau form login (menyesuaikan endpoint standar)
        # Di sini kita contohkan menggunakan requests dengan Basic Auth berdasarkan username & password
        auth = (BSRE_USERNAME, BSRE_PASSWORD) if BSRE_USERNAME and BSRE_PASSWORD else None
        
        # Menguji koneksi ke base URL atau endpoint status/login (sesuaikan path endpoint BSRe Anda, misal /api/v1/status)
        endpoint = f"{BSRE_BASE_URL.rstrip('/')}"
        
        response = requests.get(endpoint, auth=auth, timeout=10)
        
        # Menerima status kode sukses atau redirect yang menandakan server aktif
        if response.status_code < 500:
            print(f"[SUKSES] Berhasil terhubung ke Server eSign (BSRe).")
            print(f"         Base URL    : {BSRE_BASE_URL}")
            print(f"         Status Code : {response.status_code}\n")
        else:
            print(f"[PERINGATAN] Server eSign merespons dengan error server.")
            print(f"            Status Code: {response.status_code}\n")
            
    except requests.exceptions.RequestException as e:
        print(f"[GAGAL] Gagal terhubung ke jaringan/server eSign BSRe.")
        print(f"        Detail Error: {e}\n")
    except ValueError as e:
        print(f"[GAGAL] Konfigurasi BSRe tidak lengkap.")
        print(f"        Detail Error: {e}\n")


if __name__ == "__main__":
    print("=== PROGRAM PENGECEKAN KONEKSI API BSRE & GOOGLE SHEETS ===\n")
    cek_koneksi_google_sheets()
    cek_koneksi_bsre()