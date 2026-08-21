import uiautomator2 as u2
import time
import imaplib
import email
import re

# ========================================================
#  CONFIG DATA REGISTRASI & EMAIL RAHASIA
# ========================================================
EMAIL_REGIST         = "bimadun584@gmail.com"  
PASSWORD_BARU        = "Bryant1234567"
SANDI_APLIKASI_GMAIL = "Bima12345" 

print("Menghubungkan ke HP Android via UiAutomator2...")
d = u2.connect()

def ambil_otp_gmail():
    """Fungsi untuk masuk ke Gmail dan mengambil 6 digit kode OTP terbaru"""
    print(" Bot mencoba mengakses Gmail untuk mengambil OTP...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_REGIST, SANDI_APLIKASI_GMAIL)
        mail.select("inbox")

        status, messages = mail.search(None, '(FROM "no-reply@mail.instagram.com")')
        mail_ids = messages[0].split()

        if not mail_ids:
            return None

        latest_mail_id = mail_ids[-1]
        status, data = mail.fetch(latest_mail_id, "(RFC822)")
        
        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject = msg["subject"]
                print(f" Email ditemukan! Subjek: {subject}")
                
                angka_otp = re.findall(r'\b\d{6}\b', str(subject))
                if not angka_otp:
                    if msg.is_multipart():
                        for part in msg.walk():
                            body = part.get_payload(decode=True).decode(errors='ignore')
                            angka_otp = re.findall(r'\b\d{6}\b', body)
                            if angka_otp: break
                    else:
                        body = msg.get_payload(decode=True).decode(errors='ignore')
                        angka_otp = re.findall(r'\b\d{6}\b', body)

                if angka_otp:
                    return angka_otp[0]
        return None
    except Exception as e:
        print(f" Gagal mengakses Gmail: {e}")
        return None

# ========================================================
# TAHAP 1: BUKA INSTAGRAM
# ========================================================
print("\n--- TAHAP 1: BUKA INSTAGRAM ---")
d.press("home")
time.sleep(1.5)
d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.2)
time.sleep(2)

if d(text="Instagram").exists:
    d(text="Instagram").click()
else:
    d.swipe(0.8, 0.5, 0.2, 0.5, duration=0.2)
    time.sleep(1)
    d(text="Instagram").click()

print("Menunggu Instagram terbuka...")
time.sleep(6)

# ========================================================
# TAHAP 2: DI HALAMAN PENDAFTARAN (PINDAH KE EMAIL)
# ========================================================
print("\n--- TAHAP 2: PROSES REGISTRASI EMAIL ---")
if d(description="Buat akun baru").exists:
    d(description="Buat akun baru").click()
elif d(text="Buat akun baru").exists:
    d(text="Buat akun baru").click()
else:
    d.click(0.663, 0.855) 
time.sleep(4)

print("Mengklik tombol 'Daftar dengan email'...")
if d(className="android.widget.Button", description="Daftar dengan email").exists:
    d(className="android.widget.Button", description="Daftar dengan email").click()
else:
    d.click(0.754, 0.472)
time.sleep(5)

if d(className="android.widget.EditText").exists:
    print(f"Mengetik Alamat Email: {EMAIL_REGIST}") 
    d(className="android.widget.EditText").set_text(EMAIL_REGIST)
    time.sleep(5)

print("Menurunkan keyboard...")
d.press("back")
time.sleep(2)

print("Mengklik tombol Berikutnya...")
if d(className="android.widget.Button", description="Berikutnya").exists:
    d(className="android.widget.Button", description="Berikutnya").click()
else:
    d.click(0.695, 0.376)

# ========================================================
# GERBANG LOADING: MENUNGGU EMAIL KODE OTP MUNCUL
# ========================================================
print("\n Menunggu 15 detik agar Instagram selesai mengirim email...")
time.sleep(15)

halaman_otp_ready = False
for j in range(1, 10): 
    if d(className="android.widget.EditText").exists:
        halaman_otp_ready = True
        break
    time.sleep(2)

