import uiautomator2 as u2
import time
from google import genai  # Jalur resmi library terbaru masa kini!

# ========================================================
#  KUNCI AKSES GOOGLE AI STUDIO (Sesuai gambar kamu)
# ========================================================
API_KEY_GEMINI = "AQ.Ab8RN6KaO3OUWVhKi7YTzu9gWMw-2nLiFwWhZXLqVK7iahH4_g"

client = genai.Client(
    api_key=API_KEY_GEMINI,
    http_options={'api_version': 'v1'} # Memaksa sistem pakai jalur resmi v1 (Bypass 404)
)

# ========================================================
# 🧠 FUNGSI AI RESMI (GEMINI 1.5/2.5 FLASH)
# ========================================================
def buat_sambutan_gemini():
    """Fungsi AI untuk menyusun pesan pembuka/sambutan secara acak & kreatif menggunakan SDK google-genai terbaru"""
    try:
        print(" [Google AI Studio] Sedang menyusun pesan pembuka secara mandiri...")
        
        prompt = (
            "Kamu adalah anak muda Indonesia yang sedang ingin memulai chat santai dan seru dengan teman dekat di DM Instagram.\n"
            "Tugasmu: Buatkan pesan pembuka/sambutan/sapaan pertama (ice breaker) yang seru, asyik, dan santai agar temanmu tertarik membalas.\n"
            "Gaya bahasa: Sangat gaul, santai, natural, kocak, dan asyik seperti chat antar teman dekat (misal menanyakan kabar dengan cara unik, mengajak main game/nongkrong, atau melempar topik seru secara acak).\n"
            "Aturan: Maksimal 2 kalimat pendek saja. Jangan kaku seperti robot, jangan menyapa dengan formal."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f" API Google Error saat membuat sambutan: {e}, memakai default.")
        return "Halo bro! Lagi sibuk gak?"

def tanya_ai_gemini(pesan_user):
    """Fungsi AI menggunakan SDK google-genai terbaru"""
    try:
        print(" [Google AI Studio] Sedang menyusun balasan...")
        
        prompt = (
            f"Kamu adalah anak muda Indonesia yang sedang chatting santai dan seru dengan teman dekat di DM Instagram.\n"
            f"Tugasmu: Balas pesan di bawah ini dengan gaya gaul, sangat natural, dan nyambung. "
            f"Berikan respons terhadap apa yang dia katakan, lalu cobalah untuk bertanya balik "
            f"supaya terjadi pertukaran informasi yang seru dan obrolan tidak mati!\n"
            f"Aturan: Maksimal 2 kalimat pendek saja. Jangan kaku seperti robot.\n\n"
            f"Pesan temanmu: '{pesan_user}'"
        )
        
        # Format panggil model di library baru
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f" API Google Error: {e}, memakai fail-safe.")
        return "Maaf sedang sibuk"

# ========================================================
# ⚙️ CONFIG SIMULASI NGOBROL
# ========================================================
TOTAL_RONDE = 5 
PESAN_MEMULAI = buat_sambutan_gemini()
print(f" [Greeting Generated] Pesan pembuka: '{PESAN_MEMULAI}'")

# ========================================================
#  LOOPING UTAMA AUTOMATION
# ========================================================
print("Menghubungkan ke HP Android via UiAutomator2...")
d = u2.connect()

print("\n PASTIKAN: Layar HP sudah stand-by di dalam room chat!")
print("Memulai simulasi dalam 3 detik...")
time.sleep(3)

pesan_terakhir_di_sistem = PESAN_MEMULAI

for ronde in range(1, TOTAL_RONDE + 1):
    print(f"\n========================================================")
    print(f"   RONDE PERCAKAPAN KE-{ronde} (OFFICIAL NEW GENAI)")
    print(f"========================================================")

    # --- LANGKAH 1: MEMBACA CHAT TERAKHIR ---
    baca_sukses = False
    try:
        elements = d(className="android.widget.TextView", resourceIdMatches=".*message_container_text.*")
        if elements.exists and len(elements) > 0:
            pesan_masuk = elements[-1].get_text()
            if pesan_masuk and pesan_masuk != pesan_terakhir_di_sistem:
                pesan_terakhir_di_sistem = pesan_masuk
                baca_sukses = True
                print(f" [XML SUCCESS] Terbaca: '{pesan_terakhir_di_sistem}'")
    except Exception:
        baca_sukses = False

    if not baca_sukses:
        print(" [BYPASS MEMORI] Mengalirkan obrolan berdasarkan memori sirkulasi chat...")

    # --- LANGKAH 2: KONSULTASI KE GOOGLE AI ---
    BALASAN_PESAN = tanya_ai_gemini(pesan_terakhir_di_sistem)
    pesan_terakhir_di_sistem = BALASAN_PESAN

    # --- LANGKAH 3: KETIK & KIRIM PESAN ---
    print(f" Mengetik balasan: '{BALASAN_PESAN}'")
    d.click(0.259, 0.906)  
    time.sleep(0.5)
    d.send_keys(BALASAN_PESAN)
    time.sleep(1)

    print(" Mengirim pesan...")
    if d(resourceId="com.instagram.android:id/row_thread_composer_send_button_container").exists:
        d(resourceId="com.instagram.android:id/row_thread_composer_send_button_container").click()
    else:
        d.click(0.89, 0.89)
    
    time.sleep(3)

    # --- LANGKAH 4: KELUAR ---
    d.press("back")
    time.sleep(1.5)

    # --- LANGKAH 5: SWITCH AKUN ---
    d.double_click(0.89, 0.94)
    time.sleep(5)

    # --- LANGKAH 6: NAVIGASI MASUK DM ---
    d.click(0.495, 0.914)
    time.sleep(3)
    d.click(0.6, 0.429)
    time.sleep(3)

print("\n [SELESAI] Percakapan via Jalur Resmi Google GenAI Sukses!")