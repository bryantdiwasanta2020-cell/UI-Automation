import uiautomator2 as u2
import time
import sys
import os
import subprocess
from ig_helpers import connect_adb

# CONFIG DATA AKUN YANG INGIN DI-LOGIN
# ========================================================
USER_AKUN     = sys.argv[1] if len(sys.argv) > 1 else "lukyytris13" 
PASSWORD_AKUN = sys.argv[2] if len(sys.argv) > 2 else "Bryant12345678"          
device_id     = sys.argv[3] if len(sys.argv) > 3 else "all"

print("======================================================")
print("     INSTAGRAM LOGIN MASTER ROUTER ACTIVE")
print("======================================================")
print(f" Target User  : {USER_AKUN}")
print(f" Device ID    : {device_id}")
print("======================================================")

d = connect_adb(device_id)

width, height = d.window_size()

# Pastikan aplikasi Instagram terbuka terlebih dahulu agar layar termuat sempurna
print("Memastikan aplikasi Instagram terbuka...")
current_pkg = d.app_current().get('package', '')
if current_pkg != 'com.instagram.android':
    print("Membuka aplikasi Instagram...")
    d.app_start("com.instagram.android")
    time.sleep(6)
else:
    print("Instagram sudah terbuka.")
time.sleep(3)

# Cek interupsi Google Smart Lock di layar awal
try:
    if "credentialmanager" in d.app_current().get('package', '') or d(text="Batal").exists:
        print("Pop-up Google Smart Lock/Batal terdeteksi menghalangi deteksi layar awal. Mengklik Batal...")
        if d(text="Batal").exists:
            d(text="Batal").click()
        else:
            d.click(0.322, 0.873)
        time.sleep(3)
except Exception:
    pass

# DETEKSI KONDISI LAYAR SEKARANG
# ========================================================
print("\nMenganalisis tampilan layar perangkat...")

# Skenario 1: Sudah dalam keadaan masuk (Login) di akun lain
# Ditandai adanya tab navigasi bawah seperti feed_tab, profile_tab, search_tab, dsb.
is_logged_in_another = (
    d(resourceId="com.instagram.android:id/feed_tab").exists or
    d(resourceId="com.instagram.android:id/profile_tab").exists or
    d(resourceId="com.instagram.android:id/profile_tab_icon").exists or
    d(descriptionContains="Profil").exists or
    d(descriptionContains="Home").exists or
    d(descriptionContains="Search").exists
)

# Skenario 2: Layar re-entry profil ("Lanjutkan sebagai <username>" / "Continue as <username>")
# Ditandai adanya tombol profil bertuliskan nama akun / Lanjutkan
username_clean = USER_AKUN.split('@')[0]
is_reentry_screen = False

# Cek 1: Teks spesifik "Lanjutkan sebagai..." / "Continue as..." / "Lanjut" (exact description)
for regex in [
    fr"(?i).*(continue as|lanjut sebagai|log in as|masuk sebagai)\s+{username_clean}.*",
    fr"(?i).*(continue as|lanjut sebagai|log in as|masuk sebagai).*",
    r"(?i)^(continue|lanjut|lanjutkan)$"
]:
    if d(textMatches=regex).exists or d(descriptionMatches=regex).exists:
        is_reentry_screen = True
        break

# Cek 2: Tombol "Lanjut" / "Continue" DAN username target terlihat di layar (tapi bukan form normal)
if not is_reentry_screen:
    has_continue_btn = (
        d(textMatches="(?i).*(continue|lanjut).*").exists or 
        d(descriptionMatches="(?i).*(continue|lanjut).*").exists
    )
    has_username = (
        d(textContains=username_clean).exists or 
        d(descriptionContains=username_clean).exists
    )
    # Jika ada kolom input, itu form login normal, bukan reentry profil cepat
    is_normal_form = d(className="android.widget.EditText").exists
    
    if has_continue_btn and has_username and not is_normal_form:
        is_reentry_screen = True

# PILIH SCRIPT LOGIN YANG TEPAT
# ========================================================
target_script = ""
if is_logged_in_another:
    print("\n[DETEKSI] Skenario 1: Terdeteksi ada akun yang sudah Login.")
    print(" -> Menggunakan skrip switch account: bot_instagram_login_another.py")
    target_script = "bot_instagram_login_another.py"
elif is_reentry_screen:
    print("\n[DETEKSI] Skenario 2: Terdeteksi tombol profil cepat ('Lanjutkan sebagai').")
    print(" -> Menggunakan skrip login cepat: bot_instagram_login_reentry.py")
    target_script = "bot_instagram_login_reentry.py"
else:
    print("\n[DETEKSI] Skenario 3: Terdeteksi halaman login kosong / form username.")
    print(" -> Menggunakan skrip login normal: bot_instagram_login.py")
    target_script = "bot_instagram_login.py"

# EKSEKUSI SKRIP YANG DIPILIH
# ========================================================
python_bin = sys.executable
cmd = [python_bin, target_script, USER_AKUN, PASSWORD_AKUN, device_id]
print(f"Menjalankan perintah: {' '.join(cmd)}")
result = subprocess.run(cmd)

sys.exit(result.returncode)