# ========================================================
# TAHAP 3: EKSTRAKSI OTP OTOMATIS
# ========================================================
if halaman_otp_ready:
    otp_input = ambil_otp_gmail()
    
    if otp_input:
        print(f"BERHASIL! Menemukan kode OTP: {otp_input}")
        print(f"Memasukkan kode OTP {otp_input} ke HP...")
        d(className="android.widget.EditText").set_text(otp_input)
        time.sleep(2)
    else:
        otp_input = input(" Gagal ambil otomatis. Tolong masukkan manual 6 Digit OTP: ")
        d(className="android.widget.EditText").set_text(otp_input)

    d.press("back")
    time.sleep(2)

    print("Mengklik tombol Berikutnya...")
    if d(className="android.widget.Button", description="Berikutnya").exists:
        d(className="android.widget.Button", description="Berikutnya").click()
    else:
        d.click(0.695, 0.376)
    time.sleep(6)
else:
    print(" Gagal: Layar tertahan di loading terlalu lama.")
    exit()

# ========================================================
# TAHAP 4: HALAMAN BUAT KATA SANDI
# ========================================================
print("\n--- TAHAP 4: PENGISIAN KATA SANDI ---")
if d(className="android.widget.EditText").exists:
    print(f"Mengetik kata sandi baru: {PASSWORD_BARU}")
    d(className="android.widget.EditText").set_text(PASSWORD_BARU)
    time.sleep(2)

print("Menurunkan keyboard...")
d.press("back")
time.sleep(2)

print("Mengklik tombol Berikutnya setelah Sandi...")
if d(className="android.widget.Button", description="Berikutnya").exists:
    d(className="android.widget.Button", description="Berikutnya").click()
else:
    d.click(0.686, 0.378)

# =====================================================================
# TAHAP INTERUPSI META (PUTAR BALIK KE LOGIN AKUN EXIST)
# =====================================================================
print("\n--- TAHAP INTERUPSI: DETEKSI AKUN GANDA OLEH META ---")
print(" Mengecek apakah muncul pop-up interupsi 'Login ke akun ada'...")
time.sleep(6) 

mau_login_otomatis = False

# DETEKSI TOMBOL 1 (LOGIN KE AKUN YANG SUDAH ADA)
if d(resourceId="android:id/button1", text="LOGIN KE AKUN YANG SUDAH ADA").exists:
    print(" WARNING: Pembuatan akun baru diblokir, mengalihkan ke opsi Login!")
    print(" Mengeksekusi: Mengklik 'LOGIN KE AKUN YANG SUDAH ADA'...")
    d(resourceId="android:id/button1", text="LOGIN KE AKUN YANG SUDAH ADA").click()
    mau_login_otomatis = True
    time.sleep(6)
elif d(textContains="LOGIN KE AKUN").exists:
    print(" Deteksi alternatif teks berhasil, mengklik opsi Login...")
    d(textContains="LOGIN KE AKUN").click()
    mau_login_otomatis = True
    time.sleep(6)
else:
    print(" Aman! Meta tidak menginterupsi, lanjut mendaftarkan data baru.")

# PERCABANGAN UTAMA: JALUR LOGIN VS JALUR REGISTER DATA BARU
if mau_login_otomatis:
    print(" MENGALIKAN JALUR BOT: Mengisi kredensial password login...")
    time.sleep(4)
    
    # Jika Instagram meminta konfirmasi password lagi di halaman login otomatis
    if d(className="android.widget.EditText").exists:
        print(" Mengetik kembali password untuk proses verifikasi masuk...")
        d(className="android.widget.EditText").set_text(PASSWORD_BARU)
        time.sleep(2)
        d.press("back")
        time.sleep(1)
        
        if d(className="android.widget.Button", description="Berikutnya").exists:
            d(className="android.widget.Button", description="Berikutnya").click()
        elif d(className="android.widget.Button", text="Log In").exists:
            d(className="android.widget.Button", text="Log In").click()
        else:
            d.click(0.686, 0.378)
        time.sleep(8)
    else:
        print(" Otomatis dialihkan ke halaman utama/verifikasi beranda.")

