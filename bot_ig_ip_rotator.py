import time
import sys
import uiautomator2 as u2

# ==============================================================================
# HELPER 1: PING KE DNS GOOGLE UNTUK CEK KONEKTIVITAS HP
# ==============================================================================
def ping_device_internet(d):
    """
    Melakukan ping ke DNS Google 8.8.8.8 dari HP untuk mengecek koneksi internet.
    Mengembalikan True jika sukses terhubung, False jika gagal/offline.
    """
    try:
        # Melakukan ping 1 kali dengan batas waktu tunggu 4 detik
        res = d.shell("ping -c 1 -W 4 8.8.8.8", timeout=6)
        return res.exit_code == 0
    except Exception:
        return False


# ==============================================================================
# HELPER 2: MENGAMBIL DAFTAR IP LOCAL INTERFACE (rmnet, wlan, dll.)
# ==============================================================================
def get_device_local_ips(d):
    """
    Mengambil IP address lokal dari setiap interface jaringan di HP (seperti rmnet untuk data seluler, wlan untuk Wi-Fi).
    Ini tidak membutuhkan internet karena membaca langsung konfigurasi jaringan HP.
    """
    try:
        out = d.shell("ip addr show").output
        ips = {}
        current_iface = None
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            # Deteksi baris nama interface: "3: wlan0: ..."
            if ":" in line and line[0].isdigit():
                parts = line.split(":")
                if len(parts) > 1:
                    current_iface = parts[1].strip()
                    ips[current_iface] = []
            # Deteksi baris IP address: "inet 192.168.1.10/24 ..."
            elif line.startswith("inet ") and current_iface:
                parts = line.split()
                if len(parts) > 1:
                    ip_val = parts[1].split("/")[0]
                    # Abaikan localhost loopback
                    if not ip_val.startswith("127.0."):
                        ips[current_iface].append(ip_val)
        # Filter hanya kembalikan interface yang memiliki IP address aktif
        return {k: v for k, v in ips.items() if v}
    except Exception as e:
        print(f"      -> Gagal mengambil IP local interface: {e}")
        return {}


# ==============================================================================
# HELPER 3: MENGAMBIL IP PUBLIK PERANGKAT HP (VIA ADB SHELL)
# ==============================================================================
def get_device_public_ip(d):
    """
    Mengambil IP publik eksternal yang sedang aktif di HP
    dengan mencoba perintah curl/wget ke ifconfig.me dan ipify.org (HTTP & HTTPS).
    """
    # Mencoba beberapa alternatif perintah di shell HP (mencoba HTTP non-secure port 80 jika HTTPS terhalang/tidak disupport wget)
    commands = [
        "curl -s -m 6 http://ifconfig.me",
        "wget -qO- --timeout=6 http://ifconfig.me",
        "curl -s -m 8 http://api.ipify.org",
        "wget -qO- --timeout=8 http://api.ipify.org",
        "curl -s -m 6 https://ifconfig.me",
        "wget -qO- --timeout=6 https://ifconfig.me"
    ]
    
    for cmd in commands:
        try:
            # Menggunakan timeout=10 agar tidak stuck jika resolver DNS hang
            res = d.shell(cmd, timeout=10).output.strip()
            # Validasi hasil IP sederhana (tidak mengandung error dan panjangnya logis)
            if res and "error" not in res.lower() and len(res) < 45:
                return res
        except Exception:
            pass
            
    return "Unknown/Offline"


