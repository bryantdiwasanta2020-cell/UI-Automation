import time
import os
import requests
import uiautomator2 as u2

# ==============================================================================
# CONFIG CONFIGURATION FOR TELEGRAM SOLVER (OPTION 4)
# ==============================================================================
# Isi token bot Telegram dan chat ID Anda di sini jika ingin menggunakan Option 4.
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

# ==============================================================================
# HELPER: DETEKSI LAYAR RECAPTCHA
# ==============================================================================
def check_recaptcha_screen(d):
    """
    Mengecek apakah layar saat ini menampilkan tantangan reCAPTCHA / hCaptcha.
    """
    try:
        xml_src = d.dump_hierarchy()
        xml_lower = xml_src.lower()
    except Exception as e:
        print(f"[RECAPTCHA] Gagal mengambil layout layar: {e}")
        return False
        
    # Kata kunci umum yang muncul pada layar reCAPTCHA / hCaptcha gambar
    captcha_keywords = [
        "select all images", 
        "pilih semua gambar", 
        "i'm not a robot", 
        "saya bukan robot",
        "recaptcha", 
        "hcaptcha",
        "verify you are a human",
        "verifikasi bahwa anda adalah manusia"
    ]
    
    is_detected = any(kw in xml_lower for kw in captcha_keywords)
    return is_detected


# ==============================================================================
# CARA 1: SEMI-MANUAL (JEDA & DETEKSI OTOMATIS)
# ==============================================================================
def handle_recaptcha_semi_manual(d, timeout_seconds=180):
    """
    Metode 1: Menunda eksekusi bot dan menunggu Anda menyelesaikan reCAPTCHA
    secara manual (bisa langsung di layar HP atau menggunakan tool mirroring seperti scrcpy).
    """
    print("\n[⚠️ RECAPTCHA DETECTED] Layar verifikasi memilih gambar reCAPTCHA terdeteksi!")
    print("[⚠️ ACTION REQUIRED] Silakan selesaikan tantangan reCAPTCHA tersebut di HP Anda / via scrcpy.")
    print(f"Bot akan menjeda eksekusi dan memantau status setiap 5 detik (Timeout: {timeout_seconds}s)...")
    
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        # Cek apakah layar reCAPTCHA sudah selesai
        if not check_recaptcha_screen(d):
            print("[✅ SOLVED] reCAPTCHA telah diselesaikan! Melanjutkan proses login...")
            return True
            
        elapsed = int(time.time() - start_time)
        print(f"   -> Menunggu verifikasi manual selesai... ({elapsed}s/{timeout_seconds}s)")
        time.sleep(5.0)
        
    print("[❌ TIMEOUT] Batas waktu penyelesaian manual terlampaui.")
    return False


