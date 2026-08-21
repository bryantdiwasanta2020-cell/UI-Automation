import sys
import os
import time
import uiautomator2 as u2
from ig_helpers import connect_adb

# Import activity logger if available
try:
    from activity_logger import log_activity, log_complete, log_error, log_step
except Exception:
    def log_activity(*a, **kw): return ""
    def log_complete(*a, **kw): return False
    def log_error(*a, **kw): return False
    def log_step(*a, **kw): return False

# Import popup cleaner if available
try:
    from bot_instagram_clear_popups import clear_any_popup_fast, check_and_clear_daily_limit, clear_post_login_popups
except ImportError:
    def clear_any_popup_fast(d, *args, **kwargs): return False
    def check_and_clear_daily_limit(d, *args, **kwargs): return False
    def clear_post_login_popups(d, *args, **kwargs): return False


def get_connected_devices():
    import subprocess
    try:
        out = subprocess.check_output(["adb", "devices"]).decode("utf-8", errors="ignore")
        devices = []
        for line in out.strip().split("\n")[1:]:
            if "device" in line and not line.startswith("*"):
                parts = line.split()
                if len(parts) > 0:
                    devices.append(parts[0])
        return devices
    except Exception:
        return []


def run_parallel_threads(target_func, devices, *args, **kwargs):
    import threading
    import inspect
    threads = []
    print(f"[*] Menjalankan {target_func.__name__} secara paralel pada device: {devices}")
    
    sig = inspect.signature(target_func)
    dev_key = "device_pilihan"
    if "device_id" in sig.parameters:
        dev_key = "device_id"
        
    for dev in devices:
        t = threading.Thread(target=target_func, args=args, kwargs={**kwargs, dev_key: dev})
        threads.append(t)
        t.start()
        time.sleep(1.0)
    for t in threads:
        t.join()


