import uiautomator2 as u2
import time
import sys

# CONFIG DATA AKUN YANG INGIN DI-LOGIN
# ========================================================
# Jalur argumen: script, username (contoh: uyug), device_id (contoh: all atau S/N spesifik)
USER_AKUN = sys.argv[1] if len(sys.argv) > 1 else""
device_id = sys.argv[2] if len(sys.argv) > 2 else ""

print(f"Menghubungkan ke HP Android ({device_id}) via UiAutomator2...")
try:
    if not device_id or device_id == "all" or device_id == "Semua Akun Aktif (18 Device)":
        d = u2.connect()
    else:
        d = u2.connect(device_id)
    print(f"Terhubung ke perangkat: {d.device_info.get('brand', 'Unknown')} {d.device_info.get('model', 'Device')}")
except Exception as e:
    print(f"[ERROR] Gagal terhubung ke perangkat ADB: {e}")
    sys.exit(1)


def click_element_coords(d, selector):
    """Mencoba mengklik elemen menggunakan koordinat pixel pusat (x, y) agar lebih andal pada Bloks/React Native."""
    try:
        if selector.exists:
            info = selector.info
            bounds = info.get('bounds')
            if bounds:
                x_center = (bounds['left'] + bounds['right']) // 2
                y_center = (bounds['top'] + bounds['bottom']) // 2
                print(f"Mengklik koordinat pusat: ({x_center}, {y_center})")
                d.click(x_center, y_center)
                return True
            else:
                selector.click()
                return True
    except Exception as e:
        print(f"Gagal klik koordinat, fallback ke click standar: {e}")
        try:
            selector.click()
            return True
        except:
            pass
    return False


# TAHAP 1: BUKA APLIKASI FACEBOOK
# ========================================================
print("\n--- TAHAP 1: BUKA APLIKASI FACEBOOK ---")
d.press("home")
time.sleep(1.5)

# Coba jalankan aplikasi Facebook (Katana) atau Facebook Lite
package_name = "com.facebook.katana"
print("Mencoba membuka Facebook (com.facebook.katana)...")
try:
    d.app_start(package_name)
except Exception:
    print("Facebook Utama gagal dibuka. Mencoba Facebook Lite (com.facebook.lite)...")
    package_name = "com.facebook.lite"
    try:
        d.app_start(package_name)
    except Exception as e:
        print(f"[ERROR] Tidak dapat membuka Facebook maupun Facebook Lite: {e}")
        sys.exit(1)

print("Menunggu aplikasi Facebook terbuka...")
time.sleep(8)


# TAHAP 2: DETEKSI STATUS LOGIN / BERSINKAN PENGHALANG
# ========================================================
print("\n--- TAHAP 2: MEMERIKSA STATUS LOGIN ---")

# Bersihkan pop-up Google Credential Manager jika menghalangi
current_pkg = d.app_current().get('package', '')
if "credentialmanager" in current_pkg or d(text="Batal").exists:
    print("Pop-up Google Credential terdeteksi! Mengklik 'Batal'...")
    if d(text="Batal").exists:
        d(text="Batal").click()
    else:
        d.click(0.5, 0.9)  # Koordinat default bawah layar
    time.sleep(2)

# Cek apakah sudah berada di dalam aplikasi (Home / Feed)
is_logged_in = False
home_selectors = [
    d(resourceId="com.facebook.katana:id/feed_tab"),
    d(resourceId="com.facebook.katana:id/main_tabs"),
    d(resourceId="com.facebook.lite:id/feed_view"),
    d(description="Kabar Beranda"),
    d(description="News Feed")
]

print("Memeriksa apakah akun Facebook sudah dalam posisi login...")
for selector in home_selectors:
    if selector.exists:
        print(f"Terdeteksi elemen beranda: '{selector.info.get('resourceName') or selector.info.get('contentDescription')}'")
        is_logged_in = True
        break

if is_logged_in:
    print("[SUKSES] Akun sudah login sebelumnya. Misi selesai.")
    sys.exit(0)


# TAHAP 3: CARI DAN KLIK AKUN INSTAGRAM YANG TAUTKAN
# ========================================================
print("\n--- TAHAP 3: MENCARI AKUN INSTAGRAM YANG TAUTKAN ---")
account_clicked = False

max_wait_auth = 20
start_time_auth = time.time()

