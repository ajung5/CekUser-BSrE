import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

def run_test():
    print("==================================================")
    print("            TES KONEKSI API BSRE")
    print("==================================================")

    # 1. Load config
    load_dotenv()
    BASE_URL = os.getenv("BSRE_BASE_URL")
    USERNAME = os.getenv("BSRE_USERNAME")
    PASSWORD = os.getenv("BSRE_PASSWORD")

    # 2. Validasi Config
    if not BASE_URL or not USERNAME or not PASSWORD:
        print("❌ ERROR: Konfigurasi di file .env belum lengkap!")
        print(f" - BSRE_BASE_URL: {'Terisi' if BASE_URL else 'KOSONG'}")
        print(f" - BSRE_USERNAME: {'Terisi' if USERNAME else 'KOSONG'}")
        print(f" - BSRE_PASSWORD: {'Terisi' if PASSWORD else 'KOSONG'}")
        return

    print("✅ File .env berhasil dibaca.")
    print(f"🔗 Target URL: {BASE_URL}")
    print("-" * 50)

    # 3. Setup Session
    session = requests.Session()
    session.auth = HTTPBasicAuth(USERNAME, PASSWORD)
    session.headers.update({"Accept": "application/json"})

    # 4. Request Menggunakan NIK Dummy
    dummy_nik = "3213030201670001" 
    url_test = f"{BASE_URL}/api/user/status/{dummy_nik}"
    
    print(f"Mencoba ping ke endpoint: /api/user/status/{dummy_nik} ...\n")

    try:
        response = session.get(url_test, timeout=15)
        
        print(f"HTTP Status Code: {response.status_code}")
        print(f"Isi Response: {response.text}")
        print("-" * 50)

        if response.status_code == 200:
            print("✅ KONEKSI SUKSES: Auth valid dan NIK Dummy ternyata ditemukan.")
        elif response.status_code == 404:
            print("✅ KONEKSI SUKSES: Kredensial benar. (Mendapat 404 wajar karena NIK Dummy tidak terdaftar).")
        elif response.status_code == 401:
            print("❌ KONEKSI GAGAL (401): Unauthorized. Username atau Password di .env salah!")
        elif response.status_code == 403:
            print("❌ KONEKSI GAGAL (403): Forbidden. IP Anda mungkin belum di-whitelist oleh BSrE.")
        else:
            print(f"⚠️ KONEKSI ABNORMAL: Mendapat response HTTP {response.status_code}.")

    except requests.exceptions.ConnectionError:
        print("❌ KONEKSI GAGAL: Tidak dapat terhubung ke server (Connection Error).")
        print("   - Pastikan URL benar (HTTPS/HTTP).")
        print("   - Pastikan Anda terkoneksi ke jaringan/VPN yang diizinkan.")
    except requests.exceptions.Timeout:
        print("❌ KONEKSI GAGAL: Request Timeout (Server tidak merespons dalam 15 detik).")
    except Exception as e:
        print(f"❌ ERROR TIDAK TERDUGA: {str(e)}")

    print("==================================================")

if __name__ == "__main__":
    run_test()