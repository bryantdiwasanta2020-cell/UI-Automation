import sys
import uiautomator2 as u2
import time
import os
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
    from bot_instagram_clear_popups import clear_any_popup_fast, get_current_package_safe
except ImportError:
    def clear_any_popup_fast(d, *args, **kwargs):
        return False
    def get_current_package_safe(d, *args, **kwargs):
        try:
            return d.app_current().get('package', '')
        except:
            return ''

def clear_popups_logout(d):
    """
    Wrapper untuk mengarahkan ke pembersih pop-up terpusat.
    """
    return clear_any_popup_fast(d)

def run_logout_bot(device_pilihan="all", mode="single"):
    log_id = log_activity("logout", username="", status="on_progress", mode="campaign" if mode == "all" else "manual", device_id=device_pilihan)
    try:
        print("=========================================")
        print(" JALANKAN BOT LOGOUT (AKSELERASI FAST)")
        print(f" Perangkat: {device_pilihan}")
        print(f" Mode     : {mode.upper()}")
        print("=========================================")

        d = connect_adb(device_pilihan, action=None, step_label="[1] Menghubungkan ke perangkat Android...")
        width, height = d.window_size()
        print(f"Terhubung ke perangkat: {d.device_info.get('brand', 'Unknown')} {d.device_info.get('model', 'Device')}")

        open_instagram(d, device_pilihan, action=None, delay=3.5, step_label="[2] Membuka aplikasi Instagram...")

        # Bersihkan pop-up awal jika ada
        try:
            from bot_instagram_clear_popups import clear_any_popup_fast
            clear_any_popup_fast(d)
        except Exception as e:
            print(f"      -> Gagal memanggil popup cleaner: {e}")
        clear_popups_logout(d)

        time.sleep(1.0)

        # Teks menu Pengaturan yang mungkin muncul
        settings_texts = [
            "Settings and privacy", "Pengaturan dan privasi", 
            "Settings and activity", "Pengaturan dan aktivitas",
            "Settings", "Pengaturan", "Settings & Privacy", 
            "Settings & activity", "Pengaturan & aktivitas"
        ]

        # FUNGSI DETEKSI LOGOUT DINAMIS
        def find_logout_btn():
            candidates = []
            try:
                selector_text = d(textMatches="(?i).*(log[- ]?out|keluar).*")
                for i in range(selector_text.count):
                    elem = selector_text[i]
                    if elem.exists:
                        txt = elem.info.get('text', '') or ""
                        desc = elem.info.get('contentDescription', '') or ""
                        candidates.append((elem, txt, desc))
            except Exception:
                pass
            try:
                selector_desc = d(descriptionMatches="(?i).*(log[- ]?out|keluar).*")
                for i in range(selector_desc.count):
                    elem = selector_desc[i]
                    if elem.exists:
                        txt = elem.info.get('text', '') or ""
                        desc = elem.info.get('contentDescription', '') or ""
                        if not any(c[1] == txt and c[2] == desc for c in candidates):
                            candidates.append((elem, txt, desc))
            except Exception:
                pass
                
            best_candidates = []
            for elem, txt, desc in candidates:
                txt_lower = (txt or desc).lower()
                if "tambah" in txt_lower or "add" in txt_lower:
                    continue  # Abaikan Add Account
                best_candidates.append((elem, txt or desc))
            
            if best_candidates:
                return best_candidates[0][0], best_candidates[0][1]
            return None, None

        # Alur State-Machine untuk Logout yang Adaptif & Aman
        start_time = time.time()
        max_duration = 300 if mode == "all" else 120  # 300 detik untuk mode all, 120 detik untuk single
        initial_user = ""
        
        print("[3] Memulai proses Log Out Akun (State-Machine)...")
        
        while time.time() - start_time < max_duration:
            # Pemicu pembersih pop-up cepat di awal setiap iterasi
            try:
                clear_any_popup_fast(d)
            except:
                pass
            # 1. Dapatkan activity aktif saat ini
            try:
                app_info = d.app_current()
            except Exception as e:
                print(f"   -> Gagal mendapatkan info activity: {e}")
                time.sleep(2.0)
                continue
                
            pkg = app_info.get('package', '')
            act = app_info.get('activity', '')
            
            # Jika keluar dari Instagram, buka kembali
            if pkg != 'com.instagram.android':
                print(f"   [SYSTEM] Terdeteksi di luar aplikasi Instagram: '{pkg}'. Membuka kembali...")
                d.app_start("com.instagram.android")
                time.sleep(4.0)
                continue
                
            # Ambil hierarchy XML layar
            try:
                xml_src = d.dump_hierarchy()
            except Exception as e:
                print(f"   -> Gagal dump hierarchy: {e}")
                time.sleep(1.5)
                continue
            xml_lower = xml_src.lower()
            is_in_main = any(kw in act.lower() for kw in ["main", "tab", "feed", "reels", "home"]) if act else ("feed_tab" in xml_lower or "profile_tab" in xml_lower)
            
            # A. KONDISI: Dialog Konfirmasi Logout aktif
            is_logout_confirm = any(kw in xml_lower for kw in ["log out of", "keluar dari"]) and any(kw in xml_lower for kw in ["logout", "log out", "keluar", "ya", "yes"])
            if is_logout_confirm:
                print("   [CONFIRMATION] Terdeteksi dialog konfirmasi Log Out.")
                is_all_confirm = "all" in xml_lower or "semua" in xml_lower
                clicked_logout = False
                for btn_txt in ["Logout", "Log out", "Log Out", "Keluar", "Ya", "Yes"]:
                    btn = d(text=btn_txt)
                    if btn.exists:
                        print(f"      -> Mengklik tombol konfirmasi: '{btn_txt}'")
                        log_step("confirm_logout", status="complete", device_id=device_pilihan, action="logout")
                        btn.click()
                        clicked_logout = True
                        time.sleep(5.0)
                        
                        if mode == "single" or is_all_confirm:
                            print(" [SUKSES] Akun berhasil Log Out! Menghentikan program...")
                            log_complete(log_id, message="Successfully logged out")
                            sys.exit(0)
                        else:
                            print("   -> Satu akun keluar. Melanjutkan ke akun berikutnya...")
                            break
                if clicked_logout:
                    continue
                    
            # B. KONDISI: Penawaran simpan info login (Save login info)
            is_save_info = "save login info" in xml_lower or "simpan info login" in xml_lower or "remember login" in xml_lower or "simpan informasi login" in xml_lower
            if is_save_info:
                print("   [SAVE INFO] Terdeteksi penawaran simpan info login.")
                clicked_save = False
                for btn_txt in ["Lain kali", "Not now", "Not Now", "Lain Kali", "Jangan sekarang", "Jangan Sekarang"]:
                    btn = d(text=btn_txt)
                    if btn.exists:
                        print(f"      -> Mengklik: '{btn_txt}'")
                        btn.click()
                        clicked_save = True
                        time.sleep(2.0)
                        break
                if not clicked_save:
                    d.press("back")
                    time.sleep(2.0)
                continue
                
            # C. KONDISI: Sudah berada di halaman login (Signed out / Landing Page)
            is_login_screen = False
            
            # 1. Deteksi Landing Page (Daftar Akun Tersimpan)
            is_landing_page = (
                "use another profile" in xml_lower or 
                "gunakan profil lain" in xml_lower or 
                "create new account" in xml_lower or 
                "buat akun baru" in xml_lower or
                "log in to another account" in xml_lower or
                "masuk ke akun lain" in xml_lower
            )
                
            # 2. Deteksi Login Form (Form isi username/password)
            is_login_form = (
                "forgot password" in xml_lower or 
                "lupa kata sandi" in xml_lower or 
                "com.instagram.android:id/login_layout" in xml_lower or
                "nomor telepon, email" in xml_lower or
                "phone number, email" in xml_lower
            )
            
            if is_landing_page or is_login_form:
                is_login_screen = True
            
            if is_login_screen:
                print(" [SUKSES] Seluruh akun berhasil Log Out! Terdeteksi halaman login utama.")
                log_complete(log_id, message="Successfully logged out all accounts")
                sys.exit(0)
                
            # D. KONDISI: Sedang berada di halaman Pengaturan/Settings
            is_settings_screen = any(kw in xml_lower for kw in [
                "settings and privacy", "pengaturan dan privasi", 
                "settings and activity", "pengaturan dan aktivitas",
                "settings & privacy", "settings & activity",
                "accounts center", "pusat akun"
            ])
            
            if is_settings_screen:
                print("   [SETTINGS] Sedang berada di halaman Pengaturan/Settings.")
                logout_btn, btn_label = find_logout_btn()
                
                # Jika belum ketemu, scroll ke bawah secara bertahap sampai ketemu (maksimal 6 kali scroll)
                scroll_count = 0
                while not logout_btn and scroll_count < 6:
                    scroll_count += 1
                    print(f"      -> Tombol Log Out belum terlihat, melakukan scroll ke-{scroll_count}...")
                    d.swipe(0.5, 0.80, 0.5, 0.20, duration=0.15)
                    time.sleep(1.5)
                    logout_btn, btn_label = find_logout_btn()
                    
                if logout_btn:
                    print(f"      -> Menemukan tombol Log Out: '{btn_label}'. Mengklik...")
                    logout_btn.click()
                    time.sleep(2.5)
                else:
                    print("      -> Tombol Log Out tidak ditemukan setelah 6 kali scroll. Menunggu...")
                    time.sleep(2.0)
                continue

            # E. KONDISI: Ada Menu Opsi Bottom Sheet yang terbuka di layar
            is_options_menu_open = any(kw in xml_lower for kw in [
                "settings and privacy", "pengaturan dan privasi", 
                "settings and activity", "pengaturan dan aktivitas",
                "settings & privacy", "settings & activity"
            ])
            if is_options_menu_open:
                print("   [MENU OPTIONS] Menu opsi tiga garis sedang terbuka.")
                settings_clicked = False
                for txt in settings_texts:
                    btn = d(text=txt)
                    if btn.exists:
                        print(f"      -> Mengklik menu Pengaturan: '{txt}'")
                        btn.click()
                        settings_clicked = True
                        time.sleep(3.0)
                        break
                if not settings_clicked:
                    d.click(int(width * 0.5), int(height * 0.70))
                    time.sleep(3.0)
                continue

            # F. KONDISI: Ada di halaman profil (terlihat tombol edit/share profile atau menu_button)
            is_profile_page = (
                d(resourceId="com.instagram.android:id/menu_button").exists \
                or d(descriptionMatches="(?i).*(options|opsi|menu|settings|pengaturan).*").exists \
                or d(textMatches="(?i).*(edit profil|edit profile|bagikan profil|share profile).*").exists
            ) and not (
                "create new account" in xml_lower or "buat akun baru" in xml_lower or
                "use another profile" in xml_lower or "gunakan profil lain" in xml_lower
            )
                
            if is_profile_page:
                try:
                    current_username = ""
                    title_text = d(resourceId="com.instagram.android:id/action_bar_title_text")
                    title_btn = d(resourceId="com.instagram.android:id/action_bar_title")
                    if title_text.exists:
                        current_username = title_text.info.get('text', '').replace("@", "").strip()
                    elif title_btn.exists:
                        current_username = title_btn.info.get('text', '').replace("@", "").strip()
                    
                    if current_username:
                        if not initial_user:
                            initial_user = current_username
                            print(f"   [PROFILE] Mendeteksi username aktif di awal: '@{initial_user}'")
                        elif mode == "single" and current_username != initial_user:
                            print(f" [SUKSES] Akun @{initial_user} berhasil Log Out! (Sekarang beralih ke akun @{current_username})")
                            log_complete(log_id, message=f"Successfully logged out @{initial_user}")
                            sys.exit(0)
                except Exception as e:
                    pass

                print("   [PROFILE] Berada di halaman Profil. Mengklik menu Opsi (tiga garis)...")
                menu_clicked = False
                
                # 1. Cari berdasarkan ID menu_button / action_bar_right_button / action_bar_button
                for rid in ["com.instagram.android:id/menu_button", "com.instagram.android:id/action_bar_right_button", "com.instagram.android:id/action_bar_button"]:
                    btn = d(resourceId=rid)
                    if btn.exists:
                        try:
                            btn.click()
                            menu_clicked = True
                            break
                        except:
                            pass
                            
                # 2. Cari berdasarkan deskripsi spesifik (Opsi, options, menu, settings)
                if not menu_clicked:
                    for descriptor in ["Opsi lainnya", "More options", "Options", "Menu", "Settings", "Pengaturan"]:
                        elem = d(descriptionContains=descriptor)
                        if elem.exists:
                            try:
                                elem.click()
                                menu_clicked = True
                                break
                            except:
                                print("-> Eror saat mengklik menu Opsi (tiga garis)...")
                            
                                
                # 3. Fallback klik koordinat pojok kanan atas
                if not menu_clicked:
                    print("      -> Klik koordinat fallback kanan atas (tiga garis)...")
                    d.click(int(width * 0.93), int(height * 0.055))
                    menu_clicked = True
                time.sleep(2.5)
                continue

            # G. KONDISI: Tab profil terlihat (artinya kita di feed utama Instagram / MainTabActivity)
            profile_tab = None
            if d(resourceId="com.instagram.android:id/profile_tab").exists:
                profile_tab = d(resourceId="com.instagram.android:id/profile_tab")
            else:
                for descriptor in ["Profil", "Profile", "Profile tab", "Tab profil", "Self profile"]:
                    elem = d(descriptionMatches=f"(?i)^({descriptor})$")
                    if elem.exists:
                        profile_tab = elem
                        break

            if profile_tab:
                print("   [MAIN] Halaman utama terdeteksi (tab Profil terlihat). Mengklik tab Profil...")
                profile_tab.click()
                time.sleep(2.5)
                continue

            # H. KONDISI DEFAULT: Jika tidak memenuhi semua kondisi di atas (tidak di settings, tidak di profil, tab profil terhalang/tidak ada)
            # Kita kirim tombol BACK secara terus-menerus sampai kembali ke halaman IG utama!
            print("   [BACKUP] Posisi terhalang atau tidak dikenal. Mengirim tombol BACK...")
            d.press("back")
            time.sleep(2.0)

        print("[PERINGATAN] Batas waktu Log Out terlampaui.")
        log_error(log_id, error="Batas waktu Log Out terlampaui (Timeout)")
        sys.exit(1)

    except Exception as e:
        print(f"[ERROR EXCEPTION] Gagal logout: {e}")
        log_error(log_id, error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    device_id = sys.argv[1] if len(sys.argv) > 1 else ""
    mode = sys.argv[2].lower() if len(sys.argv) > 2 else "single"

    # KONDISI 1: SYSTEM MODE (Dijalankan via CLI argument lengkap)
    if device_id:
        run_logout_bot(device_id, mode)
        sys.exit(0)

    # KONDISI 2: LOCAL / LAPTOP TERMINAL MODE (Interaktif, isatty == True)
    if sys.stdin.isatty():
        try:
            print("\n--- [LOKAL MODE] MENJALANKAN BOT LOGOUT SECARA INTERAKTIF ---")
            ans_dev = input("Masukkan device ID (kosongkan/tekan Enter untuk 'all'): ").strip()
            device_id = ans_dev if ans_dev else "all"
            
            ans_mode = input("Masukkan mode logout ('single' untuk 1 akun saja, 'all' untuk semua akun) [default: single]: ").strip().lower()
            mode = ans_mode if ans_mode in ["single", "all"] else "single"
            
            run_logout_bot(device_id, mode)
            sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\nEksekusi dibatalkan oleh user.")
            sys.exit(1)

    # KONDISI 3: SERVER BACKGROUND MODE (Non-TTY, isatty == False)
    else:
        print("\n--- [SERVER MODE] MENJALANKAN BOT LOGOUT DI BACKGROUND/CRON ---")
        # 1. Coba baca dari environment variables
        device_id = os.environ.get("IG_DEVICE_ID", "all")
        mode = os.environ.get("IG_LOGOUT_MODE", "single")
        
        # 2. Coba baca dari file konfigurasi default
        if os.path.exists("default_post_config.json"):
            try:
                import json
                with open("default_post_config.json", "r") as f:
                    config = json.load(f)
                    device_id = config.get("device_id", "all")
                    mode = config.get("logout_mode", "single")
                print("   -> Menggunakan konfigurasi dari default_post_config.json")
            except Exception as e:
                print(f"   -> Gagal membaca default_post_config.json: {e}")
                
        run_logout_bot(device_id, mode)
        sys.exit(0)