while time.time() - start_time_auth < max_wait_auth:
    # 1. Coba cari dengan selector langsung
    selectors_pencarian = []
    
    if USER_AKUN and USER_AKUN.strip():
        # Masukkan selector pencarian username spesifik
        selectors_pencarian.extend([
            d(descriptionContains=USER_AKUN),
            d(textContains=USER_AKUN),
            d(descriptionContains=USER_AKUN.lower()),
            d(textContains=USER_AKUN.lower()),
            d(descriptionContains=USER_AKUN.upper()),
            d(textContains=USER_AKUN.upper())
        ])
    else:
        # Masukkan selector umum jika USER_AKUN kosong
        selectors_pencarian.extend([
            d(descriptionContains="Continue as"),
            d(descriptionContains="Lanjutkan sebagai"),
            d(textContains="Continue as"),
            d(textContains="Lanjutkan sebagai"),
            d(descriptionContains="Masuk sebagai"),
            d(descriptionContains="Log in as"),
            d(textContains="Masuk sebagai"),
            d(textContains="Log in as"),
            d(textContains="Instagram"),
            d(descriptionContains="Instagram")
        ])

    # Coba cari dan klik selector yang sesuai
    for idx, selector in enumerate(selectors_pencarian):
        if selector.exists:
            try:
                info = selector.info
                text_info = info.get('text', '') or info.get('contentDescription', '')
                
                # Jika user minta username spesifik, pastikan username ada dalam teks/desc elemen
                if USER_AKUN and USER_AKUN.strip():
                    if USER_AKUN.lower() not in text_info.lower():
                        continue # Akun yang berbeda, lewati
                
                print(f"Menemukan target: '{text_info}'. Mengklik...")
                click_element_coords(d, selector)
                account_clicked = True
                break
            except Exception as click_err:
                print(f"Gagal mengklik target: {click_err}")
                
    if account_clicked:
        time.sleep(6)
        break

    # 2. Jika tidak terdeteksi via selector langsung, coba scan clickable elements secara manual (sangat akurat)
    try:
        matched_xpath_el = None
        for el in d.xpath('//*[@clickable="true"]').all():
            attrib = el.attrib
            text = attrib.get('text', '') or ''
            desc = attrib.get('content-desc', '') or ''
            
            # Uji kecocokan
            if USER_AKUN and USER_AKUN.strip():
                # Harus mengandung username yang diminta
                if USER_AKUN.lower() in text.lower() or USER_AKUN.lower() in desc.lower():
                    matched_xpath_el = el
                    print(f" -> [MATCH XPath] Menemukan akun '{USER_AKUN}' pada elemen: Text='{text}' | Desc='{desc}'")
                    break
            else:
                # Jika kosong, cari kata kunci continue / lanjutkan / masuk sebagai default
                lower_all = (text + " " + desc).lower()
                if "continue as" in lower_all or "lanjutkan sebagai" in lower_all or "masuk sebagai" in lower_all or "log in as" in lower_all:
                    matched_xpath_el = el
                    print(f" -> [DEFAULT MATCH XPath] Menemukan tombol login default: Text='{text}' | Desc='{desc}'")
                    break
                        
        if matched_xpath_el:
            matched_xpath_el.click()
            account_clicked = True
            time.sleep(6)
            break
    except Exception as scan_err:
        print(f"Gagal memindaian clickable elements via XPath: {scan_err}")

    print("Menunggu halaman pilihan akun Facebook dimuat...")
    time.sleep(2.5)

if not account_clicked:
    # Cari tombol Buat Akun Baru / Create New Account jika akun instan tidak ada
    create_account_targets = [
        "Buat akun baru", "Buat Akun Baru", "Create new account", "Create New Account",
        "Buat akun", "Create account", "Daftar ke Facebook", "Sign Up"
    ]
    for target in create_account_targets:
        btn = d(text=target)
        if not btn.exists:
            btn = d(textContains=target)
        if not btn.exists:
            btn = d(description=target)
            
        if btn.exists:
            print(f"\n[CREATE ACCOUNT] Menemukan opsi buat akun baru: '{target}'. Mengklik...")
            click_element_coords(d, btn)
            time.sleep(6)
            account_clicked = True
            break

if not account_clicked:
    # Koordinat cadangan di area tengah-bawah layar
    print("Tombol login tidak terdeteksi. Mencoba klik koordinat tengah-bawah cadangan (0.5, 0.75)...")
    d.click(0.5, 0.75)
    time.sleep(6)


# TAHAP 4: KLIK OKE ATAU ACC POPUP/KONFIRMASI
# ========================================================
print("\n--- TAHAP 4: MENYELESAIKAN PERSUBUTAN / KONFIRMASI ---")

# Inisialisasi status form pengisian untuk membuat akun baru secara dinamis
name_filled = False
gender_selected = False
contact_filled = False
password_filled = False

# Beri waktu beberapa detik untuk memuat halaman persetujuan (200 detik agar cukup untuk pendaftaran akun)
max_wait = 200
start_time = time.time()

