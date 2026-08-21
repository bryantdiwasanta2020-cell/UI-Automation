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

# TAHAP 1: PASTIKAN INSTAGRAM TERBUKA
# ========================================================
print("\n--- TAHAP 1: BUKA INSTAGRAM ---")
current_pkg = d.app_current().get('package', '')
if current_pkg != 'com.instagram.android':
    print("Membuka aplikasi Instagram...")
    d.app_start("com.instagram.android")
    time.sleep(6)
else:
    print("Instagram sudah terbuka.")
time.sleep(2)

# Bersihkan pop-up awal jika ada
try:
    from bot_instagram_clear_popups import clear_any_popup_fast
    clear_any_popup_fast(d)
except Exception as e:
    print(f"Peringatan: Gagal memanggil popup cleaner: {e}")

# TAHAP 2: BUKA MENU TAMBAH AKUN VIA PROFIL PAGE
# ========================================================
print("\n--- TAHAP 2: PROSES MENAMBAH AKUN BARU ---")

# 1. Pastikan di Halaman Profil
print(" Membuka Halaman Profil...")
profile_tab = None
for selector in [
    d(resourceId="com.instagram.android:id/profile_tab"),
    d(resourceId="com.instagram.android:id/profile_tab_icon"),
    d(descriptionContains="Profil"),
    d(descriptionContains="Profile"),
    d(descriptionContains="Profil Anda"),
    d(descriptionContains="Your Profile")
]:
    if selector.exists:
        profile_tab = selector
        break
        
if profile_tab:
    profile_tab.click()
else:
    # Fallback koordinat kanan bawah (Y=0.93 agar di atas navigasi sistem)
    d.click(int(width * 0.90), int(height * 0.93))
time.sleep(4)

# 2. Klik username di pojok kiri atas untuk membuka daftar akun
print(" Mengklik username di pojok kiri atas untuk membuka daftar akun...")
username_btn = None
for selector in [
    d(resourceId="com.instagram.android:id/title_text"),
    d(resourceId="com.instagram.android:id/action_bar_title"),
    d(resourceId="com.instagram.android:id/row_profile_header_username")
]:
    if selector.exists:
        username_btn = selector
        break

if username_btn:
    username_btn.click()
else:
    # Fallback koordinat kiri atas untuk username profile (biasanya x=20%, y=6%)
    d.click(int(width * 0.20), int(height * 0.06))
time.sleep(3)

# Ambil username bersih (tanpa domain email atau karakter khusus)
username_clean = USER_AKUN.split('@')[0]

# Cek apakah akun target sudah login dan ada di pop-up bawah
target_logged_in = False
for selector in [d(text=username_clean), d(description=username_clean)]:
    if selector.exists:
        print(f" [INFO] Akun @{username_clean} terdeteksi sudah login di perangkat ini. Beralih akun...")
        selector.click()
        target_logged_in = True
        break

if target_logged_in:
    print(" Menunggu proses pergantian akun (6 detik)...")
    time.sleep(6)
    
    # Jalankan pembersih pop-up pasca-login
    from bot_instagram_clear_popups import clear_post_login_popups
    clear_post_login_popups(d)
    print(" [SUKSES] Berhasil beralih ke akun yang sudah terdaftar!")
    sys.exit(0)

# Jika belum login, klik "Add Instagram account" / "Tambah akun Instagram"
print(" Akun belum login di perangkat ini. Mencari opsi 'Add Instagram account'...")
add_btn = None
for sel in [
    d(textMatches="(?i).*(add instagram account|tambah akun instagram|add account|tambah akun).*"),
    d(descriptionMatches="(?i).*(add instagram account|tambah akun instagram|add account|tambah akun).*")
]:
    if sel.exists:
        add_btn = sel
        break

if add_btn:
    print(" -> Mengklik tombol: 'Add Instagram account'")
    add_btn.click()
else:
    print(" -> Tombol Tambah Akun tidak terdeteksi via teks, menggunakan koordinat fallback (0.5, 0.68)...")
    d.click(int(width * 0.5), int(height * 0.68))
time.sleep(3)

# Klik "Masuk ke akun yang sudah ada" (Log in to existing account)
print(" Mencari pilihan 'Log in to existing account'...")
login_existing = None
for sel in [
    d(textMatches="(?i).*(masuk ke akun yang sudah ada|login ke akun yang sudah ada|log in to existing account|log in to an existing account|masuk ke akun lama|log in).*"),
    d(descriptionMatches="(?i).*(masuk ke akun yang sudah ada|login ke akun yang sudah ada|log in to existing account|log in to an existing account|masuk ke akun lama|log in).*")
]:
    if sel.exists:
        login_existing = sel
        break

if login_existing:
    print(" -> Mengklik 'Log in to existing account'...")
    login_existing.click()
else:
    print(" -> Opsi 'Login ke akun yang sudah ada' tidak terdeteksi, menggunakan koordinat fallback (0.831, 0.816)...")
    d.click(int(width * 0.831), int(height * 0.816))
time.sleep(4)

# TAHAP 3: PROSES OTENTIKASI (AKUN TERTAUT VS BELUM TERTAUT PADA PANEL TAMBAH AKUN)
# ========================================================
print("\n--- TAHAP 3: OTENTIKASI PADA PANEL TAMBAH AKUN ---")

try:
    current_pkg = d.app_current().get('package', '')
    if "credentialmanager" in current_pkg or d(text="Batal").exists:
        print("Pop-up Google Credential terdeteksi menghalangi layar!")
        if d(text="Batal").exists:
            d(text="Batal").click()
        else:
            d.click(0.322, 0.873) 
        time.sleep(3)
except Exception:
    pass