else:
    # ========================================================
    # TAHAP 5: HALAMAN TANGGAL LAHIR (Hanya jalan jika registrasi baru berhasil)
    # ========================================================
    print("\n--- TAHAP 5: HALAMAN TANGGAL LAHIR (JANUARI, TGL 3x, THN 7x) ---")
    print(" Menunggu halaman Tanggal Lahir termuat...")
    time.sleep(5)

    if d(textContains="2026").exists or d(descriptionContains="Tanggal lahir").exists or d.click(0.681, 0.327):
        print(" Halaman Tanggal Lahir terdeteksi.")
        if d(textContains="2026").exists:
            d(textContains="2026").click()
        else:
            d.click(0.681, 0.327) 
        time.sleep(2)

        print(" Menggeser roda bulan ke Januari...")
        for _ in range(12): 
            d.swipe(0.25, 0.55, 0.25, 0.75, duration=0.2) 
            time.sleep(0.3)

        print(" Menggeser roda tanggal sebanyak 3 kali...")
        for _ in range(3):
            d.swipe(0.50, 0.55, 0.50, 0.75, duration=0.2) 
            time.sleep(0.5)

        print(" Menggeser roda tahun mundur sebanyak 7 kali...")
        for _ in range(7):
            d.swipe(0.75, 0.55, 0.75, 0.75, duration=0.2) 
            time.sleep(0.5)

        print("Mengklik tombol 'ATUR'...")
        if d(resourceId="android:id/button1", text="ATUR").exists:
            d(resourceId="android:id/button1", text="ATUR").click()
        else:
            d.click(0.713, 0.631) 
        time.sleep(3)

        print("Mengklik tombol 'Berikutnya' di halaman Tanggal Lahir...")
        if d(className="android.widget.Button", description="Berikutnya").exists:
            d(className="android.widget.Button", description="Berikutnya").click()
        else:
            d.click(0.772, 0.411) 
        time.sleep(5)

    # ========================================================
    # TAHAP 5.5: HALAMAN NAMA LENGKAP 
    # ========================================================
    print("\n--- TAHAP 5.5: PENGISIAN NAMA LENGKAP ---")
    time.sleep(4)
    if d(className="android.widget.EditText", description="Nama lengkap,").exists or d.click(0.445, 0.187):
        if d(className="android.widget.EditText", description="Nama lengkap,").exists:
            d(className="android.widget.EditText", description="Nama lengkap,").set_text("Bryant")
        else:
            d.click(0.445, 0.187)
            time.sleep(0.5)
            d.send_keys("Bryant")
        time.sleep(2)
        d.press("back")
        time.sleep(1.5)

        if d(className="android.widget.Button", description="Berikutnya").exists:
            d(className="android.widget.Button", description="Berikutnya").click()
        else:
            d.click(0.69, 0.272)
        time.sleep(6)

    # ========================================================
    # TAHAP 6: HALAMAN BUAT NAMA PENGGUNA (USERNAME)
    # ========================================================
    print("\n--- TAHAP 6: HALAMAN BUAT NAMA PENGGUNA (USERNAME) ---")
    time.sleep(5)
    if d(className="android.widget.Button", description="Berikutnya").exists or d.click(0.677, 0.266):
        if d(className="android.widget.Button", description="Berikutnya").exists:
            d(className="android.widget.Button", description="Berikutnya").click()
        else:
            d.click(0.677, 0.266)
        time.sleep(6)

    # ========================================================
    # TAHAP 7: HALAMAN KETENTUAN & KEBIJAKAN META (SAYA SETUJU)
    # ========================================================
    print("\n--- TAHAP 7: HALAMAN KEBIJAKAN META (FINAL) ---")
    time.sleep(6)
    if d(className="android.widget.Button", description="Saya setuju").exists or d(text="Saya setuju").exists:
        if d(className="android.widget.Button", description="Saya setuju").exists:
            d(className="android.widget.Button", description="Saya setuju").click()
        else:
            d.text("Saya setuju").click()
    else:
        d.click(0.259, 0.586)
    time.sleep(12)

# =====================================================================
# ZONA PENYATUAN ALUR: PEMBERSIHAN POP-UP BERANDA (UNTUK LOGIN & REGIST)
# =====================================================================

# ========================================================
# TAHAP 8: BYPASS WELCOME SCREEN (NUX - LAIN KALI)
# ========================================================
print("\n--- TAHAP 8: BYPASS WELCOME SCREEN (NUX) ---")
print(" Menunggu halaman pengenalan pengguna baru (NUX)...")
time.sleep(8)

