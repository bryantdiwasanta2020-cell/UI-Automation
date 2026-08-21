import uiautomator2 as u2
import time
import random
import sys
import re
from ig_helpers import connect_adb, open_instagram

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
    from bot_instagram_clear_popups import clear_any_popup_fast, check_and_clear_daily_limit
except Exception as e:
    def clear_any_popup_fast(d):
        return False
    def check_and_clear_daily_limit(d):
        return False


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

def scroll_dan_follow(target_url="", device_id="all", my_account=""):
    log_id = log_activity("follow_orang", username=target_url or "(notifikasi)", status="on_progress", mode="manual", device_id=device_id, extra={"my_account": my_account})
    try:
        # 1. Koneksi ke perangkat Android
        print("=========================================")
        print(f" JALANKAN BOT FOLLOW ORANG")
        if target_url:
            print(f" Target Profil: {target_url}")
        else:
            print(f" Target Profil: (Daftar Aktivitas Notifikasi)")
        if my_account:
            print(f" Menggunakan Akun Saya: {my_account}")
        print("=========================================")

        d = connect_adb(device_id, action="follow_orang", step_label="[1/5] Menghubungkan ke perangkat Android via ADB...")
        
        width, height = d.window_size()
        print(f"Terhubung ke perangkat: {d.device_info.get('brand', 'Unknown')} {d.device_info.get('model', 'Device')}")

        # 2. Buka aplikasi Instagram
        open_instagram(d, device_id, action="follow_orang", delay=6, step_label="[2/5] Membuka aplikasi Instagram...")
        clear_any_popup_fast(d)

        # === PROSES SWAP AKUN DI AWAL (JIKA PARAMETER DIBERIKAN) ===
        if my_account and my_account.strip() != "":
            print(f"[PRE-RUN] Mengganti akun ke: '{my_account}'...")
            
            # 1. Mengklik tombol Profil kanan bawah (dengan verifikasi halaman profil aktif)
            profile_active = False
            for check_prof in range(3):
                profile_tab = None
                if d(resourceId="com.instagram.android:id/profile_tab").exists:
                    profile_tab = d(resourceId="com.instagram.android:id/profile_tab")
                else:
                    sel = d(descriptionMatches="(?i).*(profile|profil).*", packageName="com.instagram.android")
                    if sel.exists:
                        profile_tab = sel
                            
                if profile_tab:
                    try:
                        profile_tab.click()
                        print("      -> Mengklik tab Profil via selector...")
                        time.sleep(3.0)
                    except:
                        pass
                else:
                    print("      -> Mengklik tab Profil via koordinat fallback...")
                    d.click(int(width * 0.90), int(height * 0.93))
                    time.sleep(1.5)
                    d.click(int(width * 0.90), int(height * 0.914))
                    time.sleep(2.0)
                
                clear_any_popup_fast(d)
                
                # Verifikasi jika nama akun/title bar profil muncul
                if d(resourceId="com.instagram.android:id/action_bar_title").exists or d(resourceId="com.instagram.android:id/title_with_badge_container").exists:
                    profile_active = True
                    break
                else:
                    print(f"      -> Halaman profil belum aktif (percobaan {check_prof+1}/3). Mencoba klik ulang tab Profil...")
            
            clean_acc = my_account.replace("@", "").strip().lower()
            
            # Cek apakah sudah berada di akun tersebut
            current_username = ""
            action_bar_title = d(resourceId="com.instagram.android:id/action_bar_title")
            title_badge = d(resourceId="com.instagram.android:id/title_with_badge_container")
            if action_bar_title.exists:
                current_username = action_bar_title.info.get("text", "").strip().lower()
            elif title_badge.exists:
                child_tv = title_badge.child(className="android.widget.TextView")
                if child_tv.exists:
                    current_username = child_tv.info.get("text", "").strip().lower()
                    
            if current_username == clean_acc:
                print(f"[PRE-RUN] Sudah berada di akun '{clean_acc}'. Melanjutkan perintah...")
            else:
                # 2. Mengklik Nama Pengguna di pojok atas (tengah/kiri) untuk membuka menu ganti akun
                print(f"      -> Akun saat ini '{current_username}' berbeda dengan target '{clean_acc}'. Membuka menu ganti akun...")
                if action_bar_title.exists:
                    action_bar_title.click()
                elif title_badge.exists:
                    title_badge.click()
                else:
                    # Fallback koordinat atas (Bryant Kalibrasi: 0.25, 0.06)
                    d.click(int(width * 0.25), int(height * 0.06))
                time.sleep(3.5)
                
                # 3. Cari nama akun dalam daftar pop-up bawah
                btn_acc = d(text=clean_acc)
                if not btn_acc.exists:
                    btn_acc = d(textContains=clean_acc)
                    
                if btn_acc.exists:
                    print(f"      -> Akun '{clean_acc}' ditemukan di daftar. Mengklik untuk beralih...")
                    btn_acc.click()
                    time.sleep(6.0)
                    clear_any_popup_fast(d)
                    
                    # Cek jika bottom sheet pilihan akun masih terbuka di layar
                    is_sheet_open = (
                        d(resourceId="com.instagram.android:id/bottom_sheet_container").exists or
                        d(textMatches="(?i).*(tambahkan akun|add account).*").exists
                    )
                    if is_sheet_open:
                        print("      -> Bottom sheet pilihan akun masih terbuka. Menekan BACK untuk menutup...")
                        d.press("back")
                        time.sleep(2.0)
                        
                    # Pastikan aplikasi Instagram tetap terbuka di foreground
                    if d.app_current().get('package') != 'com.instagram.android':
                        print("      -> Terdeteksi keluar dari Instagram, membuka kembali...")
                        d.app_start("com.instagram.android")
                        time.sleep(5.0)
                        
                    print(f"[PRE-RUN] Sukses beralih ke akun '{clean_acc}'. Melanjutkan perintah...")
                else:
                    print(f"[PRE-RUN] Akun '{clean_acc}' tidak ditemukan di menu ganti akun!")
                    print("      -> Menutup menu ganti akun (mengirim BACK)...")
                    d.press("back")
                    time.sleep(1.5)
                    print("akun tidak ditemukan")
                    print("=========================================\n")
                    raise Exception("Akun kustom tidak ditemukan")

        # 3. Proses Navigasi dan Follow
        if target_url and target_url.strip() != "":
            # Buka url profil target
            if not (target_url.startswith("http://") or target_url.startswith("https://") or "instagram.com" in target_url):
                # Jika input berupa username biasa (cth: cristiano), buat URL profil
                profile_url = f"https://www.instagram.com/{target_url.replace('@', '').strip()}/"
            else:
                profile_url = target_url.strip()
                
            print(f"[3/5] Membuka URL profil secara langsung: {profile_url}...")
            # Verifikasi jika profil target berhasil dibuka
            profile_opened = False
            for check_prof in range(3):
                d.shell(f'am start -a android.intent.action.VIEW -d "{profile_url}" com.instagram.android')
                time.sleep(6)
                clear_any_popup_fast(d)
                
                if d(textMatches="(?i).*(postingan|posts|pengikut|followers|mengikuti|following).*").exists:
                    profile_opened = True
                    break
                else:
                    print(f"      -> Profil target belum terbuka (percobaan {check_prof+1}/3). Mencoba memicu ulang URL...")
                    
            if not profile_opened:
                raise Exception("Gagal membuka halaman profil target @{}".format(target_url))
            
            # Cari tombol Follow/Ikuti di profil
            print("[4/5] Mencari tombol Follow/Ikuti di halaman profil...")
            log_step("find_follow_button", status="complete", device_id=device_id, action="follow_orang")
            # Mencocokkan teks tombol secara presisi untuk menghindari teks deskriptif seperti "Followed by..."
            follow_btn = d(textMatches="(?i)^(Follow|Ikuti|Follow back|Ikuti balik)$")
            if not follow_btn.exists:
                follow_btn = d(descriptionMatches="(?i)^(Follow|Ikuti|Follow back|Ikuti balik)$")
                
            if follow_btn.exists:
                print(f"      -> Menemukan tombol Follow: '{follow_btn.info.get('text', 'Follow')}'")
                follow_btn.click()
                time.sleep(3.0)
                print("[SUKSES] Akun profil berhasil di-follow!")
            else:
                already_following = d(textMatches="(?i)^(Following|Mengikuti|Message|Kirim pesan|Requested|Diminta)$")
                if already_following.exists:
                    print(f"      -> Akun ini sudah diikuti sebelumnya (Status: '{already_following.info.get('text', '')}').")
                else:
                    print("      -> Tombol Follow/Ikuti tidak terdeteksi di layar.")
            
            print("      -> Selesai melakukan follow profil target.")
            
        else:
            # Jalankan alur follow dari Notifikasi
            print("[3/5] Membuka halaman Notifikasi...")
            log_step("open_notifications", status="complete", device_id=device_id, action="follow_orang")
            xpath_notif = '//*[@resource-id="com.instagram.android:id/notification"]/android.view.ViewGroup[1]'
            
            if d.xpath(xpath_notif).exists:
                print("Mengklik ikon Notifikasi via XPath...")
                d.xpath(xpath_notif).click()
            elif d(resourceId="com.instagram.android:id/notification").exists:
                print("Mengklik ikon Notifikasi via resourceId...")
                d(resourceId="com.instagram.android:id/notification").click()
            elif d(descriptionContains="Notifikasi", packageName="com.instagram.android").exists:
                print("Mengklik ikon Notifikasi via description 'Notifikasi'...")
                d(descriptionContains="Notifikasi", packageName="com.instagram.android").click()
            elif d(descriptionContains="Notification", packageName="com.instagram.android").exists:
                print("Mengklik ikon Notifikasi via description 'Notification'...")
                d(descriptionContains="Notification", packageName="com.instagram.android").click()
            else:
                # Fallback klik menggunakan koordinat perkiraan di kanan atas layar
                print("Mengklik ikon Notifikasi via koordinat kalibrasi (0.94, 0.054)...")
                d.click(int(width * 0.94), int(height * 0.054))
                
            time.sleep(4)  # Tunggu halaman notifikasi memuat
            clear_any_popup_fast(d)

            print("\n[4/5] Memulai proses scroll dan follow otomatis di Notifikasi...")
            sudah_diklik_koordinat = set()
            tidak_ada_perubahan_scroll = 0
            max_scroll_tanpa_perubahan = 10
            max_scrolls = 3
            total_scrolls = 0
            total_di_follow = 0
            is_first_scroll = True

            # Batasan area klik agar tidak mengklik header atau footer menu
            y_min = int(height * 0.15)
            y_max = int(height * 0.85)

            while total_scrolls < max_scrolls and tidak_ada_perubahan_scroll < max_scroll_tanpa_perubahan:
                # Melakukan scroll ke bawah terlebih dahulu untuk memuat konten/akun baru
                if is_first_scroll:
                    print("\nMelakukan scroll ke bawah pertama kali (2x scroll)...")
                    # Scroll ke-1
                    d.swipe(width // 2, int(height * 0.8), width // 2, int(height * 0.2), duration=0.5)
                    total_scrolls += 1
                    time.sleep(2.0)
                    # Scroll ke-2
                    d.swipe(width // 2, int(height * 0.8), width // 2, int(height * 0.2), duration=0.5)
                    total_scrolls += 1
                    time.sleep(3.0)
                    is_first_scroll = False
                else:
                    print("\nMelakukan scroll ke bawah...")
                    # Swipe dari 80% tinggi layar ke 20% tinggi layar
                    d.swipe(width // 2, int(height * 0.8), width // 2, int(height * 0.2), duration=0.5)
                    total_scrolls += 1
                    time.sleep(3.0)  # Tunggu konten memuat setelah scroll
                
                clear_any_popup_fast(d)

                print("\nMencari tombol Follow/Ikuti di layar saat ini...")
                buttons = d(className="android.widget.Button")
                tombol_diklik_di_layar_ini = 0

                for btn in buttons:
                    try:
                        if not btn.exists:
                            continue

                        info = btn.info
                        txt = info.get('text', '')
                        desc = info.get('contentDescription', '')

                        txt_lower = txt.lower() if txt else ""
                        desc_lower = desc.lower() if desc else ""

                        bounds = info.get('bounds', {})
                        if not bounds:
                            continue

                        x = (bounds['left'] + bounds['right']) // 2
                        y = (bounds['top'] + bounds['bottom']) // 2
                        koordinat = (x, y)

                        btn_width = bounds['right'] - bounds['left']
                        btn_height = bounds['bottom'] - bounds['top']

                        if not (y_min <= y <= y_max):
                            continue

                        is_follow_btn = False

                        if "ikuti" in txt_lower or "follow" in txt_lower:
                            is_follow_btn = True
                        elif txt == "" and "follow" in desc_lower:
                            is_follow_btn = True
                        elif txt == "" and desc == "" and btn_width > btn_height * 1.5:
                            is_follow_btn = True

                        skip_keywords = ["mengikuti", "following", "requested", "diminta", "pesan", "message", "batal", "cancel"]
                        for kw in skip_keywords:
                            if kw in txt_lower or kw in desc_lower:
                                is_follow_btn = False
                                break

                        if is_follow_btn and koordinat not in sudah_diklik_koordinat:
                            print(f"Mengklik tombol Follow di koordinat {koordinat} (Teks: '{txt}', Desc: '{desc}')")
                            btn.click()
                            
                            sudah_diklik_koordinat.add(koordinat)
                            tombol_diklik_di_layar_ini += 1
                            total_di_follow += 1
                            
                            jeda = random.uniform(2.0, 4.0)
                            time.sleep(jeda)
                    except Exception as e:
                        continue

                if tombol_diklik_di_layar_ini == 0:
                    tidak_ada_perubahan_scroll += 1
                    print(f"Tidak menemukan tombol follow baru (Percobaan scroll kosong: {tidak_ada_perubahan_scroll}/{max_scroll_tanpa_perubahan})")
                else:
                    tidak_ada_perubahan_scroll = 0

            # Memulai proses kembali ke atas jika ada scroll ke bawah yang dilakukan
            if total_scrolls > 0:
                print(f"\n[INFO] Selesai mencari orang. Memulai proses kembali ke atas ({total_scrolls}x scroll)...")
                for i in range(total_scrolls):
                    print(f"Scrolling ke atas ({i+1}/{total_scrolls})...")
                    d.swipe(width // 2, int(height * 0.2), width // 2, int(height * 0.8), duration=0.3)
                    time.sleep(0.8)
                    
            # Klik tombol kembali (back arrow) di kiri atas
            print("[5/5] Mencoba mengklik tombol kembali (Back) di kiri atas...")
            xpath_back = '//*[@resource-id="com.instagram.android:id/action_bar_button_back"]'
            
            if d(descriptionContains="Kembali", packageName="com.instagram.android").exists:
                d(descriptionContains="Kembali", packageName="com.instagram.android").click()
                print("Berhasil klik tombol kembali via desc 'Kembali'")
            elif d(descriptionContains="Back", packageName="com.instagram.android").exists:
                d(descriptionContains="Back", packageName="com.instagram.android").click()
                print("Berhasil klik tombol kembali via desc 'Back'")
            elif d(descriptionContains="Navigate up", packageName="com.instagram.android").exists:
                d(descriptionContains="Navigate up", packageName="com.instagram.android").click()
                print("Berhasil klik tombol kembali via desc 'Navigate up'")
            elif d.xpath(xpath_back).exists:
                d.xpath(xpath_back).click()
                print("Berhasil klik tombol kembali via XPath")
            else:
                print("Klik tombol kembali via d.press('back')...")
                d.press("back")
                
            time.sleep(2)
            print(f"\n[SELESAI] Proses selesai! Total akun yang berhasil di-follow: {total_di_follow}")
            
        # Alur Akhir: Kembali ke Beranda Instagram (dengan forced stop + restart agar bersih)
        print("\n[5/5] Kembali ke Beranda utama Instagram dan menyegarkan (refresh) feed...")
        try:
            print("      -> Menghentikan paksa (kill) aplikasi Instagram...")
            d.app_stop("com.instagram.android")
            time.sleep(2.0)
            
            print("      -> Membuka kembali aplikasi Instagram...")
            d.app_start("com.instagram.android")
            time.sleep(5.0)
            
            # Segarkan (Refresh) feed dengan klik Beranda
            home_clicked = False
            for rid in ["com.instagram.android:id/feed_tab", "com.instagram.android:id/home_tab"]:
                if d(resourceId=rid).exists:
                    d(resourceId=rid).click()
                    home_clicked = True
                    break
            
            if not home_clicked:
                for desc in ["Beranda", "Home", "Feed"]:
                    el_desc = d(descriptionContains=desc, packageName="com.instagram.android")
                    if el_desc.exists:
                        el_desc.click()
                        home_clicked = True
                        break
                        
            if not home_clicked:
                # Fallback koordinat Beranda (kiri bawah)
                d.click(int(width * 0.10), int(height * 0.93))
            time.sleep(2.0)
            
            d.swipe(0.5, 0.30, 0.5, 0.80, duration=0.25)
            time.sleep(3.0)
            print("      [SUKSES] Halaman Beranda berhasil di-refresh.")
            log_complete(log_id, message="Follow orang action completed successfully")
        except Exception as opt_err:
            print(f"      -> Gagal kembali/refresh Beranda: {opt_err}")
            log_complete(log_id, message="Follow orang action completed but failed to refresh home")

    except Exception as e:
        print(f"Terjadi kesalahan utama: {e}")
        log_error(log_id, error=str(e))

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


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser(description="Bot Instagram Follow Orang / Target Profile")
    parser.add_argument("pos_args", nargs="*", help="Positional arguments untuk kompatibilitas mundur")
    parser.add_argument("--target", "--target_url", "--target-url", "--url", "--username", "--user", "-t", default="", help="Target username atau URL profil")
    parser.add_argument("--mode", "-m", default="username", help="Mode follow (username/url/normal/target_user)")
    parser.add_argument("--device", "--device-id", "--device_id", "-d", default="all", help="Device ID atau 'all'")
    parser.add_argument("--my-account", "--my_account", "--account", "-a", default="", help="Username akun pengakses")
    parser.add_argument("--count", "--limit", "-l", type=int, default=1, help="Jumlah target")

    args, unknown = parser.parse_known_args() if hasattr(parser, 'parse_known_args') else (parser.parse_args(), [])
    
    target = args.target or ""
    device_id = args.device or "all"
    my_account = args.my_account or ""
    pos = list(args.pos_args)

    if pos:
        # Check if first pos arg is a mode tag (e.g. 'target_user', 'target_url', 'username', 'normal', 'url')
        if pos[0].lower() in ["target_user", "target_url", "username", "url", "normal", "target", "user"]:
            pos.pop(0)
            
        if pos:
            if not target:
                target = pos[0]
            if len(pos) > 1 and device_id == "all":
                device_id = pos[1]
            if len(pos) > 2 and not my_account:
                my_account = pos[2]

    return target, device_id, my_account

if __name__ == "__main__":
    target_url, device_id, my_account = parse_arguments()
    
    if not target_url and len(sys.argv) <= 1 and sys.stdin.isatty():
        try:
            print("\n--- MENJALANKAN BOT FOLLOW ORANG SECARA INTERAKTIF ---")
            ans_url = input("Masukkan URL / Username profil target (kosongkan untuk follow dari Notifikasi): ").strip()
            if ans_url:
                target_url = ans_url
            ans_dev = input("Masukkan device ID (kosongkan/tekan Enter untuk 'all'): ").strip()
            if ans_dev:
                device_id = ans_dev
        except (EOFError, KeyboardInterrupt):
            pass
            
    devices = resolve_devices(device_id)
    if len(devices) > 1:
        run_parallel_threads(scroll_dan_follow, devices, target_url=target_url, my_account=my_account)
    else:
        scroll_dan_follow(target_url, device_id=devices[0], my_account=my_account)