current_act = d.app_current().get('activity', '')
is_linked_on_device = False

for selector in [d(text=username_clean), d(description=username_clean)]:
    if selector.exists:
        is_linked_on_device = True
        break

if is_linked_on_device:
    print(f"[TIPE 1] Akun '{USER_AKUN}' terdeteksi SUDAH TERTAUT di panel login.")
    print(" Mencoba masuk dengan memilih akun tertaut...")
    
    clicked = False
    for selector in [d(text=username_clean), d(description=username_clean)]:
        if selector.exists:
            selector.click()
            clicked = True
            break
            
    time.sleep(6)
    
    # Periksa apakah meminta password
    if d(className="android.widget.EditText").exists:
        print(" Akun tertaut memerlukan Kata Sandi. Mengisi password...")
        pw_field = d(className="android.widget.EditText")
        pw_field.click()
        time.sleep(1)
        pw_field.set_text(PASSWORD_AKUN)
        time.sleep(2)
        
        # Klik tombol Masuk
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
        print(" [SUKSES] Berhasil login langsung via akun tertaut tanpa mengetik password!")

else:
    print(f"[TIPE 2] Akun '{USER_AKUN}' BELUM TERTAUT.")
    print(" Mencari opsi 'Add another account' untuk mengakses form username & password...")
    
    nav_clicked = False
    for sel in [
        d(textMatches="(?i).*(add another account|masuk ke akun lain|log in to another account|log into another account|tambah akun lain|use another|gunakan profil lain|gunakan akun lain).*"),
        d(descriptionMatches="(?i).*(add another account|masuk ke akun lain|log in to another account|log into another account|tambah akun lain|use another|gunakan profil lain|gunakan akun lain).*")
    ]:
        if sel.exists:
            try:
                print(f" -> Mengklik opsi: '{sel.get_text() if sel.exists else 'Use another account'}'")
                sel.click()
                nav_clicked = True
                time.sleep(5)
                break
            except:
                pass
            
    if not nav_clicked:
        if d(className="android.widget.EditText").exists:
            print(" Form login normal sudah terbuka.")
        else:
            if "ModalActivity" in current_act or d(className="android.widget.Button", description="Login").exists:
                print(" Terdeteksi modal pilihan akun lama.")
                if d(className="android.widget.Button", description="Login").exists:
                    d(className="android.widget.Button", description="Login").click()
                else:
                    d.click(0.854, 0.374)
            else:
                print(" Menembak koordinat default form login...")
                d.click(0.509, 0.915)
            time.sleep(5)
            
    # INPUT USERNAME & PASSWORD
    print("\n--- INPUT KREDENSIAL MANUAL ---")
    edit_texts = d(className="android.widget.EditText")
    
    # 1. Input Username
    username_field = None
    if edit_texts.exists and len(edit_texts) >= 1:
        username_field = edit_texts[0]
    elif d(descriptionContains="Nama pengguna").exists:
        username_field = d(descriptionContains="Nama pengguna")
    elif d(descriptionContains="Username").exists:
        username_field = d(descriptionContains="Username")
        
    if username_field and username_field.exists:
        print(f" Mengetik Username: {USER_AKUN}")
        username_field.click()
        time.sleep(1)
        username_field.set_text(USER_AKUN)
        time.sleep(2)
    else:
        print(" Menembak kolom username via koordinat...")
        d.click(0.145, 0.23) 
        time.sleep(1)
        d.send_keys(USER_AKUN)
        time.sleep(2)
        
    # 2. Input Password
    password_field = None
    if edit_texts.exists and len(edit_texts) >= 2:
        password_field = edit_texts[1]
    elif d(descriptionContains="Kata sandi").exists:
        password_field = d(descriptionContains="Kata sandi")
    elif d(descriptionContains="Password").exists:
        password_field = d(descriptionContains="Password")
        
    if password_field and password_field.exists:
        print(" Mengetik Kata Sandi...")
        password_field.click()
        time.sleep(1)
        password_field.set_text(PASSWORD_AKUN)
        time.sleep(2)
    else:
        print(" Menembak kolom password via koordinat...")
        d.click(0.327, 0.311)
        time.sleep(1)
        d.send_keys(PASSWORD_AKUN)
        time.sleep(2)
        
    # 3. Klik tombol Masuk
    print(" Mengklik tombol 'Log In'...")
    login_btn = None
    for selector in [
        d(resourceId="com.instagram.android:id/next_button"),
        d(resourceId="com.instagram.android:id/primary_button"),
        d(resourceIdMatches=".*login.*"),
        d(resourceIdMatches=".*log_in.*"),
        d(textMatches="(?i).*(log in|login|masuk).*"),
        d(descriptionMatches="(?i).*(log in|login|masuk).*"),
        d(className="android.widget.Button")
    ]:
        if selector.exists:
            login_btn = selector
            break
            
    if login_btn:
        login_btn.click()
    else:
        d.press("enter")
        
    print(" Menunggu proses otentikasi server Meta (8 detik)...")
    time.sleep(8)

# TAHAP 4: BERSIHKAN POP-UP PASCA-LOGIN & VERIFIKASI
# ========================================================
from bot_instagram_clear_popups import clear_post_login_popups
clear_post_login_popups(d)

xml_src = (d.dump_hierarchy() or "").lower()
if any(err in xml_src for err in ["incorrect password", "sandi salah", "can't find account", "tidak menemukan akun", "disabled", "ditangguhkan"]):
    print(" [FAILED] Login gagal, kredensial atau akun bermasalah.")
    sys.exit(1)

print(" [SUKSES] Akun baru berhasil ditambahkan dan diloginkan!")
sys.exit(0)
