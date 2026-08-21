import uiautomator2 as u2
import time
import subprocess  # Library tangguh untuk bypass command ADB di Windows
from google import genai  # Jalur resmi library terbaru masa kini!

# ========================================================
#  CONFIG USERNAME INSTAGRAM (SESUAI DATA DUMP KAMU)
# ========================================================
USERNAME_AKUN_1 = "lukidiwa13"   
USERNAME_AKUN_2 = "leopard09881" 

# ========================================================
#  KUNCI AKSES GOOGLE AI STUDIO
# ========================================================
API_KEY_GEMINI = "AQ.Ab8RN6KaO3OUWVhKi7YTzu9gWMw-2nLiFwWhZXLqVK7iahH4_g"
ADB_PATH = r"C:\platform-tools-latest-windows\platform-tools\adb.exe"

client = genai.Client(
    api_key=API_KEY_GEMINI,
    http_options={'api_version': 'v1'} 
)

TOTAL_RONDE = 5 
PESAN_MEMULAI = "Halo bro! Balapan mobil yuk!!"

def tanya_ai_gemini(pesan_user, role_sekarang):
    """Fungsi AI menggunakan SDK google-genai terbaru dengan penanganan error"""
    try:
        print(f" [Google AI Studio] Sedang menyusun balasan untuk {role_sekarang}...")
        prompt = (
            f"Kamu adalah anak muda Indonesia yang sedang chatting santai dan seru dengan teman dekat di DM Instagram.\n"
            f"Saat ini kamu sedang memegang akun: {role_sekarang}.\n"
            f"Tugasmu: Balas pesan di bawah ini dengan gaya gaul, sangat natural, dan nyambung. "
            f"Berikan respons terhadap apa yang dia katakan, lalu cobalah untuk bertanya balik "
            f"supaya terjadi pertukaran informasi yang seru!\n"
            f"Aturan: Maksimal 2 kalimat pendek saja. Jangan kaku seperti robot.\n\n"
            f"Pesan temanmu: '{pesan_user}'"
        )
        response = client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f" API Google Error: {e}")
        return "Maaf sedang sibuk"

# ========================================================
#  LOOPING UTAMA AUTOMATION (SINKRON BOLAK-BALIK)
# ========================================================
print("Menghubungkan ke HP Android via UiAutomator2...")
d = u2.connect()

print("\n PASTIKAN: HP terhubung dan posisi awal ada di DALAM ROOM CHAT!")
print("Memulai simulasi dalam 3 detik...")
time.sleep(3)   

# Set awal bot berjalan menggunakan Akun 1
akun_sekarang = USERNAME_AKUN_1
pesan_terakhir_di_sistem = PESAN_MEMULAI