# ==============================================================================
# UTAMA: ROTASI IP DENGAN TOGGLE AIRPLANE MODE
# ==============================================================================
def rotate_device_ip(d, delay_between=6.0, delay_reconnect=18.0):
    """
    Melakukan toggle Airplane Mode via ADB shell pada HP Android
    untuk mendapatkan IP data seluler baru dari operator (IP Rotation).
    """
    print("\n--- [START] PROSES ROTASI IP ADDRESS ---")
    
    # 1. Cek status internet & IP saat ini sebelum rotasi
    print("[1] Memeriksa status koneksi internet HP sebelum rotasi...")
    is_online_before = ping_device_internet(d)
    print(f"    -> Status Internet: {'ONLINE (Internet Tersambung)' if is_online_before else 'OFFLINE (Internet Terputus)'}")
    
    local_ips_before = get_device_local_ips(d)
    print(f"    -> Local Interface IP: {local_ips_before}")
    
    ip_before = get_device_public_ip(d)
    print(f"    -> IP Saat Ini: {ip_before}")
    
    if not is_online_before:
        print("    [WARNING] HP terdeteksi offline sebelum rotasi dimulai.")

    # Cek apakah sebelumnya Wi-Fi aktif
    was_wifi_active = False
    for k in local_ips_before.keys():
        if "wlan" in k:
            was_wifi_active = True
            break

    # 2. Aktifkan Mode Pesawat (Memutus Koneksi)
    print(f"\n[2] Menyalakan Mode Pesawat (Airplane Mode: ENABLE)...")
    try:
        # Perintah ini bawaan Android 9+ via ADB Shell (Tidak butuh Root)
        d.shell("cmd connectivity airplane-mode enable")
        print(f"    -> Mode Pesawat aktif. Menunggu {delay_between} detik...")
        time.sleep(delay_between)
    except Exception as e:
        print(f"    [ERROR] Gagal menyalakan Mode Pesawat via shell: {e}")
        return False
        
    is_online_during = ping_device_internet(d)
    print(f"    -> Status Internet saat Mode Pesawat: {'ONLINE' if is_online_during else 'OFFLINE (Koneksi Sukses Terputus)'}")

    # 3. Matikan Mode Pesawat (Menghubungkan Kembali)
    print(f"\n[3] Mematikan Mode Pesawat (Airplane Mode: DISABLE)...")
    try:
        d.shell("cmd connectivity airplane-mode disable")
        
        # Paksa aktifkan Wi-Fi agar HP kembali mendapatkan koneksi internet
        print("    -> Mengaktifkan kembali Wi-Fi (svc wifi enable)...")
        d.shell("svc wifi enable")
            
        print(f"    -> Menghubungkan kembali ke jaringan. Menunggu {delay_reconnect} detik...")
        time.sleep(delay_reconnect)
    except Exception as e:
        print(f"    [ERROR] Gagal mematikan Mode Pesawat via shell: {e}")
        return False

    # 4. Cek IP baru setelah rotasi
    print("\n[4] Memeriksa status koneksi internet HP setelah rotasi...")
    is_online_after = ping_device_internet(d)
    print(f"    -> Status Internet: {'ONLINE (Koneksi Berhasil Pulih)' if is_online_after else 'OFFLINE'}")
    
    local_ips_after = get_device_local_ips(d)
    print(f"    -> Local Interface IP Baru: {local_ips_after}")
    
    ip_after = get_device_public_ip(d)
    print(f"    -> IP Publik Baru: {ip_after}")

    # 5. Evaluasi Hasil
    # Cek apakah terjadi pemutusan dan pemulihan koneksi
    rotation_worked = not is_online_during and is_online_after
    
    # Bandingkan local IP pada interface data seluler (rmnet, ccmni, dsb. yang bukan wlan/lo/p2p)
    mobile_iface_before = {k: v for k, v in local_ips_before.items() if "wlan" not in k and "p2p" not in k and "lo" not in k}
    mobile_iface_after = {k: v for k, v in local_ips_after.items() if "wlan" not in k and "p2p" not in k and "lo" not in k}
    
    ip_changed = False
    if mobile_iface_before and mobile_iface_after:
        first_iface_b = list(mobile_iface_before.keys())[0]
        first_iface_a = list(mobile_iface_after.keys())[0]
        if mobile_iface_before[first_iface_b] != mobile_iface_after[first_iface_a]:
            ip_changed = True
            print(f"\n[✅ SUCCESS] Local IP Data Seluler sukses diputar dari {mobile_iface_before[first_iface_b]} -> {mobile_iface_after[first_iface_a]}!")

    if ip_after != "Unknown/Offline" and ip_before != "Unknown/Offline":
        if ip_after != ip_before:
            print(f"\n[✅ SUCCESS] IP Publik sukses diputar dari {ip_before} -> {ip_after}!")
            return True
        else:
            print("\n[⚠️ WARNING] IP Publik tidak berubah. Hal ini bisa terjadi jika:")
            print("    1. HP terhubung ke Wi-Fi (Wi-Fi IP bersifat statis, matikan Wi-Fi HP dan gunakan data seluler).")
            print("    2. Operator seluler menetapkan IP lease time yang sama.")
            print("    3. Waktu tunggu koneksi kurang lama (coba naikkan delay_reconnect).")
            return False
    elif ip_changed:
        print("\n[✅ SUCCESS] Rotasi IP berhasil diverifikasi berdasarkan perubahan Local IP Seluler!")
        return True
    elif rotation_worked:
        print("\n[✅ OK] Toggle Mode Pesawat berhasil berjalan (koneksi sirkuit internet berhasil diputus & disambung kembali).")
        return True
    else:
        print("\n[❌ FAILED] HP gagal terhubung kembali ke internet.")
        return False


# ==============================================================================
# MAIN RUNNER
# ==============================================================================
if __name__ == "__main__":
    # Ganti dengan device ID Anda saat melakukan testing
    TEST_DEVICE_ID = "R9RYA030KWX"
    
    if len(sys.argv) > 1:
        TEST_DEVICE_ID = sys.argv[1]

    print(f"Menghubungkan ke device: {TEST_DEVICE_ID}...")
    try:
        d = u2.connect(TEST_DEVICE_ID)
        # Ambil nama brand/model HP
        brand = d.device_info.get('brand', 'Unknown')
        model = d.device_info.get('model', 'Device')
        print(f"Terhubung ke: {brand} {model}")
    except Exception as e:
        print(f"Gagal koneksi ke HP: {e}")
        sys.exit(1)

    # Jalankan rotasi IP
    rotate_device_ip(d, delay_between=6.0, delay_reconnect=18.0)
