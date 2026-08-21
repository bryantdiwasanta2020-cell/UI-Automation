import uiautomator2 as u2
import time
from google import genai

# ========================================================
#  KUNCI AKSES GOOGLE AI STUDIO
# ========================================================
API_KEY_GEMINI = "AQ.Ab8RN6KaO3OUWVhKi7YTzu9gWMw-2nLiFwWhZXLqVK7iahH4_g"
client = genai.Client(
    api_key=API_KEY_GEMINI,
    http_options={'api_version': 'v1'}
)

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

# ========================================================
#  CONFIG DATA TARGET & MEDIA
# ========================================================
USERNAME_TARGET = "neymarjr"  # Ganti dengan username target dari mentor
PESAN_DM        = buat_sambutan_gemini()
print(f" [Greeting Generated] Pesan pembuka: '{PESAN_DM}'")

print("Menghubungkan ke HP Android via UiAutomator2...")
d = u2.connect()

# ========================================================
#  HELPER FUNCTION (DATA INSPECT TOMBOL KEMBALI BRYANT)
# ========================================================
def klik_kembali():
    """Fungsi pengaman menggunakan data inspect tombol kembali Bryant"""
    if d(resourceId="com.instagram.android:id/left_action_bar_buttons").exists:
        print(" Menekan tombol kembali via 'left_action_bar_buttons'...")
        d(resourceId="com.instagram.android:id/left_action_bar_buttons").click()
        time.sleep(2)
        return True
    elif d(resourceId="com.instagram.android:id/action_bar_new_title_container").exists:
        print(" Menekan tombol kembali via 'action_bar_new_title_container'...")
        d(resourceId="com.instagram.android:id/action_bar_new_title_container").click()
        time.sleep(2)
        return True
    else:
        print(" Komponen tidak terlihat, menggunakan back system Android...")
        d.press("back")
        time.sleep(2)
        return True

# ========================================================
# 1. ALUR: HOME PAGE & BUKA IG
# ========================================================
print("\n--- TAHAP 1: HOME PAGE & BUKA INSTAGRAM ---")
d.press("home")
time.sleep(1.5)

# Geser layar jika IG ada di menu aplikasi (swipe up)
d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.2)
time.sleep(2)

if d(text="Instagram").exists:
    d(text="Instagram").click()
else:
    # Swipe ke samping jika belum ketemu
    d.swipe(0.8, 0.5, 0.2, 0.5, duration=0.2)
    time.sleep(1)
    d(text="Instagram").click()

print("Menunggu Instagram terbuka dan stabil...")
time.sleep(5)

# ========================================================
# 2. ALUR: CARI TARGET (SEARCH BAR) - UPDATE FIX BRYANT
# ========================================================
print("\n--- TAHAP 2: MENCARI TARGET ---")

print(" Klik ikon Kaca Pembesar di menu bawah...")
if d(resourceId="com.instagram.android:id/search_tab").exists:
    d(resourceId="com.instagram.android:id/search_tab").click()
else:
    print(" Menembak ikon search via koordinat kalibrasi Bryant (0.704, 0.914)...")
    d.click(0.704, 0.914) 
time.sleep(4)

print(" Memfokuskan kolom Search Bar atas...")
if d(resourceId="com.instagram.android:id/explore_action_bar_container").exists:
    d(resourceId="com.instagram.android:id/explore_action_bar_container").click()
else:
    print(" Menembak bar pencarian via koordinat kalibrasi Bryant (0.286, 0.046)...")
    d.click(0.286, 0.046) 
time.sleep(3)

print(f" Mengetik username target: {USERNAME_TARGET}")
d.send_keys(USERNAME_TARGET)
time.sleep(4)

print(" Mengklik akun teratas hasil pencarian...")
if d(resourceId="com.instagram.android:id/row_search_user_info_container").exists:
    d(resourceId="com.instagram.android:id/row_search_user_info_container").click()
else:
    print(" Menembak baris akun teratas via koordinat kalibrasi Bryant (0.668, 0.244)...")
    d.click(0.668, 0.244) 
time.sleep(6) # Tunggu profil terbuka penuh

# ========================================================
# 3. ALUR: MELAKUKAN FOLLOW
# ========================================================
print("\n--- TAHAP 3: MELAKUKAN FOLLOW ---")
if d(text="Ikuti").exists:
    print(" Menemukan tombol 'Ikuti', langsung klik...")
    d(text="Ikuti").click()
    time.sleep(2.5)
elif d(text="Follow").exists:
    print(" Menemukan tombol 'Follow', langsung klik...")
    d(text="Follow").click()
    time.sleep(2.5)
else:
    print(" Tombol follow tidak terbaca atau sudah di-follow sebelumnya.")

print("\n--- TAHAP 3.5: KEMBALI 2 KALI SESUAI INSTRUKSI ---")
print("↩ Kembali Pertama (Keluar dari Profil Target)...")
klik_kembali()

print("↩ Kembali Kedua (Keluar dari Pencarian ke Halaman Utama)...")
klik_kembali()

# ========================================================
# 4. ALUR: MASUK DM & CARI NAMA (MODAL ACTIVITY)
# ========================================================
print("\n--- TAHAP 4: MASUK MENU PESAN & CARI NAMA TARGET ---")
print(" Mengklik tombol/ikon Pesan...")
if d(resourceId="com.instagram.android:id/direct_tab").child(resourceId="com.instagram.android:id/tab_icon").exists:
    d(resourceId="com.instagram.android:id/direct_tab").child(resourceId="com.instagram.android:id/tab_icon").click()