approved = False
while time.time() - start_time < max_wait:
    # 1. Deteksi dan isi form input jika muncul di layar
    edit_texts = d(className="android.widget.EditText")
    if edit_texts.exists and len(edit_texts) > 0:
        # Cek apakah layar meminta nama
        is_name_screen = False
        for keyword in ["nama", "name", "depan", "belakang", "first", "last"]:
            if d(textContains=keyword).exists or d(descriptionContains=keyword).exists:
                is_name_screen = True
                break
                
        if is_name_screen and not name_filled:
            import random
            first_names = ["Luki", "Adi", "Budi", "Chandra", "Dewi", "Eko", "Fajar", "Gita", "Hadi", "Indra", "Joko", "Kartika", "Mega", "Nugroho", "Putra", "Rini", "Sari", "Tono", "Wawan", "Yudi"]
            last_names = ["Prasetyo", "Santoso", "Wijaya", "Kurniawan", "Saputra", "Hidayat", "Nugraha", "Setiawan", "Utomo", "Wibowo", "Siregar", "Harahap", "Ginting", "Nasution", "Tanjung", "Lubis", "Pasaribu"]
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            print("\n[FORM NAMA] Mendeteksi form pengisian nama di layar!")
            if len(edit_texts) >= 2:
                print(f"Mengisi Nama Depan: '{first_name}' dan Nama Belakang: '{last_name}'")
                edit_texts[0].set_text(first_name)
                time.sleep(1.5)
                edit_texts[1].set_text(last_name)
                time.sleep(1.5)
            else:
                full_name = f"{first_name} {last_name}"
                print(f"Mengisi Nama Lengkap: '{full_name}'")
                edit_texts[0].set_text(full_name)
                time.sleep(1.5)
                
            # Cari dan klik tombol Next / Lanjutkan / Save / Daftar
            next_clicked = False
            for btn_text in ["Lanjutkan", "Next", "Berikutnya", "Simpan", "Save", "Daftar", "Sign Up", "Oke", "OK"]:
                btn = d(textContains=btn_text)
                if btn.exists:
                    print(f"Mengklik tombol lanjutan form nama: '{btn_text}'")
                    click_element_coords(d, btn)
                    next_clicked = True
                    time.sleep(5)
                    break
            if not next_clicked:
                print("Tombol lanjut tidak terdeteksi via teks, menekan tombol ENTER...")
                d.press("enter")
                time.sleep(5)
            name_filled = True
            
        # 1.2 Deteksi form input email atau nomor HP jika muncul di layar (setelah nama diisi)
        elif name_filled and not contact_filled:
            is_contact_screen = False
            for keyword in ["telepon", "phone", "seluler", "mobile", "email", "surel", "nomor", "number"]:
                if d(textContains=keyword).exists or d(descriptionContains=keyword).exists:
                    is_contact_screen = True
                    break
                    
            if is_contact_screen:
                contact_info = USER_AKUN if (USER_AKUN and ("@" in USER_AKUN or USER_AKUN.isdigit())) else f"user_{int(time.time())}@gmail.com"
                print(f"\n[FORM KONTAK] Mengisi kolom kontak dengan: '{contact_info}'")
                edit_texts[0].set_text(contact_info)
                time.sleep(1.5)
                
                # Klik tombol lanjut
                next_clicked = False
                for btn_text in ["Lanjutkan", "Next", "Berikutnya", "Daftar", "Sign Up", "Oke", "OK"]:
                    btn = d(textContains=btn_text)
                    if btn.exists:
                      print(f"Mengklik tombol lanjutan setelah isi kontak: '{btn_text}'")
                      click_element_coords(d, btn)
                      next_clicked = True
                      time.sleep(5)
                      break
                if not next_clicked:
                    d.press("enter")
                    time.sleep(5)
                contact_filled = True
                
        # 1.3 Deteksi form input password / kata sandi jika muncul
        elif name_filled and not password_filled:
            is_password_screen = False
            for keyword in ["sandi", "password", "security"]:
                if d(textContains=keyword).exists or d(descriptionContains=keyword).exists:
                    is_password_screen = True
                    break
                    
            if is_password_screen:
                default_pass = "Bryant12345678!"
                print(f"\n[FORM SANDI] Mengisi kata sandi baru dengan: '{default_pass}'")
                edit_texts[0].set_text(default_pass)
                time.sleep(1.5)
                
                # Klik tombol lanjut
                next_clicked = False
                for btn_text in ["Lanjutkan", "Next", "Berikutnya", "Daftar", "Sign Up", "Oke", "OK"]:
                    btn = d(textContains=btn_text)
                    if btn.exists:
                      print(f"Mengklik tombol lanjutan setelah isi sandi: '{btn_text}'")
                      click_element_coords(d, btn)
                      next_clicked = True
                      time.sleep(5)
                      break
                if not next_clicked:
                    d.press("enter")
                    time.sleep(5)
                password_filled = True
            
    # 1b. Deteksi dan pilih Gender jika muncul di layar (pilih Laki-laki / Male)
    if not gender_selected:
        gender_options = ["Laki-laki", "Laki-Laki", "Male"]
        for option in gender_options:
            gender_el = d(text=option)
            if not gender_el.exists:
                gender_el = d(textContains=option)
            if not gender_el.exists:
                gender_el = d(description=option)
            if not gender_el.exists:
                gender_el = d(descriptionContains=option)
                
            if gender_el.exists:
                print(f"\n[FORM GENDER] Mendeteksi pilihan gender: '{option}'")
                click_element_coords(d, gender_el)
                time.sleep(3)
                
                # Cari dan klik tombol Next / Lanjutkan setelah pilih gender
                next_clicked = False
                for btn_text in ["Lanjutkan", "Next", "Berikutnya", "Simpan", "Save", "Daftar", "Sign Up", "Oke", "OK"]:
                    btn = d(textContains=btn_text)
                    if btn.exists:
                        print(f"Mengklik tombol lanjutan setelah pilih gender: '{btn_text}'")
                        click_element_coords(d, btn)
                        next_clicked = True
                        time.sleep(5)
                        break
                if not next_clicked:
                    print("Tombol lanjut tidak terdeteksi via teks, menekan ENTER...")
                    d.press("enter")
                    time.sleep(5)
                gender_selected = True
                break

    # 2. Cari tombol bertuliskan Oke, Setuju, Lanjutkan, Izinkan, Ya, Confirm, dll.
    confirm_targets = [
        # TINGKAT 1: Persetujuan/Penautan Akun Utama / Mulai Pembuatan Akun
        "Allow and continue", "Allow and Continue", "allow and continue", "Izinkan dan lanjutkan", "Izinkan dan Lanjutkan",
        "Oke", "OK", "Setuju", "Agree", "Ya, Hubungkan", "Yes, Connect", "Yes, Link", "Izinkan", "Allow", "Confirm", "Konfirmasi",
        "Saya Setuju", "I Agree", "Atur", "Set", "Gunakan", "Use", "Mulai", "Get Started", "Berikutnya",
        
        # TINGKAT 2: Lewati/Skip wizard penyiapan profil (agar tidak mengubah data akun)
        "Lewati", "Skip", "Lain kali", "Lain Kali", "Not now", "Not Now", "Jangan sekarang", "Jangan Sekarang", "Tutup", "Close", "Batal", "Cancel",
        
        # TINGKAT 3: Kelanjutan umum (Lanjutkan/Continue)
        "Lanjutkan", "Continue", "Done"
    ]
    
    for target in confirm_targets:
        # Coba klik berdasarkan teks
        el = d(text=target)
        if el.exists:
            text_val = el.info.get('text', '') or el.info.get('contentDescription', '') or ''
            if "without" in text_val.lower() or "tanpa" in text_val.lower():
                print(f"Skipping negative option: '{text_val}'")
                continue
            print(f"Menemukan tombol konfirmasi: '{target}'. Mengklik...")
            click_element_coords(d, el)
            approved = True
            time.sleep(4)
            break
            
        # Coba klik berdasarkan textContains (hanya jika panjang teks tidak terlalu panjang)
        el = d(textContains=target)
        if el.exists and len(el.info.get('text', '')) < 35:
            text_val = el.info.get('text', '')
            if "without" in text_val.lower() or "tanpa" in text_val.lower():
                print(f"Skipping negative option (contains): '{text_val}'")
                continue
            print(f"Menemukan tombol konfirmasi (contains): '{text_val}'. Mengklik...")
            click_element_coords(d, el)
            approved = True
            time.sleep(4)
            break

        # Coba klik berdasarkan description
        el = d(description=target)
        if el.exists:
            desc_val = el.info.get('contentDescription', '') or ''
            if "without" in desc_val.lower() or "tanpa" in desc_val.lower():
                print(f"Skipping negative option (description): '{desc_val}'")
                continue
            print(f"Menemukan tombol konfirmasi (deskripsi): '{target}'. Mengklik...")
            click_element_coords(d, el)
            approved = True
            time.sleep(4)
            break

    # Cek apakah beranda Facebook sudah terbuka
    for selector in home_selectors:
        if selector.exists:
            print("[SUKSES] Berhasil masuk to Beranda Facebook!")
            sys.exit(0)
            
    time.sleep(2)

# Cek hasil akhir
for selector in home_selectors:
    if selector.exists:
        print("[SUKSES] Berhasil masuk to Beranda Facebook!")
        sys.exit(0)

print("[PERINGATAN] Selesai melakukan alur klik, tetapi halaman utama Facebook tidak terdeteksi.")
print("Periksa layar perangkat untuk memastikan apakah login memerlukan verifikasi tambahan.")
sys.exit(1)