# ==============================================================================
# CARA 4: REMOTE SOLVER VIA BOT TELEGRAM (INTERAKTIF)
# ==============================================================================
def handle_recaptcha_via_telegram(d, device_id, username, timeout_seconds=300):
    """
    Metode 4: Mengambil screenshot layar HP, mengirimkannya ke bot Telegram Anda,
    dan menunggu Anda mengirim perintah koordinat klik dari HP pribadi Anda.
    
    Perintah di Telegram:
    - /click <x_percentage> <y_percentage>  -> Mengklik titik koordinat di layar HP.
                                               Contoh: /click 0.5 0.65
    - /continue                              -> Klik tombol verifikasi/selanjutnya.
    - /skip                                  -> Lewati tantangan (batal).
    """
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or TELEGRAM_CHAT_ID == "YOUR_TELEGRAM_CHAT_ID":
        print("[ERROR] Token Telegram belum dikonfigurasi di file ini. Silakan isi terlebih dahulu.")
        return False

    print("\n[⚠️ RECAPTCHA DETECTED] Layar reCAPTCHA terdeteksi!")
    print("[TELEGRAM] Mengirim screenshot layar HP ke Telegram...")
    
    # Ambil screenshot HP dan simpan sementara
    screenshot_path = f"captcha_{device_id}_{username}.png"
    try:
        d.screenshot(screenshot_path)
    except Exception as e:
        print(f"[ERROR] Gagal mengambil screenshot HP: {e}")
        return False
        
    # Kirim foto ke Telegram
    caption = (
        f"🚨 *TANTANGAN CAPTCHA DETECTED!*\n"
        f"📱 Device: `{device_id}`\n"
        f"👤 Akun: `{username}`\n\n"
        f"Ketik balasan untuk berinteraksi:\n"
        f"• `/click <x_persen> <y_persen>` (contoh: `/click 0.5 0.65` untuk klik tengah)\n"
        f"• `/continue` (untuk klik tombol verifikasi di HP)\n"
        f"• `/skip` (untuk membatalkan/skip)"
    )
    
    send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(screenshot_path, "rb") as photo:
            r = requests.post(send_url, files={"photo": photo}, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"})
            print(f"      -> Screenshot terkirim. Status API: {r.status_code}")
    except Exception as e:
        print(f"[ERROR] Gagal mengirim screenshot ke Telegram: {e}")
        return False
    finally:
        # Hapus file screenshot lokal agar bersih
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

    # Loop polling untuk membaca pesan balasan dari Telegram
    start_time = time.time()
    last_update_id = None
    width, height = d.window_size()
    
    print("[TELEGRAM] Menunggu perintah balasan dari Telegram...")
    
    while time.time() - start_time < timeout_seconds:
        # Polling pesan masuk Telegram
        updates_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        params = {"timeout": 5, "offset": last_update_id}
        
        try:
            res = requests.get(updates_url, params=params, timeout=10).json()
            results = res.get("result", [])
        except Exception as e:
            print(f"   -> Gagal polling Telegram API: {e}")
            time.sleep(3.0)
            continue
            
        for update in results:
            last_update_id = update["update_id"] + 1
            message = update.get("message", {})
            text = message.get("text", "").strip()
            
            if not text:
                continue
                
            # HANYA PROSES perintah yang diawali dengan slash (/)
            if text.startswith("/click"):
                parts = text.split()
                if len(parts) == 3:
                    try:
                        x_pct = float(parts[1])
                        y_pct = float(parts[2])
                        
                        # Hitung pixel koordinat berdasarkan persentase layar
                        target_x = int(width * x_pct)
                        target_y = int(height * y_pct)
                        
                        print(f"[TELEGRAM] Menerima perintah KLIK pada ({x_pct}, {y_pct}) -> Pixel: ({target_x}, {target_y})")
                        d.click(target_x, target_y)
                        
                        # Ambil screenshot baru dan kirim ulang sebagai konfirmasi
                        time.sleep(2.0)
                        d.screenshot(screenshot_path)
                        with open(screenshot_path, "rb") as photo:
                            requests.post(send_url, files={"photo": photo}, data={"chat_id": TELEGRAM_CHAT_ID, "caption": f"Status setelah klik ({x_pct}, {y_pct})"})
                        if os.path.exists(screenshot_path):
                            os.remove(screenshot_path)
                            
                    except Exception as e:
                        print(f"   -> Gagal memproses koordinat klik: {e}")
                        
            elif text.startswith("/continue") or text.startswith("/done"):
                print("[TELEGRAM] Menerima perintah CONTINUE. Mengklik tombol verifikasi...")
                
                # Klik tombol verifikasi (Continue/Verify)
                clicked = False
                for label in ["Verify", "Verifikasi", "Continue", "Lanjutkan"]:
                    btn = d(text=label) or d(description=label)
                    if btn.exists:
                        btn.click()
                        clicked = True
                        break
                
                # Fallback koordinat tombol verify (biasanya di kanan bawah frame recaptcha)
                if not clicked:
                    d.click(int(width * 0.5), int(height * 0.85))
                    
                time.sleep(5.0)
                
                # Cek apakah Captcha sudah hilang
                if not check_recaptcha_screen(d):
                    print("[✅ SOLVED] reCAPTCHA selesai via Telegram!")
                    return True
                else:
                    # Kirim screenshot baru jika verifikasi masih gagal
                    d.screenshot(screenshot_path)
                    with open(screenshot_path, "rb") as photo:
                        requests.post(send_url, files={"photo": photo}, data={"chat_id": TELEGRAM_CHAT_ID, "caption": "Verifikasi gagal atau muncul Captcha baru. Silakan klik ulang."})
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                        
            elif text.startswith("/skip"):
                print("[TELEGRAM] Menerima perintah SKIP. Melewati tantangan.")
                return False
                
        time.sleep(2.0)
        
    print("[❌ TIMEOUT] Batas waktu polling Telegram terlampaui.")
    return False


# ==============================================================================
# MAIN TEST SCRIPT
# ==============================================================================
if __name__ == "__main__":
    # Ganti dengan device ID Anda saat melakukan testing
    TEST_DEVICE_ID = "R9RYA030KWX"
    TEST_USERNAME = "keysaputri12131"
    
    print(f"Menghubungkan ke device: {TEST_DEVICE_ID}...")
    try:
        d = u2.connect(TEST_DEVICE_ID)
    except Exception as e:
        print(f"Gagal koneksi ke HP: {e}")
        exit(1)
        
    print("Mengecek apakah sedang ada layar reCAPTCHA di HP...")
    if check_recaptcha_screen(d):
        # Jalankan Cara 1 (Semi-Manual)
        handle_recaptcha_semi_manual(d)
        
        # ATAU Jalankan Cara 4 (Telegram) jika token sudah diisi:
        # handle_recaptcha_via_telegram(d, TEST_DEVICE_ID, TEST_USERNAME)
    else:
        print("Layar reCAPTCHA tidak terdeteksi saat ini di HP.")
