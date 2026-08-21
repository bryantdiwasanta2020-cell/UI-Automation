import uiautomator2 as u2
import time
import os
import imaplib
import email
import re

# ========================================================
# KONFIGURASI AKUN GMAIL KAMU
# ========================================================
EMAIL_KAMU = "bimadun584@gmail.com"
#  MASUKKAN 16 DIGIT SANDI APLIKASI KAMU DI SINI (TANPA SPASI)
GMAIL_APP_PASSWORD = "Bima12345" 

# Menghubungkan ke HP Android
d = u2.connect() 

def ambil_otp_dari_server_gmail():
    """Fungsi VIP untuk masuk ke server Gmail dan mengambil OTP Telegram"""
    print("Menghubungkan ke server Gmail via IMAP...")
    try:
        # Konek ke server aman Gmail
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_KAMU, GMAIL_APP_PASSWORD)
        mail.select("inbox")
        
        # Cari email terbaru dari Telegram
        status, messages = mail.search(None, '(FROM "Telegram")')
        
        if status == "OK" and messages[0]:
            email_ids = messages[0].split()
            latest_email_id = email_ids[-1] # Ambil email paling terakhir/terbaru
            
            # Ambil data konten email
            status, data = mail.fetch(latest_email_id, "(RFC822)")
            raw_email = data[0][1]
            
            msg = email.message_from_bytes(raw_email)
            isi_email = ""
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        isi_email = part.get_payload(decode=True).decode()
                        break
            else:
                isi_email = msg.get_payload(decode=True).decode()
            
            # Cari 5 atau 6 digit angka OTP Telegram
            kode_otp = re.findall(r'\b\d{5,6}\b', isi_email)
            if kode_otp:
                # Cari yang bukan kode negara atau bagian teks lain
                for angka in kode_otp:
                    if angka != "62" and angka != "85770":
                        print(f"-> [SUKSES SERVER] Menemukan OTP di Gmail: {angka}")
                        mail.logout()
                        return angka
                        
        mail.logout()
    except Exception as e:
        print(f"Gagal konek server Gmail (Cek Sandi Aplikasi): {e}")
    return None

print("--- MEMULAI BOT TELEGRAM VIA SERVER GMAIL ---")

# ========================================================
# 1. KEMBALI KE BERANDA & BUKA TELEGRAM
# ========================================================
print("Memastikan HP berada di halaman Beranda...")
d.press("home")
time.sleep(2)

if not d(text="Telegram").exists:
    d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.2)
    time.sleep(2)

if d(text="Telegram").exists:
    d(text="Telegram").click()
else:
    os.system("adb shell am start -n org.telegram.messenger/org.telegram.ui.LaunchActivity")
time.sleep(4)

# ========================================================
# 2. HALAMAN AWAL (MULAI PERCAKAPAN)
# ========================================================
if d(text="Mulai Percakapan").exists:
    print("Mengklik 'Mulai Percakapan'...")
    d(text="Mulai Percakapan").click()
    time.sleep(3)

# Bypass izin akses jika muncul
for _ in range(2):
    if d(text="Lanjutkan").exists: d(text="Lanjutkan").click(); time.sleep(1)
    if d(text="Izinkan").exists: d(text="Izinkan").click(); time.sleep(1)

# ========================================================
# 3. INPUT NOMOR HP & KLIK "SELESAI"
# ========================================================
kode_negara = "62"    
sisa_nomor_hp = "85770522217" 

if d(className="android.widget.EditText").exists:
    print("Mengisi data nomor HP...")
    d(className="android.widget.EditText", instance=0).set_text(kode_negara)
    time.sleep(1)
    d(className="android.widget.EditText", instance=1).set_text(sisa_nomor_hp)
    time.sleep(2)
    
    if d(description="Selesai").exists:
        d(description="Selesai").click()
        time.sleep(3)
        
    if d(text="Ya").exists:
        print("Mengklik 'Ya' pada konfirmasi...")
        d(text="Ya").click()
        time.sleep(4)
else:
    print("Kolom input nomor HP tidak ditemukan.")
    exit()

# ========================================================
# # 4. INPUT EMAIL OTOMATIS (VERSI AMAN & ANTI-TIMPA)
# ========================================================
email_kamu = "bryantdiwasanta2020@gmail.com"

print("\n[PROSES] Menunggu layar pengisian Email siap...")
time.sleep(4) # Beri jeda pasti agar layar nomor HP benar-benar hilang dan berganti ke layar email

if d(className="android.widget.EditText").exists:
    print("Membersihkan kolom sebelum mengetik email...")
    d(className="android.widget.EditText").clear_text() # Hapus sisa nomor HP jika masih nempel
    time.sleep(1)
    
    print(f"Mengetik email: {email_kamu}...")
    d(className="android.widget.EditText").set_text(email_kamu)
    time.sleep(2)
    
    # Klik selesai untuk submit email
    if d(description="Selesai").exists:
        print("Mengklik tombol 'Selesai' untuk kirim email...")
        d(description="Selesai").click()
    else:
        print("Tombol Selesai tidak ada, menekan tombol Enter keyboard...")
        d.press("enter")
        
    print("Email berhasil dikirim ke server Telegram. Menunggu halaman OTP...")
    time.sleep(5)

# ========================================================
# 5. TAHAP AUTOMATIC OTP (MENGGUNAKAN UIAUTOMATOR2 - ANTI ADB ERROR)
# ========================================================
if d(className="android.widget.EditText").exists or d(className="android.view.ViewGroup").exists:
    print("\n[PROSES] Kolom OTP terdeteksi aktif!")
    print("[PROSES] Memulai pencarian OTP langsung ke server Gmail (Looping)...")
    
    otp_terdeteksi = None
    for i in range(10): 
        otp_terdeteksi = ambil_otp_dari_server_gmail()
        if otp_terdeteksi:
            break
        print("OTP belum masuk ke inbox server, mengecek lagi dalam 5 detik...")
        time.sleep(5)
        
    if otp_terdeteksi:
        print(f"Mengisi OTP {otp_terdeteksi} otomatis via UiAutomator2...")
        
        # Siasat klik tengah layar dulu agar kolom inputnya fokus
        d.click(0.5, 0.4)
        time.sleep(1)
        
        # KETIK OTP MENGGUNAKAN JALUR SAKTI UIAUTOMATOR2 (Tembus proteksi tanpa ADB Windows)
        d.send_keys(otp_terdeteksi)
        time.sleep(3)

        # Klik selesai terakhir untuk konfirmasi masuk dashboard chat
        if d(description="Selesai").exists:
            d(description="Selesai").click()
        else:
            d.press("enter")
        time.sleep(5)
        print(" BERHASIL TOTAL! Cek HP-mu, bot login sukses 100% tanpa kendala ADB!")
    else:
        print(" Gagal mendapatkan OTP dari server Gmail setelah 50 detik.")
else:
    print("Halaman pengisian OTP tidak terdeteksi.")

print("Selesai")