else:
    print(" Menembak ikon pesan via koordinat inspect Bryant (0.509, 0.914)...")
    d.click(0.509, 0.914)
time.sleep(3)

print(" Membuka kolom Cari Nama untuk di-DM...")
if d(text="Cari").exists:
    d(text="Cari").click()
else:
    print(" Menembak bar text Cari via koordinat inspect Bryant (0.395, 0.126)...")
    d.click(0.395, 0.126)
time.sleep(2)

print(" Memfokuskan kolom input pencarian nama...")
if d(resourceId="com.instagram.android:id/search_bar_field_container").exists:
    d(resourceId="com.instagram.android:id/search_bar_field_container").click()
else:
    print(" Menembak search bar field via koordinat inspect Bryant (0.295, 0.065)...")
    d.click(0.295, 0.065)
time.sleep(2)

print(f" Mengetik ulang nama target untuk membuka chat room: {USERNAME_TARGET}")
if d(className="android.widget.EditText").exists:
    d(className="android.widget.EditText").set_text(USERNAME_TARGET)
else:
    d.send_keys(USERNAME_TARGET)
time.sleep(4)

# FIX BRYANT: Menggunakan d.xpath().exists yang benar agar tidak error ReferenceError
print(" Mengklik akun teratas dari hasil pencarian Grid...")
if d.xpath("//android.widget.GridView/android.widget.LinearLayout[1]/android.widget.LinearLayout[1]").exists:
    print(" Menembak via XPath GridView (Syntax Fix)...")
    d.xpath("//android.widget.GridView/android.widget.LinearLayout[1]/android.widget.LinearLayout[1]").click()
elif d(resourceId="com.instagram.android:id/row_search_user_info_container").exists:
    print(" Menembak via resourceId container...")
    d(resourceId="com.instagram.android:id/row_search_user_info_container").click()
else:
    # KALIBRASI ULANG: Menembak area tengah baris teks nama, bukan pojok kanan luar (0.89)
    print(" Mencoba klik area tengah hasil pencarian via koordinat kalibrasi (0.550, 0.132)...")
    d.click(0.550, 0.132)
    time.sleep(1.5)
    
    # Jika belum masuk room chat, tembak koordinat pojok kanan pilihanmu sebagai pertahanan terakhir
    if not d(resourceId="com.instagram.android:id/composer_content_container").exists:
        print(" Belum masuk room chat, menembak koordinat cadangan Bryant (0.89, 0.132)...")
        d.click(0.89, 0.132)

time.sleep(5)  # Tunggu chat room terbuka penuh

# ========================================================
# 5. ALUR: KIRIM PESAN TEKS & MEDIA 
# ========================================================
print("\n--- TAHAP 5: KIRIM PESAN DM ---")
print(" Mengklik kolom input chat...")
if d(resourceId="com.instagram.android:id/composer_content_container").exists:
    d(resourceId="com.instagram.android:id/composer_content_container").click()
else:
    print(" Menembak area kolom pesan via koordinat inspect Bryant (0.109, 0.9)...")
    d.click(0.109, 0.9)
time.sleep(2)

print(f" Mengetik teks: '{PESAN_DM}'")
d.send_keys(PESAN_DM)
time.sleep(2)

print(" Klik tombol Kirim Pesan...")
if d(resourceId="com.instagram.android:id/row_thread_composer_send_button_icon").exists:
    d(resourceId="com.instagram.android:id/row_thread_composer_send_button_icon").click()
else:
    print(" Menembak tombol kirim via koordinat inspect Bryant (0.89, 0.9)...")
    d.click(0.89, 0.9)
time.sleep(3)

# ========================================================
# 6. ALUR: KIRIM GAMBAR / VIDEO DARI GALERI
# ========================================================
print("\n--- TAHAP 6: KIRIM GAMBAR DARI GALERI ---")
print(" Mencari ikon Galeri/Kamera di sebelah kolom chat...")
if d(resourceId="com.instagram.android:id/row_feed_comment_msgr_camera_button").exists:
    d(resourceId="com.instagram.android:id/row_feed_comment_msgr_camera_button").click()
else:
    d.click(0.785, 0.945) 
time.sleep(3)

# Proteksi Pop-up Izin Akses Media Android
if d(textContains="Izinkan").exists or d(textContains="Allow").exists or d(textContains="saat aplikasinya digunakan").exists:
    print("Pop-up Izin Akses Media terdeteksi! Klik Izinkan...")
    if d(textContains="Izinkan").exists:
        d(textContains="Izinkan").click()
    elif d(textContains="saat aplikasinya digunakan").exists:
        d(textContains="saat aplikasinya digunakan").click()
    else:
        d(textContains="Allow").click()
    time.sleep(3)

print(" Memilih gambar/video pertama di galeri...")
d.click(0.165, 0.755) 
time.sleep(3) 

print(" Mengklik tombol Kirim Media (Panah Biru)...")
if d(description="Kirim").exists:
    d(description="Kirim").click()
elif d(text="Kirim").exists:
    d(text="Kirim").click()
else:
    d.click(0.905, 0.850) 
time.sleep(5)

# --- Reset posisi untuk target berikutnya ---
print(" Mengembalikan posisi bot ke menu utama...")
klik_kembali()

print("\n ========================================================")
print(" [GRAND GOAL SUCCESS] BOT BERHASIL MENGEKSEKUSI SEMUA ALUR!")
print("   Buka IG -> Cari -> Follow -> Jeda Kembali 2x -> Masuk DM -> Kirim Teks -> Kirim Gambar!")
print("======================================================== \n")