import uiautomator2 as u2
import time


# CONFIG DAFTAR AKUN BARU (CUMA 1 AKUN TAMBAHAN)

# Akun utama (lukyytris13) tidak perlu dimasukkan karena posisinya sudah login di HP.
DAFTAR_AKUN_BARU = [
    {"user": "leopard09881", "pass": "Bren_123"}
]

print("Menghubungkan ke HP Android via UiAutomator2...")
d = u2.connect()

# ========================================================
# TAHAP 1: BUKA INSTAGRAM DAN MASUK KE SETELAN
# ========================================================
print("\n--- TAHAP 1: BUKA INSTAGRAM ---")
d.press("home")
time.sleep(1.5)
d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.2)
time.sleep(3)

if d(text="Instagram").exists:
    d(text="Instagram").click()
else:
    d.swipe(0.8, 0.5, 0.2, 0.5, duration=0.2)
    time.sleep(1)
    d(text="Instagram").click()

print("Menunggu Instagram terbuka dan loading beranda...")
time.sleep(6)

#  KALIBRASI BRYANT 1: Klik Profil setelah landing page utama
print(" [KLIK] Menuju halaman Profil (Kanan Bawah)...")
d.click(0.904, 0.914) 
time.sleep(4)

#  KALIBRASI BRYANT 2: Klik Opsi untuk melihat setelan
print(" [KLIK] Membuka menu Opsi/Setelan (Kanan Atas)...")
if d(description="Opsi").exists:
    d(description="Opsi").click()
else:
    d.click(0.918, 0.063) 
time.sleep(4)


# ========================================================
# TAHAP 2: PROSES MENAMBAHKAN AKUN KEDUA
# ========================================================
for index, akun in enumerate(DAFTAR_AKUN_BARU, start=1):
    USER_AKUN = akun["user"]
    PASSWORD_AKUN = akun["pass"]
    
    print(f"\n ========================================================")
    print(f"        PROSES TAMBAH AKUN: {USER_AKUN}")
    print(f"======================================================== ")

    # 1. Scroll ke paling bawah untuk cari "Tambahkan Akun"
    print(" Scroll ke bawah mencari menu 'Tambahkan Akun'...")
    for _ in range(10): 
        if d(text="Tambahkan akun").exists or d(text="Tambahkan Akun").exists:
            print("   Menu 'Tambahkan akun' sudah terlihat, berhenti scroll.")
            break
        d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.3)
        time.sleep(1)
        
    # 2. Klik Tombol Tambahkan Akun
    print(" Klik opsi 'Tambahkan Akun'...")
    if d(text="Tambahkan akun").exists:
        d(text="Tambahkan akun").click()
    else:
        print("   Mengeklik menggunakan koordinat kalibrasi (0.218, 0.881)...")
        d.click(0.218, 0.881) 
    time.sleep(4)

    # 3. Pilih "Log in ke akun yang sudah ada"
    print(" Pilih 'Log in ke akun yang sudah ada'...")
    if d(description="Login ke akun yang sudah ada").exists:
        print("   Ketemu berdasarkan Deskripsi! Klik...")
        d(description="Login ke akun yang sudah ada").click()
    elif d(text="Log in ke akun yang sudah ada").exists:
        print("   Ketemu berdasarkan Teks! Klik...")
        d(text="Log in ke akun yang sudah ada").click()
    else:
        print("   Menembak area tombol via koordinat (0.831, 0.824)...")
        d.click(0.831, 0.824) 
    time.sleep(5)

    # 4. Klik Tombol Lanjut di halaman Modal
    print(" Menghadapi halaman konfirmasi, mengklik 'Lanjut'...")
    if d(description="Lanjut").exists:
        print("   Ketemu tombol Lanjut berdasarkan deskripsi! Klik...")
        d(description="Lanjut").click()
    elif d(text="Lanjut").exists:
        d(text="Lanjut").click()
    else:
        print("   Menembak tombol Lanjut via koordinat (0.627, 0.578)...")
        d.click(0.627, 0.578)
    time.sleep(5) 

    # 5. Mulai Input Kredensial Akun Baru (Langsung Tembak Kata Sandi)
    print(" Menghalau Google Credential Manager jika muncul...")
    if d(text="Batal").exists: d(text="Batal").click()
    time.sleep(2)

    print(" Mengetik Kata Sandi Baru...")
    if d(description="Kata sandi,").exists:
        print("   Kolom kata sandi terdeteksi via deskripsi! Mengisi password...")
        d(description="Kata sandi,").set_text(PASSWORD_AKUN)
    else:
        print("   Menembak kolom kata sandi via koordinat (0.59, 0.358)...")
        d.click(0.59, 0.358)
        time.sleep(1)
        d.send_keys(PASSWORD_AKUN)
    time.sleep(2)

    print("Menurunkan keyboard...")
    d.press("back")
    time.sleep(1.5)

    # 6. Klik Tombol Login Biru di ModalActivity
    print(" Mengklik tombol 'Login' di halaman Modal...")
    if d(description="Login").exists:
        print("   Tombol Login terdeteksi via deskripsi! Klik...")
        d(description="Login").click()
    elif d(text="Login").exists:
        d(text="Login").click()
    else:
        print("   Menembak tombol Login via koordinat (0.627, 0.441)...")
        d.click(0.627, 0.441)
    time.sleep(10) 

    # 6.5. Tangani Google Credential Manager (Simpan Sandi ke Google) jika muncul setelah Login
    print(" Menghalau Google Credential Manager setelah login...")
    if d(text="Simpan sandi ke Google?").exists or d(text="Save password to Google?").exists or d(text="Simpan sandi?").exists:
        print("   Terdeteksi popup Google Password Manager.")
        if d(text="Batal").exists:
            d(text="Batal").click()
        elif d(text="Lain kali").exists:
            d(text="Lain kali").click()
        elif d(text="Tidak").exists:
            d(text="Tidak").click()
        else:
            d.press("back")
        time.sleep(2)
    elif d(text="Batal").exists:
        print("   Terdeteksi tombol 'Batal' sistem/Google, mengklik...")
        d(text="Batal").click()
        time.sleep(2)

    # 7. Bersihkan Pop-up pasca login biar balik ke beranda bersih
    if d(description="Lain Kali").exists: d(description="Lain Kali").click()
    time.sleep(3)
    if d(description="Paham").exists: d(description="Paham").click()
    time.sleep(2)

    print(f" Akun {USER_AKUN} BERHASIL DITAMBAHKAN SEBAGAI AKUN KEDUA!")

# ========================================================
#  TAHAP 3: OTOMATIS SWAP BALIK KE AKUN PERTAMA
# ========================================================
print("\n --- TAHAP 3: PROSES PINDAH KEMBALI KE AKUN UTAMA ---")
time.sleep(3)

print(" Mengklik tombol Profil (Kanan Bawah)...")
d.click(0.904, 0.914) 
time.sleep(4)

print(" Mengklik Nama Pengguna di pojok kiri atas...")
d.click(0.25, 0.06) 
time.sleep(4)

print(" Memilih dan mengklik akun utama 'lukyytris13'...")
if d(text="lukyytris13").exists:
    d(text="lukyytris13").click()
else:
    # Koordinat cadangan pop-up bawah untuk akun pertama
    d.click(0.5, 0.78) 

time.sleep(6)
print("\n ========================================================")
print(" [GRAND MISSION ACCOMPLISHED] LOGIN DAN SWITCH SELESAI DLM 1 FILE!")
print("======================================================== \n")