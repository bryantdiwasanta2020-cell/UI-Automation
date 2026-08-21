import uiautomator2 as u2
import time
import g4f

# ========================================================
# ⚙️ CONFIG SIMULASI NGOBROL
# ========================================================
TOTAL_RONDE = 10
PESAN_MEMULAI = "Halo bro! Main bola yuk!!" # Pancingan pertama nyata

# ========================================================
# 🧠 FUNGSI AI (g4f) - PROMPT DIPERKERSET AGAR TUKAR INFORMASI
# ========================================================
def tanya_ai_gemini(pesan_user, riwayat_konteks=""):
    """Fungsi AI yang dipaksa mengalirkan obrolan, bertanya balik, dan tukar informasi"""
    try:
        print(" AI sedang menyusun balasan yang nyambung...")
        prompt = (
            f"Kamu adalah anak muda Indonesia yang sedang chatting santai dan seru dengan teman dekat di DM Instagram.\n"
            f"Tugasmu: Balas pesan di bawah ini dengan gaya gaul, sangat natural, dan nyambung. "
            f"Berikan respons terhadap apa yang dia katakan, lalu cobalah untuk bertanya balik atau membagikan info/cerita pendek "
            f"supaya terjadi pertukaran informasi yang seru dan obrolan tidak mati!\n"
            f"Aturan: Maksimal 2 kalimat pendek saja. Jangan kaku seperti robot.\n\n"
            f"Pesan temanmu: '{pesan_user}'"
        )
        
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[{"role": "user", "content": prompt}],
            timeout=12
        )
        return response.strip()
    except Exception as e:
        print(f" AI Timeout, memakai fail-safe.")
        return None

print("Menghubungkan ke HP Android via UiAutomator2...")
d = u2.connect()

print("\n PASTIKAN: Layar HP sudah stand-by di dalam room chat!")
print("Memulai simulasi dalam 3 detik...")
time.sleep(3)

pesan_terakhir_di_sistem = PESAN_MEMULAI

# ========================================================
#  LOOPING UTAMA (AI VS AI)
# ========================================================
for ronde in range(1, TOTAL_RONDE + 1):
    print(f"\n========================================================")
    print(f"   RONDE PERCAKAPAN KE-{ronde}")
    print(f"========================================================")

    # --- LANGKAH 1: MEMBACA CHAT TERAKHIR DENGAN STRATEGI BARU ---
    print(" Mencoba membaca obrolan terakhir di layar...")
    
    # Taktik 1: Coba baca via elemen XML universal Instagram
    baca_sukses = False
    try:
        elements = d(className="android.widget.TextView", resourceIdMatches=".*message_container_text.*")
        if elements.exists and len(elements) > 0:
            pesan_masuk = elements[-1].get_text()
            # Validasi agar tidak membaca pesan yang baru saja diketik sendiri di ronde yang sama
            if pesan_masuk and pesan_masuk != pesan_terakhir_di_sistem:
                pesan_terakhir_di_sistem = pesan_masuk
                baca_sukses = True
                print(f" [XML SUCCESS] Terbaca: '{pesan_terakhir_di_sistem}'")
    except Exception:
        baca_sukses = False

    # Taktik 2: Jika XML gagal/dikunci, gunakan taktik ingatan rantai obrolan (Bypass)
    if not baca_sukses:
        print(" [BYPASS APRESIASI] XML terkunci, mengalirkan obrolan berdasarkan memori sirkulasi chat...")
        # Bot akan menjawab pesan terakhir yang dikirim oleh bot sebelumnya agar topik tetap nyambung!

    # --- LANGKAH 2: KONSULTASI KE AI ---
    BALASAN_PESAN = tanya_ai_gemini(pesan_terakhir_di_sistem)
    
    if not BALASAN_PESAN:
        BALASAN_PESAN = "Wkwk seru banget asli. Terus gimana kelanjutannya?"

    # Simpan balasan ini sebagai referensi konteks ronde berikutnya jika XML nge-bug lagi
    pesan_terakhir_di_sistem = BALASAN_PESAN

    # --- LANGKAH 3: KETIK & KIRIM PESAN ---
    print(f" Mengetik balasan: '{BALASAN_PESAN}'")
    d.click(0.259, 0.906)  # Koordinat input chat HP kamu
    time.sleep(0.5)
    d.send_keys(BALASAN_PESAN)
    time.sleep(1)

    print(" Mengirim pesan...")
    if d(resourceId="com.instagram.android:id/row_thread_composer_send_button_container").exists:
        d(resourceId="com.instagram.android:id/row_thread_composer_send_button_container").click()
    else:
        d.click(0.89, 0.89)
    
    time.sleep(3)

    # --- LANGKAH 4: KELUAR MENUJU BERANDA ---
    print(" Keluar dari chat menuju Beranda...")
    d.press("back")
    time.sleep(1.5)

    # --- LANGKAH 5: PINDAH AKUN INSTAN ---
    print(" [SWITCH AKUN] Double click ikon profil kanan bawah...")
    d.double_click(0.89, 0.94)
    print(" Menunggu proses perpindahan akun (5 detik)...")
    time.sleep(5)

    # --- LANGKAH 6: NAVIGASI MASUK DM SEUAI SKEMA HP KAMU ---
    print(" Menuju halaman DM/Inbox via direct_tab...")
    d.click(0.495, 0.914)
    time.sleep(3)

    print(" Membuka obrolan teratas di daftar inbox...")
    d.click(0.6, 0.429)
    time.sleep(3)

print("\n [SELESAI] Obrolan dinamis tukar informasi sukses diselesaikan!")