def switch_instagram_account(target_username, device_pilihan="all"):
    clean_username = target_username.replace("@", "").strip()
    log_id = log_activity("switch_account", username=clean_username, status="on_progress", mode="manual", device_id=device_pilihan)
    
    try:
        print("=========================================")
        print(" JALANKAN BOT GANTI AKUN INSTAGRAM")
        print(f" Target Akun : @{clean_username}")
        print(f" Device      : {device_pilihan}")
        print("=========================================")

        print("[1] Menghubungkan ke perangkat Android...")
        log_step("connect_device", status="complete", device_id=device_pilihan, action="switch_account")
        d = connect_adb(device_pilihan)
            
        width, height = d.window_size()
        print(f"Terhubung ke perangkat: {d.device_info.get('brand', 'Unknown')} {d.device_info.get('model', 'Device')} ({width}x{height})")

        print("[2] Membuka kembali Instagram secara bersih (Force Close & Restart)...")
        log_step("open_app", status="complete", device_id=device_pilihan, action="switch_account")
        try:
            d.app_stop("com.instagram.android")
            time.sleep(1.5)
            # Tembak force-stop sistem adb sebagai jaring pengaman tambahan
            d.shell("am force-stop com.instagram.android")
            time.sleep(1.0)
        except Exception as e:
            print(f"      [WARNING] Gagal menghentikan Instagram: {e}")
            
        d.app_start("com.instagram.android")
        print("      -> Menunggu aplikasi terbuka secara penuh (6.5 detik)...")
        time.sleep(6.5)
        clear_any_popup_fast(d)

        # 1. Pastikan posisi di Beranda/Profil dengan menekan Profil kanan bawah
        print("[3] Mengakses halaman Profil...")
        log_step("open_profile", status="complete", device_id=device_pilihan, action="switch_account")
        
        # Jaring pengaman: Jika berada di dalam sub-halaman (detail post/comment/keyboard terbuka), tekan BACK sampai tab bar terlihat
        try:
            d.keyboard_dismiss()
            time.sleep(0.5)
        except:
            pass
            
        for back_attempt in range(5):
            main_tabs_exist = (
                d(resourceId="com.instagram.android:id/profile_tab").exists or
                d(resourceId="com.instagram.android:id/profile_tab_avatar").exists or
                d(resourceId="com.instagram.android:id/feed_tab").exists or
                d(resourceId="com.instagram.android:id/clips_tab").exists or
                d(resourceId="com.instagram.android:id/search_tab").exists or
                d(descriptionMatches="(?i).*(Profil|Profile|Beranda|Home|Search|Reels|Search and Explore).*").exists
            )
            if main_tabs_exist:
                break
            print(f"      -> Terdeteksi berada di sub-halaman/postingan. Mengirim BACK ke-{back_attempt+1}...")
            d.press("back")
            time.sleep(2.0)
            clear_any_popup_fast(d)

        x_profile = int(width * 0.904)
        y_profile = int(height * 0.914)
        d.click(x_profile, y_profile)
        time.sleep(3.0)
        clear_any_popup_fast(d)

        # Cek apakah akun aktif saat ini sudah sesuai dengan target (agar tidak stuck/error jika sudah aktif)
        current_active_user = ""
        for rid in ["com.instagram.android:id/action_bar_title", "com.instagram.android:id/action_bar_title_text", "com.instagram.android:id/title_text"]:
            el = d(resourceId=rid)
            if el.exists:
                try:
                    current_active_user = el.get_text().replace("@", "").strip().lower()
                    break
                except:
                    pass
                
        if current_active_user == clean_username.lower():
            print(f"   -> Akun @{clean_username} sudah aktif saat ini. Melewati proses ganti akun...")
            log_complete(log_id, message=f"Already active as @{clean_username}")
            return True

        # 2. Tekan Lama pada Tombol Profil untuk memunculkan daftar akun yang sudah login (Trik Fast Switcher)
        print("[4] Membuka menu ganti akun dengan menekan lama profil...")
        log_step("open_profile_switcher", status="complete", device_id=device_pilihan, action="switch_account")
        
        profile_tab = None
        for rid in ["com.instagram.android:id/profile_tab", "com.instagram.android:id/profile_tab_avatar"]:
            if d(resourceId=rid).exists:
                profile_tab = d(resourceId=rid)
                break
        
        if profile_tab and profile_tab.exists:
            try:
                profile_tab.long_click()
                print("      -> Long click profile tab via selector berhasil")
            except Exception:
                d.long_click(x_profile, y_profile, 1.5)
                print("      -> Fallback long click profile tab via koordinat")
        else:
            d.long_click(x_profile, y_profile, 1.5)
            print("      -> Fallback long click profile tab via koordinat")
        time.sleep(3.5)

        # 3. Cari nama akun dalam daftar pop-up bawah
        print(f"[5] Mencari akun target @{clean_username}...")
        log_step("click_target_account", status="on_progress", device_id=device_pilihan, action="switch_account")
        btn_acc = d(text=clean_username)
        if not btn_acc.exists:
            btn_acc = d(textContains=clean_username)

        if btn_acc.exists:
            print(f"      -> Akun @{clean_username} ditemukan di daftar. Mengklik untuk beralih...")
            btn_acc.click()
            time.sleep(6.0)
            clear_any_popup_fast(d)
            print("=========================================")
            print(f" BERHASIL BERALIH KE AKUN @{clean_username}")
            print("=========================================\n")
            log_step("click_target_account", status="complete", device_id=device_pilihan, action="switch_account")
            log_complete(log_id, message=f"Switched successfully to @{clean_username}")
            return True
        else:
            # Tutup menu ganti akun jika gagal
            d.press("back")
            time.sleep(1.5)
            raise ValueError(f"Akun @{clean_username} tidak terdaftar di perangkat ini!")

    except Exception as e:
        print(f"ERROR: Terjadi kesalahan saat beralih akun: {e}")
        log_error(log_id, error=str(e))
        return False


def resolve_devices(device_id):
    devices = []
    if not device_id:
        device_id = "all"
    if "," in device_id:
        devices = [d.strip() for d in device_id.split(",") if d.strip()]
    elif device_id.lower() == "all" or "semua" in device_id.lower():
        devices = get_connected_devices()
        if not devices:
            devices = ["all"]
    else:
        devices = [device_id]
    return devices


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR: Argumen username target wajib diisi!")
        print("Penggunaan: python3 switch_akun_ig.py <target_username> [device_id]")
        sys.exit(1)

    target_username = sys.argv[1]
    device_id = sys.argv[2] if len(sys.argv) > 2 else "all"

    devices = resolve_devices(device_id)
    if len(devices) > 1:
        run_parallel_threads(switch_instagram_account, devices, target_username=target_username)
    else:
        success = switch_instagram_account(target_username, device_pilihan=devices[0])
        if not success:
            sys.exit(1)