for ronde in range(1, TOTAL_RONDE + 1):
    print(f"\n========================================================")
    print(f"   RONDE KE-{ronde} | GILIRAN AKUN: {akun_sekarang}")
    print(f"========================================================")

    # --- STEP 1: SCREENSHOT ANTI-GELAP (BUAT LAPORAN MAGANG) ---
    time.sleep(1) 
    nama_file_ss = f"screenshot_ronde_{ronde}_{akun_sekarang}.png"
    subprocess.run([ADB_PATH, "shell", "screencap", "-p", f"/sdcard/{nama_file_ss}"], stdout=subprocess.DEVNULL)
    subprocess.run([ADB_PATH, "pull", f"/sdcard/{nama_file_ss}", f"C:\\Magang\\{nama_file_ss}"], stdout=subprocess.DEVNULL)
    print(f" Screenshot sukses ditarik ke C:\\Magang\\{nama_file_ss}")

    # --- STEP 2: BACA CHAT TERAKHIR YANG MASUK DI LAYAR ---
    baca_sukses = False
    try:
        elements = d(className="android.widget.TextView")
        if elements.exists and len(elements) > 0:
            for i in range(len(elements) - 1, -1, -1):
                txt = elements[i].get_text()
                if txt and len(txt) < 100 and ":" not in txt and txt != "Sedang Aktif" and txt != "Dilihat":
                    pesan_masuk = txt
                    break
            
            if pesan_masuk and pesan_masuk != pesan_terakhir_di_sistem:
                pesan_terakhir_di_sistem = pesan_masuk
                baca_sukses = True
                print(f" Chat terakhir terbaca di layar: '{pesan_terakhir_di_sistem}'")
    except Exception:
        baca_sukses = False

    if not baca_sukses:
        print(" [MEMORI] Mengalirkan obrolan berdasarkan sirkulasi pesan terakhir...")

    # --- STEP 3: KONSULTASI KE AI GEMINI ---
    BALASAN_PESAN = tanya_ai_gemini(pesan_terakhir_di_sistem, akun_sekarang)
    pesan_terakhir_di_sistem = BALASAN_PESAN

    # --- STEP 4: KETIK CHAT (KOORDINAT DUMP KAMU) ---
    print(f" Akun {akun_sekarang} mengetik: '{BALASAN_PESAN}'")
    d.click(0.3, 0.849)  # Titik kolom ketik teks
    time.sleep(0.5)
    d.send_keys(BALASAN_PESAN)
    time.sleep(1)

    # --- STEP 5: TOMBOL KIRIM CHAT (KOORDINAT DUMP KAMU) ---
    print(" Mengirim pesan...")
    d.click(0.886, 0.9)  # Titik ikon pesawat kertas biru
    time.sleep(3)
    
    # --- STEP 6: KELUAR DARI ROOM CHAT ---
    print(" Keluar ke halaman list DM...")
    d.press("back")
    time.sleep(2)

    # --- STEP 7: GANTI PROFIL / AKUN (MENU ATAS DM - KOORDINAT DUMP KAMU) ---
    print(f" Mengetuk nama atas (0.536, 0.05) untuk memicu menu ganti akun...")
    d.click(0.536, 0.05)
    time.sleep(2.5) # Tunggu pop-up dari bawah muncul sempurna
    
    # Menentukan target akun berikutnya
    akun_target = USERNAME_AKUN_2 if akun_sekarang == USERNAME_AKUN_1 else USERNAME_AKUN_1
    print(f" Memilih akun target di pop-up: '{akun_target}'")
    
    # Klik berdasarkan posisi akun yang dituju
    if akun_target == "leopard09881":
        d.click(0.395, 0.608)  # Klik baris leopard
    else:
        d.click(0.395, 0.52)   # Klik baris lukidiwa (posisi atasnya)
        
    # Update status akun yang sekarang aktif setelah di-klik
    akun_sekarang = akun_target
    print(f" Berhasil ganti session! Sekarang menggunakan akun: {akun_sekarang}")
    time.sleep(6)  # Jeda loading sinkronisasi ganti akun di Instagram Lite

    # --- LANGKAH 8: MASUK ROOM CHAT TERATAS KEMBALI ---
    print(f" Menunggu list DM muncul sempurna untuk akun {akun_sekarang}...")
    time.sleep(5)  # PERPANJANG JEDA: Akun baru butuh waktu buat loading list DM
    
    # Deteksi pengaman: Pastikan sudah di menu DM (bukan Home)
    if not d(descriptionMatches="(?i)(Direct|Pesan|Messenger|Inbox)").exists:
        print(" Mencari icon DM karena belum masuk halaman DM...")
        d.click(0.89, 0.06) # Klik area icon DM di kanan atas
        time.sleep(3)

    print(f"Mengklik baris chat teratas untuk giliran akun {akun_sekarang}...")
    # Klik chat teratas pakai data dump kamu
    d.click(0.459, 0.368) 
    time.sleep(3) # Tunggu sampai benar-benar masuk ke dalam ruang chat
    

print("\n [SELESAI] Bot Chat + Ganti Akun Bolak-balik Berhasil Disinkronkan!")