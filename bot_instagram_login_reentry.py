import uiautomator2 as u2
import time
import sys
import os
from ig_helpers import connect_adb

# CONFIG DATA AKUN YANG INGIN DI-LOGIN
# ========================================================
USER_AKUN     = sys.argv[1] if len(sys.argv) > 1 else "lukyytris13" 
PASSWORD_AKUN = sys.argv[2] if len(sys.argv) > 2 else "Bryant12345678"          
device_id     = sys.argv[3] if len(sys.argv) > 3 else "all"

d = connect_adb(device_id)

width, height = d.window_size()

# TAHAP 1: BUKA INSTAGRAM
# ========================================================
print("\n--- TAHAP 1: BUKA INSTAGRAM ---")
current_pkg = d.app_current().get('package', '')
if current_pkg != 'com.instagram.android':
    d.press("home")
    time.sleep(1.5)
    print("Membuka aplikasi Instagram...")
    d.app_start("com.instagram.android")
    time.sleep(6)
else:
    print("Instagram sudah terbuka.")
time.sleep(2)

# TAHAP 2: PROSES LOGIN ULANG (RE-ENTRY PROFILE CLICK)
# ========================================================
print("\n--- TAHAP 2: LOGIN ULANG DENGAN PROFIL TERSEDIA ---")

# 1. Bersihkan pop-up Google Smart Lock/Credential Manager di awal jika menghalangi
try:
    current_pkg = d.app_current().get('package', '')
    if "credentialmanager" in current_pkg or d(text="Batal").exists:
        print("Pop-up Google Credential terdeteksi menghalangi layar awal!")
        if d(text="Batal").exists:
            d(text="Batal").click()
        else:
            d.click(0.322, 0.873) 
        time.sleep(3)
except Exception:
    pass

# 2. Cari tombol 'Lanjut sebagai ...' atau 'Continue as ...' atau 'Lanjut'
username_clean = USER_AKUN.split('@')[0]
lanjut_btn = None

# Tunggu hingga salah satu tombol profil/lanjut muncul di layar (maksimal 10 detik)
print(" Menunggu tombol 'Lanjut' atau profil muncul di layar...")
for _ in range(10):
    found = False
    for regex in [
        fr"(?i).*(continue as|lanjut sebagai|log in as|masuk sebagai)\s+{username_clean}.*",
        fr"(?i).*{username_clean}.*",
        r"(?i)^(continue|lanjut|lanjutkan)$",
        r"(?i).*(continue|lanjut|masuk|log in).*"
    ]:
        for sel in [d(textMatches=regex), d(descriptionMatches=regex)]:
            if sel.exists:
                lanjut_btn = sel
                found = True
                break
        if found:
            break
    if found:
        break
    time.sleep(1)

if lanjut_btn:
    print(f" -> Mengklik tombol profil/lanjut: '{lanjut_btn.info.get('text') or lanjut_btn.info.get('contentDescription') or 'Lanjut'}'")
    try:
        lanjut_btn.click()
        time.sleep(2)
    except Exception as e:
        print(f"    -> Gagal klik standar: {e}")
        
    # Jika tombol masih eksis, berarti klik standar tidak memicu perpindahan halaman
    # Jika tombol masih eksis, berarti klik standar tidak memicu perpindahan halaman
    if lanjut_btn.exists:
        print("    [Info] Tombol Lanjut masih terdeteksi. Mencoba klik via koordinat bounds elemen...")
        try:
            bounds = lanjut_btn.info.get('bounds', {})
            if bounds:
                cx = (bounds['left'] + bounds['right']) // 2
                cy = (bounds['top'] + bounds['bottom']) // 2
                print(f"    -> Klik koordinat center bounds: ({cx}, {cy})")
                d.click(cx, cy)
                time.sleep(2)
        except Exception as e2:
            print(f"    -> Gagal klik bounds: {e2}")
            
    if lanjut_btn.exists:
        print("    -> Mencoba klik koordinat persentase presisi (0.745, 0.588)...")
        d.click(int(width * 0.745), int(height * 0.588))
        time.sleep(2)
else:
    print(" -> Tombol profil/lanjut tidak terdeteksi via teks, mencoba koordinat persentase presisi (0.745, 0.588)...")
    d.click(int(width * 0.745), int(height * 0.588))
time.sleep(4)

# 3. Input Password jika diminta
print(" Menunggu kolom input kata sandi muncul...")
d(className="android.widget.EditText").wait(timeout=5)
edit_texts = d(className="android.widget.EditText")
if edit_texts.exists:
    print(" Kolom Password terdeteksi. Mengisi password...")
    pw_field = edit_texts[0]
    pw_field.click()
    time.sleep(1)
    pw_field.set_text(PASSWORD_AKUN)
    time.sleep(2)
    
    # Klik tombol Masuk/Log In
    login_btn = None
    for selector in [
        d(resourceId="com.instagram.android:id/next_button"),
        d(resourceId="com.instagram.android:id/primary_button"),
        d(textMatches="(?i).*(log in|login|masuk).*"),
        d(className="android.widget.Button")
    ]:
        if selector.exists:
            login_btn = selector
            break
    if login_btn:
        login_btn.click()
    else:
        d.press("enter")
        
    print(" Menunggu proses otentikasi (8 detik)...")
    time.sleep(8)
else:
    print(" Tidak meminta password (langsung masuk via login cepat).")

# TAHAP 3: BERSIHKAN POP-UP PASCA-LOGIN (MICROPHONE, NOTIFIKASI, GOOGLE & LAINNYA)
# ========================================================
print("\n--- TAHAP 3: BERSIHKAN SEGALA POP-UP PASCA-LOGIN ---")

# 1. Cek Pop-up Google Smart Lock ("Simpan kata sandi ke Google?")
try:
    current_pkg = d.app_current().get('package', '')
    if "credentialmanager" in current_pkg or d(text="Batal").exists or d(text="Batal").exists:
        print(" [+] Pop-up Google Smart Lock/Save Password terdeteksi! Mengklik Batal...")
        if d(text="Batal").exists:
            d(text="Batal").click()
        else:
            d.click(0.322, 0.873)
        time.sleep(2)
except Exception:
    pass

# 2. Cek Izin Mikrofon & Kamera Android (sistem permission)
for regex in [
    r"(?i).*(while using the app|saat aplikasinya digunakan|saat aplikasi digunakan).*",
    r"(?i).*(allow|izinkan).*",
    r"(?i).*(only this time|hanya kali ini).*"
]:
    for sel in [d(textMatches=regex), d(descriptionMatches=regex)]:
        if sel.exists:
            print(f" [+] Pop-up Izin Akses Sistem (Mikrofon/Kamera/Notifikasi) terdeteksi! Mengklik: '{regex}'")
            try:
                sel.click()
                time.sleep(2.5)
            except:
                pass

# 3. Panggil modul pembersih pop-up Instagram komprehensif
from bot_instagram_clear_popups import clear_post_login_popups
clear_post_login_popups(d)

print(" [SUKSES] Re-entry login dan pembersihan pop-up berhasil diselesaikan!")
sys.exit(0)