if d(resourceId="com.instagram.android:id/igds_headline_secondary_action_text_button").exists or d(text="Lain kali").exists:
    print("Tombol NUX 'Lain kali' terdeteksi oleh bot!")
    if d(resourceId="com.instagram.android:id/igds_headline_secondary_action_text_button").exists:
        d(resourceId="com.instagram.android:id/igds_headline_secondary_action_text_button").click()
    else:
        d(text="Lain kali").click()
    time.sleep(5)
else:
    print(" Menembak lewat koordinat jagoan...")
    d.click(0.609, 0.863)
    time.sleep(5)

if d(resourceId="com.instagram.android:id/igds_headline_secondary_action_text_button").exists:
    d(resourceId="com.instagram.android:id/igds_headline_secondary_action_text_button").click()
    time.sleep(4)

# ========================================================
# TAHAP 9: BYPASS PERMISSION SYSTEM ANDROID (MULTI POP-UP)
# ========================================================
print("\n--- TAHAP 9: BYPASS PERMISSION SYSTEM ANDROID ---")
time.sleep(4)
for i in range(1, 4):
    if d(resourceId="com.android.permissioncontroller:id/permission_deny_button").exists or d(text="Jangan izinkan").exists:
        print(f"Pop-up Izin Android ke-{i} terdeteksi! Klik Jangan izinkan...")
        if d(resourceId="com.android.permissioncontroller:id/permission_deny_button").exists:
            d(resourceId="com.android.permissioncontroller:id/permission_deny_button").click()
        else:
            d.click(0.722, 0.879)
        time.sleep(3) 
    else:
        break

# ========================================================
# TAHAP 10: SIKAT BERSIH ALL ONBOARDING & POP-UP (LOOPING)
# ========================================================
print("\n--- TAHAP 10: SIKAT BERSIH ALL ONBOARDING & POP-UP ---")
time.sleep(4)
for putaran in range(1, 11):
    print(f" Memeriksa sisa rintangan onboarding (Putaran ke-{putaran})...")
    rintangan_ditemukan = False

    if d(resourceId="com.instagram.android:id/action_bar_action_text", text="Lewati").exists:
        d(resourceId="com.instagram.android:id/action_bar_action_text", text="Lewati").click()
        rintangan_ditemukan = True
    elif d(resourceId="com.instagram.android:id/skip_button").exists or d(text="Lewati").exists:
        if d(resourceId="com.instagram.android:id/skip_button").exists:
            d(resourceId="com.instagram.android:id/skip_button").click()
        else:
            d(text="Lewati").click()
        rintangan_ditemukan = True
    elif d(resourceId="com.instagram.android:id/igds_alert_dialog_cancel_button").exists or d(text="Tidak, lewati").exists:
        if d(resourceId="com.instagram.android:id/igds_alert_dialog_cancel_button").exists:
            d(resourceId="com.instagram.android:id/igds_alert_dialog_cancel_button").click()
        else:
            d.click(0.495, 0.613)
        rintangan_ditemukan = True

    if rintangan_ditemukan:
        time.sleep(4) 
    else:
        print(" Layar onboarding sudah bersih!")
        break

time.sleep(2)
if d(activity="com.instagram.nux.impl.dynamicflow.onboarding.OnboardingActivity").exists:
    d.click(0.886, 0.057)
    time.sleep(5)

# ========================================================
# TAHAP 11: HALAMAN UTAMA BERANDA (KLIK PAHAM FINAL)
# ========================================================
print("\n--- TAHAP 11: HALAMAN UTAMA BERANDA (WELCOME POP-UP) ---")
time.sleep(5)
if d(resourceId="com.instagram.android:id/igds_headline_primary_action_button").exists or d(description="Paham").exists:
    print(" Pop-up 'Paham' di Beranda Utama terdeteksi! Klik...")
    if d(resourceId="com.instagram.android:id/igds_headline_primary_action_button").exists:
        d(resourceId="com.instagram.android:id/igds_headline_primary_action_button").click()
    else:
        d.click(0.6, 0.869)
    time.sleep(4)

print("\n ========================================================")
print(" [GRAND MISSION ACCOMPLISHED] PROSES SELESAI SAKSES!")
print("   Bot berhasil membawa akun masuk ke beranda via jalur aman!")
print("======================================================== \n")