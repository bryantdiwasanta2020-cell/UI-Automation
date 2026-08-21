import sys
import uiautomator2 as u2
import time
import os
import threading
import re
from ig_helpers import connect_adb, open_instagram

# Session holders for failure recovery
CURRENT_D_SESSION = [None]
ORIGINAL_ACCOUNT_HOLDER = [None]

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
    from bot_instagram_clear_popups import clear_any_popup_fast, handle_system_dialogs_and_permissions, get_current_package_safe, clear_post_login_popups
except ImportError:
    def clear_any_popup_fast(d, *args, **kwargs):
        return False
    def handle_system_dialogs_and_permissions(d, *args, **kwargs):
        return False
    def clear_post_login_popups(d, *args, **kwargs):
        return False
    def get_current_package_safe(d, *args, **kwargs):
        try:
            return d.app_current().get('package', '')
        except:
            return ''

def find_element_by_text_or_desc(d, text_val, regex=False, contains=False):
    """
    Mencari UiObject berdasarkan text atau description secara aman.
    """
    if regex:
        sel_text = d(textMatches=text_val)
        if sel_text.exists:
            return sel_text
        sel_desc = d(descriptionMatches=text_val)
        if sel_desc.exists:
            return sel_desc
    elif contains:
        sel_text = d(textContains=text_val)
        if sel_text.exists:
            return sel_text
        sel_desc = d(descriptionContains=text_val)
        if sel_desc.exists:
            return sel_desc
    else:
        sel_text = d(text=text_val)
        if sel_text.exists:
            return sel_text
        sel_desc = d(description=text_val)
        if sel_desc.exists:
            return sel_desc
    return None

def run_login_bot(user, password, device_pilihan="all"):
    log_id = log_activity("login", username=user, status="on_progress", mode="manual", device_id=device_pilihan)
    try:
        _run_login_bot_impl(user, password, device_pilihan, log_id)
    except Exception as e:
        print(f"\n[ERROR] Terjadi kesalahan saat login: {e}")
        log_error(log_id, error=str(e))
        
        # Recovery ke akun semula jika ada
        d = CURRENT_D_SESSION[0]
        original_account = ORIGINAL_ACCOUNT_HOLDER[0]
        if d and original_account and original_account.lower() != user.lower():
            try:
                width, height = d.window_size()
                _kembali_ke_akun_asal(d, original_account, width, height)
            except Exception as rec_err:
                print(f"   -> Gagal memulihkan ke akun asal: {rec_err}")
        sys.exit(1)

def _kembali_ke_akun_asal(d, original_account, width, height):
    if not original_account:
        return
    print(f"\n--- [RECOVERY] MENGEMBALIKAN KE AKUN SEMULA: '{original_account}' ---")
    try:
        if d.app_current().get("package") != "com.instagram.android":
            d.app_start("com.instagram.android")
            time.sleep(4.0)
    except:
        pass

    for attempt in range(4):
        try:
            xml_src = d.dump_hierarchy()
            xml_lower = xml_src.lower()
        except:
            time.sleep(1.5)
            continue
            
        if "feed_tab" in xml_lower or "profile_tab" in xml_lower:
            profile_title_elm = None
            for sel in [
                d(resourceId="com.instagram.android:id/action_bar_title", className="android.widget.TextView"),
                d(resourceId="com.instagram.android:id/title_text", className="android.widget.TextView")
            ]:
                if sel.exists:
                    profile_title_elm = sel
                    break
            
            if profile_title_elm:
                active_user = profile_title_elm.get_text().strip().lower()
                if original_account.lower() in active_user or active_user in original_account.lower():
                    print(f"   -> [SUKSES RECOVERY] Berhasil kembali ke akun semula '{original_account}'!")
                    return
                else:
                    print("   -> Akun tidak cocok. Membuka account switcher untuk beralih...")
                    profile_tab = d(resourceId="com.instagram.android:id/profile_tab")
                    if profile_tab.exists:
                        profile_tab.long_click()
                    else:
                        d.click(int(width * 0.9), int(height * 0.93))
                        time.sleep(0.5)
                        d.long_click(int(width * 0.9), int(height * 0.93), duration=1.0)
                    time.sleep(3.0)
                    continue
            else:
                profile_tab = d(resourceId="com.instagram.android:id/profile_tab")
                if profile_tab.exists:
                    profile_tab.click()
                else:
                    d.click(int(width * 0.9), int(height * 0.93))
                time.sleep(2.5)
                continue

        is_switcher_open = (
            ("tambah" in xml_lower and "akun" in xml_lower) or 
            ("add" in xml_lower and "account" in xml_lower) or 
            ("log in or create" in xml_lower) or 
            ("masuk atau buat" in xml_lower)
        )
        if is_switcher_open:
            target_btn = find_element_by_text_or_desc(d, original_account)
            if not target_btn or not target_btn.exists:
                target_btn = find_element_by_text_or_desc(d, original_account, contains=True)
            if target_btn and target_btn.exists:
                print(f"   -> Menemukan akun semula '{original_account}' di switcher. Klik untuk beralih...")
                target_btn.click()
                time.sleep(5.0)
                return
            else:
                d.press("back")
                time.sleep(2.0)
                return

        if "pilih akun" in xml_lower or "choose account" in xml_lower or "existing" in xml_lower or "sudah ada" in xml_lower:
            target_btn = find_element_by_text_or_desc(d, original_account)
            if not target_btn or not target_btn.exists:
                target_btn = find_element_by_text_or_desc(d, original_account, contains=True)
            if target_btn and target_btn.exists:
                print(f"   -> Menemukan akun semula '{original_account}' di saved list. Klik...")
                target_btn.click()
                time.sleep(5.0)
                return
            else:
                return
        
        d.press("back")
        time.sleep(2.0)

def _run_login_bot_impl(user, password, device_pilihan="all", log_id=None):
    print("=========================================")
    print(" JALANKAN BOT LOGIN (STATE-MACHINE MODE)")
    print(f" Akun: {user}")
    print(f" Perangkat: {device_pilihan}")
    print("=========================================")

    d = connect_adb(device_pilihan, action="login", step_label="[1] Menghubungkan ke perangkat Android...")
    CURRENT_D_SESSION[0] = d
    ORIGINAL_ACCOUNT_HOLDER[0] = None
        
    width, height = d.window_size()
    
    # Set u2 settings untuk kecepatan maksimal
    try:
        for key in ['waitForIdle', 'wait_for_idle']:
            try:
                d.settings[key] = False
            except:
                pass
        d.settings['click_post_delay'] = 0
        d.settings['key_post_delay'] = 0
        print("      -> Mengatur u2 settings: INSTANT EXECUTION")
    except Exception as e:
        print(f"      -> Gagal menyetel u2 settings: {e}")
        
    try:
        d.wait_timeout = 3.0
    except:
        pass

    print(f"Terhubung ke perangkat: {d.device_info.get('brand', 'Unknown')} {d.device_info.get('model', 'Device')}")

    # Pastikan layar menyala & tidak terkunci
    try:
        d.screen_on()
        d.unlock()
        time.sleep(1.0)
    except:
        pass

    open_instagram(d, device_pilihan, action="login", delay=3.5, step_label="[2] Membuka aplikasi Instagram...")

    username_pencarian = user.split('@')[0]
    start_time = time.time()
    max_duration = 120  # 120 detik maksimal
    success = False
    seen_wrong_users = {}
    single_saved_landing_attempts = 0
    
    print("[3] Memulai deteksi tampilan dan login dinamis...")
    log_step("login_state_machine", status="on_progress", device_id=device_pilihan, action="login")
    
    while time.time() - start_time < max_duration:
        # Ambil paket aplikasi aktif
        pkg = get_current_package_safe(d)
        
        # Jaring pengaman jika terpental keluar dari Instagram atau terhalang sistem
        if pkg and pkg != 'com.instagram.android' and pkg != 'com.android.systemui' and 'launcher' not in pkg.lower() and 'credential' not in pkg.lower() and 'gms' not in pkg.lower():
            print(f"   [SYSTEM] Terdeteksi aplikasi lain aktif: '{pkg}'. Mengirim tombol BACK...")
            d.press("back")
            time.sleep(2.0)
            continue

        # Ambil hirarki halaman XML
        try:
            xml_src = d.dump_hierarchy()
        except Exception as e:
            print(f"   -> Gagal membaca layout layar: {e}")
            time.sleep(1.5)
            continue
            
        xml_lower = xml_src.lower()

        # CHECKER: Jaring pengaman jika tidak sengaja masuk ke layar Registrasi/Buat Akun baru
        is_registration_screen = (
            "buat nama pengguna" in xml_lower or 
            "create username" in xml_lower or 
            "tanggal lahir" in xml_lower or 
            "date of birth" in xml_lower or 
            "buat kata sandi" in xml_lower or 
            "create a password" in xml_lower or
            "nama lengkap" in xml_lower or
            "full name" in xml_lower
        )
        # Halaman Saved Account memiliki tombol "Create new account" tetapi tidak memiliki EditText.
        # Jika terdeteksi is_registration_screen DAN ada EditText, berarti kita berada di dalam form registrasi.
        if is_registration_screen and d(className="android.widget.EditText").exists:
            print("   [CHECKER] Terdeteksi masuk ke layar registrasi/buat akun baru. Mengirim tombol BACK untuk kembali...")
            d.press("back")
            time.sleep(2.5)
            continue

        # CASE 0: Batas Harian (Daily Limit)
        if "daily limit" in xml_lower or "batas harian" in xml_lower:
            if clear_any_popup_fast(d):
                continue

        # CASE 1: Sudah masuk ke Beranda utama (Sudah Login)
        if "feed_tab" in xml_lower or "profile_tab" in xml_lower:
            print("   [LOGGED IN] Mendeteksi status sudah login.")
            
            # Cari username element hanya jika berupa TextView (menghindari mendeteksi Logo Instagram yang berupa ImageView di homepage)
            profile_title_elm = None
            for sel in [
                d(resourceId="com.instagram.android:id/action_bar_title", className="android.widget.TextView"),
                d(resourceId="com.instagram.android:id/title_text", className="android.widget.TextView")
            ]:
                if sel.exists:
                    profile_title_elm = sel
                    break
            
            if profile_title_elm:
                try:
                    active_user = profile_title_elm.get_text().strip().lower()
                    print(f"      -> Akun aktif saat ini: '{active_user}'")
                    if ORIGINAL_ACCOUNT_HOLDER[0] is None:
                        ORIGINAL_ACCOUNT_HOLDER[0] = active_user
                    
                    # Jika akun aktif cocok dengan target secara eksak (tanpa @ dan lowercase), login SUKSES!
                    user_clean = username_pencarian.strip().lower().lstrip('@')
                    active_clean = active_user.strip().lower().lstrip('@')
                    if user_clean == active_clean:
                        print(f" [SUKSES] Sudah login di akun yang benar: '{active_user}'.")
                        success = True
                        break
                    else:
                        # Jika akun salah ini sudah dikunjungi sebelumnya, hentikan loop
                        seen_wrong_users[active_user] = seen_wrong_users.get(active_user, 0) + 1
                        if seen_wrong_users[active_user] >= 6:
                            error_msg = f"Loop terdeteksi: Akun aktif saat ini '{active_user}' tidak cocok dengan parameter '{username_pencarian}'."
                            print(f"   [BATAL] {error_msg}")
                            print("           Harap periksa kembali penulisan username di parameter perintah Anda.")
                            log_error(log_id, error_msg)
                            break

                        # Akun aktif salah, buka switcher akun dengan long click tab profil
                        print(f"      -> Akun aktif '{active_user}' tidak cocok. Membuka switcher akun...")
                        profile_tab = d(resourceId="com.instagram.android:id/profile_tab")
                        if profile_tab.exists:
                            profile_tab.long_click()
                        else:
                            d.click(int(width * 0.9), int(height * 0.93))
                            time.sleep(0.5)
                            d.long_click(int(width * 0.9), int(height * 0.93), duration=1.0)
                        time.sleep(3.0)
                        continue
                except Exception as get_txt_err:
                    print(f"      -> Gagal mendapatkan teks username (menunggu halaman stabil): {get_txt_err}")
                    time.sleep(1.5)
                    continue
            else:
                # Jika belum di halaman profil, klik tab profil untuk memeriksa username aktif
                print("      -> Mengklik tab profil untuk memverifikasi username...")
                profile_tab = d(resourceId="com.instagram.android:id/profile_tab")
                if profile_tab.exists:
                    profile_tab.click()
                else:
                    d.click(int(width * 0.9), int(height * 0.93))
                time.sleep(2.5)
                continue

        # CASE 1.6: Pilihan Tambah Akun (Log in to existing vs Create new account)
        if "existing" in xml_lower or "sudah ada" in xml_lower or "akun lama" in xml_lower or "akun lain" in xml_lower or "another account" in xml_lower:
            print("   [ADD ACCOUNT OPTION] Dialog pilihan login akun lama terdeteksi.")
            clicked_opt = False
            for opt_regex in [
                r"(?i).*(masuk ke akun yang sudah ada|log in to existing account|log into existing account|log in to an existing account|Masuk ke akun lama).*",
                r"(?i).*(masuk ke akun lama|log in to existing|log into existing|masuk ke akun lain|log in to another account|log into another account).*"
            ]:
                btn = find_element_by_text_or_desc(d, opt_regex, regex=True)
                if btn and btn.exists:
                    print(f"      -> Mengklik pilihan: '{btn.get_text() if btn.exists else 'Masuk ke akun lama'}'")
                    btn.click()
                    clicked_opt = True
                    time.sleep(4.0)
                    break
            if not clicked_opt:
                # Fallback contains
                for kw in ["sudah ada", "existing account", "akun lama", "log in to", "akun lain", "another account"]:
                    btn = find_element_by_text_or_desc(d, kw, contains=True)
                    if btn and btn.exists:
                        print(f"      -> Mengklik pilihan contains '{kw}'...")
                        btn.click()
                        clicked_opt = True
                        time.sleep(4.0)
                        break
            continue

        # CASE 1.5: Switcher Akun Terbuka (Account Switcher Bottom Sheet)
        is_switcher_open = (
            ("tambah" in xml_lower and "akun" in xml_lower) or 
            ("add" in xml_lower and "account" in xml_lower) or 
            ("log in or create" in xml_lower) or 
            ("masuk atau buat" in xml_lower)
        )
        is_options_dialog = "existing" in xml_lower or "sudah ada" in xml_lower or "akun lama" in xml_lower
        
        if is_switcher_open and not is_options_dialog:
            print("   [SWITCHER] Switcher akun terdeteksi.")
            target_on_switcher = find_element_by_text_or_desc(d, username_pencarian)
            if target_on_switcher and target_on_switcher.exists:
                print(f"      -> Menemukan akun target '{username_pencarian}' di switcher. Klik untuk beralih...")
                target_on_switcher.click()
                time.sleep(6.0)
                continue
            
            # Jika tidak ada di list, klik "Tambahkan akun"
            add_clicked = False
            for add_regex in [
                r"(?i).*(tambahkan akun|tambah akun|add account|add instagram account).*",
                r"(?i).*(log in or create|masuk atau buat).*"
            ]:
                btn = find_element_by_text_or_desc(d, add_regex, regex=True)
                if btn and btn.exists:
                    print(f"      -> Mengklik tombol '{btn.get_text() if btn.exists else 'Tambahkan akun'}'...")
                    btn.click()
                    add_clicked = True
                    time.sleep(3.0)
                    break
            if not add_clicked:
                for kw in ["tambahkan akun", "tambah akun", "add account", "add instagram account"]:
                    btn = find_element_by_text_or_desc(d, kw, contains=True)
                    if btn and btn.exists:
                        print(f"      -> Mengklik tombol contains '{kw}'...")
                        btn.click()
                        add_clicked = True
                        time.sleep(3.0)
                        break
            if not add_clicked:
                print("      -> Klik fallback koordinat Tambahkan Akun...")
                d.click(int(width * 0.5), int(height * 0.90))
                time.sleep(3.0)
            continue

        # CASE 2: Interupsi dialog izin akses / permission sistem
        if "permission" in pkg or "grant" in pkg or "allow" in xml_lower or "izinkan" in xml_lower:
            if handle_system_dialogs_and_permissions(d):
                continue

        # CASE 3: Pop-up Google Credential Manager (Smart Lock)
        if "credentialmanager" in pkg or "smart lock" in xml_lower or "credentialchooser" in xml_lower or "google.android.gms" in pkg:
            print("   [GOOGLE Smart Lock] Dialog credential terdeteksi. Membatalkan otomatis agar login ulang...")
            batal_clicked = False
            for text_batal in ["Batal", "Cancel", "Tutup", "Close", "None of the above", "Tidak ada di atas", "Kembali", "Jangan sekarang", "Lain kali", "Tidak", "Tidak, terima kasih", "No thanks", "Never", "No"]:
                btn = find_element_by_text_or_desc(d, text_batal, contains=True)
                if btn and btn.exists:
                    print(f"      -> Mengklik tombol pembatalan: '{text_batal}'")
                    btn.click()
                    time.sleep(2.0)
                    batal_clicked = True
                    break
            if not batal_clicked:
                print("      -> Tombol pembatalan tidak ditemukan di layar, menekan tombol BACK fisik...")
                d.press("back")
                time.sleep(2.0)
            continue

        # CASE 3.5: Layar Akun Tertaut Tunggal (Single Saved Account Landing Page)
        # Deteksi via tombol Settings/titik tiga di kanan atas dan adanya tombol Continue / Use another profile
        is_single_saved_landing = (d(description="Settings").exists or d(text="Settings").exists) and (
            d(text="Continue").exists or d(text="Lanjutkan").exists or 
            d(text="Use another profile").exists or d(text="Gunakan profil lain").exists or
            d(textContains="Continue as").exists or d(textContains="Lanjutkan sebagai").exists
        )
        
        if is_single_saved_landing:
            print("   [SINGLE SAVED LANDING] Terdeteksi layar landing satu-ketuk akun tertaut.")
            
            # Cek apakah nama akun target sama dengan akun tertaut yang ditawarkan (Continue as <target>)
            target_matched = False
            continue_btn = None
            for sel in [
                d(text=f"Continue as {username_pencarian}"),
                d(text=f"Lanjutkan sebagai {username_pencarian}"),
                d(textContains=username_pencarian)
            ]:
                if sel.exists:
                    continue_btn = sel
                    target_matched = True
                    break
            
            if target_matched and continue_btn:
                print(f"      -> Akun target '{username_pencarian}' cocok. Mengklik Continue...")
                continue_btn.click()
                time.sleep(6.0)
                continue
            
            # Jika akun tidak cocok, klik opsi gunakan profil lain untuk masuk ke form login
            print("      -> Akun tertaut tidak cocok. Mencari opsi 'Use another profile' atau 'Gunakan profil lain'...")
            another_clicked = False
            for text_target in [
                "Use another profile", "Gunakan profil lain", 
                "Gunakan akun lain", "Use another account",
                "Log in to another account", "Masuk ke akun lain"
            ]:
                btn = find_element_by_text_or_desc(d, f"(?i).*{text_target}.*", regex=True)
                if btn and btn.exists:
                    print(f"      -> Mengklik pilihan: '{text_target}' untuk menuju form login...")
                    btn.click()
                    another_clicked = True
                    time.sleep(4.0)
                    break
            
            if not another_clicked:
                # Cari secara dinamis semua elemen clickable yang berisi kata kunci pengalihan akun
                try:
                    for i in range(d(clickable=True).count):
                        elem = d(clickable=True)[i]
                        if elem.exists:
                            txt = (elem.info.get('text', '') or elem.info.get('contentDescription', '') or '').lower()
                            if any(kw in txt for kw in ["lain", "another", "switch", "ganti", "bukan", "not ", "existing"]):
                                print(f"      -> Menemukan elemen pengalihan dinamis: '{txt}'. Mengklik...")
                                elem.click()
                                another_clicked = True
                                time.sleep(4.0)
                                break
                except Exception as dyn_err:
                    print(f"      -> Gagal mencari elemen pengalihan dinamis: {dyn_err}")
            
            if not another_clicked:
                single_saved_landing_attempts += 1
                if single_saved_landing_attempts == 1:
                    print("      -> Tombol tidak terdeteksi, klik koordinat fallback 1 (0.5, 0.65)...")
                    d.click(int(width * 0.5), int(height * 0.65))
                elif single_saved_landing_attempts == 2:
                    print("      -> Tombol tidak terdeteksi, klik koordinat fallback 2 (0.5, 0.70)...")
                    d.click(int(width * 0.5), int(height * 0.70))
                elif single_saved_landing_attempts == 3:
                    print("      -> Tombol tidak terdeteksi, klik koordinat fallback 3 (0.5, 0.60)...")
                    d.click(int(width * 0.5), int(height * 0.60))
                elif single_saved_landing_attempts == 4:
                    print("      -> Tombol tidak terdeteksi, klik koordinat fallback 4 (0.5, 0.75)...")
                    d.click(int(width * 0.5), int(height * 0.75))
                elif single_saved_landing_attempts == 5:
                    print("      -> Tombol tidak terdeteksi, mengirim tombol BACK...")
                    d.press("back")
                else:
                    print("      [-] ERROR: Terjebak di layar Single Saved Landing tanpa opsi pengalihan yang berfungsi.")
                    raise RuntimeError("Terjebak di layar Single Saved Landing.")
                time.sleep(4.0)
            else:
                # Reset counter jika berhasil dialihkan
                single_saved_landing_attempts = 0
            continue

        # CASE 4: Layar pemilihan akun tertaut (Saved Account)
        is_saved_accounts_screen = False
        for kw_regex in [
            r"(?i).*(pilih akun|choose account).*",
            r"(?i).*(masuk ke akun lain|log in to another account|log into another account).*",
            r"(?i).*(gunakan akun lain|use another account|gunakan profil lain|use another profile).*",
            r"(?i).*(buat akun baru|create new account).*"
        ]:
            if d(textMatches=kw_regex).exists or d(descriptionMatches=kw_regex).exists:
                is_saved_accounts_screen = True
                break
        if not is_saved_accounts_screen:
            if username_pencarian.lower() in xml_lower and ("login" in xml_lower or "masuk" in xml_lower or "account" in xml_lower) and not ("kata sandi" in xml_lower or "password" in xml_lower):
                is_saved_accounts_screen = True
                
        # Jaring pengaman: Jika ada EditText di layar, ini adalah form login/kredensial, BUKAN list akun tersimpan!
        if d(className="android.widget.EditText").exists:
            is_saved_accounts_screen = False
        
        if is_saved_accounts_screen:
            print("   [SAVED ACCOUNTS LIST] Layar pemilihan akun terdeteksi.")
            
            # HP Baru / Fresh landing page check: Jika ada tombol Log in / Masuk tanpa kolom EditText
            landing_login_btn = None
            for sel in [d(text="Log in"), d(text="Masuk"), d(description="Log in"), d(description="Masuk")]:
                if sel.exists:
                    landing_login_btn = sel
                    break
            
            if landing_login_btn and not d(className="android.widget.EditText").exists:
                print("      -> Mendeteksi landing page HP baru. Mengklik tombol 'Log in'...")
                try:
                    landing_login_btn.click()
                    time.sleep(4.0)
                    continue
                except:
                    pass

            user_btn = find_element_by_text_or_desc(d, username_pencarian)
            if not user_btn or not user_btn.exists:
                user_btn = find_element_by_text_or_desc(d, username_pencarian, contains=True)
            if user_btn and user_btn.exists:
                print(f"      -> Menemukan akun target '{username_pencarian}' di daftar. Klik untuk masuk...")
                user_btn.click()
                time.sleep(5.0)
                continue
                
            another_clicked = False
            for text_target in [
                "Masuk ke akun lain", "Log in to another account", "Log into another account",
                "Gunakan akun lain", "Use another account", "Gunakan profil lain", "Use another profile", 
                "Log in to another profile", "Log into another profile", "Masuk ke akun lama"
            ]:
                btn = find_element_by_text_or_desc(d, f"(?i).*{text_target}.*", regex=True)
                if btn and btn.exists:
                    print(f"      -> Mengklik opsi akun lain: '{text_target}'...")
                    btn.click()
                    another_clicked = True
                    time.sleep(4.0)
                    break
            
            if not another_clicked:
                another_regex = r"(?i).*(masuk ke akun lain|log in to another account|log into another account|gunakan akun lain|use another account|gunakan profil lain|use another profile|log in to another profile).*"
                btn = find_element_by_text_or_desc(d, another_regex, regex=True)
                if btn and btn.exists:
                    print(f"      -> Mengklik opsi akun lain via regex...")
                    btn.click()
                    another_clicked = True
                    time.sleep(4.0)
            
            if not another_clicked:
                print("      -> Klik fallback koordinat untuk akun lain (avoiding create account)...")
                d.click(int(width * 0.5), int(height * 0.76))
                time.sleep(4.0)
            continue

        # CASE 4.5: Dialog Recover Your Account (Kredensial Salah / Rusak)
        if "recover your account" in xml_lower or "no longer connected to an account" in xml_lower:
            print("   [KREDENSIAL SALAH] Terdeteksi dialog 'Recover your account'. Akun/password tidak valid.")
            cancel_btn = None
            for sel in [d(text="CANCEL"), d(text="Cancel"), d(description="CANCEL"), d(description="Cancel")]:
                if sel.exists:
                    cancel_btn = sel
                    break
            
            if cancel_btn:
                print("      -> Mengklik CANCEL...")
                cancel_btn.click()
            else:
                d.press("back")
            time.sleep(2.0)
            print("      -> Menghentikan bot karena kredensial bermasalah.")
            original_account = ORIGINAL_ACCOUNT_HOLDER[0]
            if d and original_account and original_account.lower() != user.lower():
                try:
                    _kembali_ke_akun_asal(d, original_account, width, height)
                except Exception as rec_err:
                    print(f"   -> Gagal memulihkan ke akun asal: {rec_err}")
            sys.exit(1)

        # CASE 4.6: Dialog Can't Find Account (Akun Tidak Ditemukan)
        is_cant_find_account = (
            "can't find account" in xml_lower or 
            "tidak dapat menemukan akun" in xml_lower or 
            "we can't find an account" in xml_lower or
            "tidak menemukan akun" in xml_lower
        )
        if is_cant_find_account:
            error_msg = f"Akun tidak ditemukan: Instagram tidak dapat menemukan akun '{username_pencarian}'."
            print(f"   [ACCOUNT NOT FOUND] {error_msg}")
            
            # Dismiss dialog by clicking TRY AGAIN or Cancel or pressing back
            dismiss_btn = None
            for txt in ["Try again", "Try Again", "Coba lagi", "Coba Lagi", "Batal", "Cancel"]:
                sel = find_element_by_text_or_desc(d, f"(?i).*{txt}.*", regex=True)
                if sel and sel.exists:
                    dismiss_btn = sel
                    break
            if dismiss_btn:
                print(f"      -> Mengklik tombol: '{dismiss_btn.get_text() if dismiss_btn.exists else 'Try Again'}'...")
                dismiss_btn.click()
            else:
                d.press("back")
            time.sleep(2.0)
            
            # Kembalikan ke akun asal
            original_account = ORIGINAL_ACCOUNT_HOLDER[0]
            if d and original_account and original_account.lower() != user.lower():
                try:
                    _kembali_ke_akun_asal(d, original_account, width, height)
                except Exception as rec_err:
                    print(f"   -> Gagal memulihkan ke akun asal: {rec_err}")
            
            if log_id:
                log_error(log_id, error=error_msg)
            sys.exit(1)

        # CASE 4.7: Dialog Incorrect Password (Sandi Salah)
        is_incorrect_password = (
            "incorrect password" in xml_lower or 
            "sandi salah" in xml_lower or 
            "kata sandi salah" in xml_lower or
            "password yang anda masukkan salah" in xml_lower or
            "kata sandi yang anda masukkan salah" in xml_lower or
            "incorrect password for" in xml_lower
        )
        if is_incorrect_password:
            error_msg = f"Sandi salah: Kata sandi yang dimasukkan salah untuk akun '{username_pencarian}'."
            print(f"   [WRONG PASSWORD] {error_msg}")
            
            # Tutup dialog dengan mengklik OK, Lupa Sandi, atau menekan tombol back
            dismiss_btn = None
            for txt in ["OK", "Ok", "Coba lagi", "Try again", "Try Again", "Batal", "Cancel"]:
                sel = find_element_by_text_or_desc(d, f"(?i).*{txt}.*", regex=True)
                if sel and sel.exists:
                    dismiss_btn = sel
                    break
            if dismiss_btn:
                print(f"      -> Mengklik tombol penutup dialog: '{dismiss_btn.get_text() if dismiss_btn.exists else 'OK'}'...")
                dismiss_btn.click()
            else:
                d.press("back")
            time.sleep(2.0)
            
            # Kembalikan ke akun asal
            original_account = ORIGINAL_ACCOUNT_HOLDER[0]
            if d and original_account and original_account.lower() != user.lower():
                try:
                    _kembali_ke_akun_asal(d, original_account, width, height)
                except Exception as rec_err:
                    print(f"   -> Gagal memulihkan ke akun asal: {rec_err}")
            
            if log_id:
                log_error(log_id, error=error_msg)
            sys.exit(1)

        # CASE 4.75: Dialog Akun Ditangguhkan / Dinonaktifkan (Account Disabled/Suspended)
        is_account_disabled = (
            "has been disabled" in xml_lower or 
            "telah dinonaktifkan" in xml_lower or 
            "suspended" in xml_lower or
            "ditangguhkan" in xml_lower or
            "violating our terms" in xml_lower or
            "melanggar ketentuan" in xml_lower
        )
        if is_account_disabled:
            error_msg = f"Akun ditangguhkan: Akun '{username_pencarian}' diblokir atau ditangguhkan oleh Instagram."
            print(f"   [ACCOUNT BLOCKED] {error_msg}")
            
            # Tutup dialog dengan menekan back
            d.press("back")
            time.sleep(2.0)
            
            # Kembalikan ke akun asal
            original_account = ORIGINAL_ACCOUNT_HOLDER[0]
            if d and original_account and original_account.lower() != user.lower():
                try:
                    _kembali_ke_akun_asal(d, original_account, width, height)
                except Exception as rec_err:
                    print(f"   -> Gagal memulihkan ke akun asal: {rec_err}")
            
            if log_id:
                log_error(log_id, error=error_msg)
            sys.exit(1)

        # CASE 4.8: Penawaran Save Login Info (Simpan Info Login)
        if "save login info" in xml_lower or "save your login info" in xml_lower or "simpan info login" in xml_lower or "simpan informasi login" in xml_lower:
            print("   [SAVE LOGIN INFO] Layar penawaran simpan info login terdeteksi.")
            not_now_clicked = False
            for not_now_text in ["Not now", "Lain kali", "Jangan sekarang"]:
                btn = find_element_by_text_or_desc(d, f"(?i).*{not_now_text}.*", regex=True)
                if btn and btn.exists:
                    print(f"      -> Mengklik tombol '{not_now_text}'...")
                    btn.click()
                    not_now_clicked = True
                    time.sleep(4.0)
                    break
            if not not_now_clicked:
                btn = find_element_by_text_or_desc(d, r"(?i).*(not now|lain kali|jangan sekarang).*", regex=True)
                if btn and btn.exists:
                    print(f"      -> Mengklik tombol '{btn.get_text()}' via regex...")
                    btn.click()
                    not_now_clicked = True
                    time.sleep(4.0)
            if not not_now_clicked:
                print("      -> Tombol Not Now tidak terdeteksi, mengirim tombol BACK...")
                d.press("back")
                time.sleep(3.0)
            continue

        # CASE 4.85: Penanganan Captcha Instagram (Captcha Screen)
        is_captcha_screen = (
            "enter the characters you see" in xml_lower or
            "real human behind this login" in xml_lower or
            "can't read this?" in xml_lower or
            "use capital letters" in xml_lower or
            "masukkan karakter" in xml_lower
        )
        if is_captcha_screen:
            print("   [⚠️ CAPTCHA DETECTED] Layar verifikasi Captcha terdeteksi.")
            
            # Buat folder captcha/instagram/ jika belum ada
            import os
            captcha_dir = os.path.join("captcha", "instagram")
            try:
                os.makedirs(captcha_dir, exist_ok=True)
            except Exception as dir_err:
                print(f"      -> Gagal membuat direktori captcha: {dir_err}")
            
            # Format nama file: device_id_username.txt
            safe_device = "".join([c for c in device_pilihan if c.isalnum() or c in ("_", "-")])
            safe_user = "".join([c for c in user if c.isalnum() or c in ("_", "-")])
            captcha_file_path = os.path.join(captcha_dir, f"{safe_device}_{safe_user}.txt")
            
            # Buat file jika belum ada, masukkan komentar instruksi
            if not os.path.exists(captcha_file_path):
                try:
                    with open(captcha_file_path, "w", encoding="utf-8") as f:
                        f.write(f"# --- INSTAGRAM LOGIN CAPTCHA SOLVER ---\n")
                        f.write(f"# Perangkat: {device_pilihan}\n")
                        f.write(f"# Akun: {user}\n")
                        f.write(f"# \n")
                        f.write(f"# PETUNJUK PENGISIAN:\n")
                        f.write(f"# 1. Tulis kode captcha di baris kosong paling bawah.\n")
                        f.write(f"# 2. WAJIB tambahkan tanda titik (.) di akhir kode agar bot tahu Anda selesai mengetik.\n")
                        f.write(f"# Contoh: qtwybh.\n")
                        f.write(f"# --------------------------------------\n")
                    print(f"      -> File instruksi dibuat: '{captcha_file_path}'")
                except Exception as file_err:
                    print(f"      -> Gagal menulis file instruksi captcha: {file_err}")
            
            print(f"   [⚠️ ACTION REQUIRED] Silakan buka file '{captcha_file_path}' lalu isi dengan kode Captcha yang tampil di layar HP (akhiri dengan titik '.').")
            
            # Polling loop menunggu input pengguna (maksimal 5 menit / 300 detik)
            captcha_code = ""
            start_wait = time.time()
            wait_timeout = 300  # 5 menit
            last_announce = 0
            
            while time.time() - start_wait < wait_timeout:
                # Cetak log setiap 10 detik
                if time.time() - last_announce >= 10:
                    elapsed = int(time.time() - start_wait)
                    print(f"      -> Menunggu input Captcha di '{captcha_file_path}' (akhiri dengan titik '.') ({elapsed}s/{wait_timeout}s)...")
                    last_announce = time.time()
                
                # Coba baca file
                if os.path.exists(captcha_file_path):
                    try:
                        with open(captcha_file_path, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                        
                        # Filter baris komentar dan baris kosong
                        code_lines = []
                        for line in lines:
                            stripped = line.strip()
                            if stripped and not stripped.startswith("#"):
                                code_lines.append(stripped)
                        
                        if code_lines:
                            temp_code = "".join(code_lines).strip()
                            if temp_code.endswith("."):
                                captcha_code = temp_code[:-1].strip()
                                break
                    except Exception as read_err:
                        print(f"      -> Gagal membaca file captcha: {read_err}")
                
                time.sleep(3.0)
            
            if not captcha_code:
                print("   [TIMEOUT] Pengisian Captcha dibatalkan atau waktu tunggu habis.")
                # Hapus file jika timeout
                try:
                    os.remove(captcha_file_path)
                except:
                    pass
                # Gagal login
                raise TimeoutError("Batas waktu pengisian Captcha terlampaui.")
            
            print(f"   [CAPTCHA] Memproses kode Captcha: '{captcha_code}'...")
            
            # Input kode Captcha ke dalam EditText
            input_success = False
            try:
                # Cari input field untuk captcha
                captcha_input = d(className="android.widget.EditText")
                if captcha_input.exists:
                    print("      -> Mengetik Captcha via EditText...")
                    captcha_input.click()
                    time.sleep(0.5)
                    captcha_input.set_text(captcha_code)
                    time.sleep(1.5)
                    input_success = True
            except Exception as input_err:
                print(f"      -> Gagal mengetik Captcha via element: {input_err}")
            
            if not input_success:
                try:
                    # Fallback klik koordinat input captcha (biasanya di tengah-tengah form)
                    print("      -> Menggunakan koordinat fallback untuk input Captcha (0.5, 0.65)...")
                    d.click(int(width * 0.5), int(height * 0.65))
                    time.sleep(1.0)
                    d.send_keys(captcha_code)
                    time.sleep(1.5)
                    input_success = True
                except Exception as input_err_fallback:
                    print(f"      -> Gagal mengetik Captcha via koordinat fallback: {input_err_fallback}")
            
            # Klik tombol Continue/Lanjutkan
            submit_success = False
            try:
                # Tombol Continue/Lanjutkan
                for btn_label in ["Continue", "Lanjutkan", "Next", "Selanjutnya"]:
                    btn = find_element_by_text_or_desc(d, btn_label)
                    if btn and btn.exists:
                        print(f"      -> Mengklik tombol '{btn_label}'...")
                        btn.click()
                        submit_success = True
                        time.sleep(5.0)
                        break
                
                if not submit_success:
                    # Cari resourceId com.instagram.android:id/primary_button atau com.instagram.android:id/next_button
                    for rid in ["com.instagram.android:id/primary_button", "com.instagram.android:id/next_button"]:
                        btn = d(resourceId=rid)
                        if btn.exists:
                            print(f"      -> Mengklik tombol submit via ID: '{rid}'...")
                            btn.click()
                            submit_success = True
                            time.sleep(5.0)
                            break
            except Exception as submit_err:
                print(f"      -> Gagal mengklik submit Captcha: {submit_err}")
                
            if not submit_success:
                try:
                    # Klik koordinat tombol Continue
                    print("      -> Menggunakan koordinat fallback tombol Continue (0.5, 0.88)...")
                    d.click(int(width * 0.5), int(height * 0.88))
                    time.sleep(5.0)
                except Exception as submit_err_fallback:
                    print(f"      -> Gagal klik submit Captcha via koordinat fallback: {submit_err_fallback}")
            
            # Hapus file .txt setelah submit selesai
            try:
                os.remove(captcha_file_path)
                print(f"      -> File captcha '{captcha_file_path}' dihapus.")
            except Exception as del_err:
                print(f"      -> Warning Gagal menghapus file captcha: {del_err}")
                
            continue

        # CASE 4.9: Pembersihan pop-up / tutorial / onboarding pasca-login
        if clear_any_popup_fast(d):
            continue

        # CASE 5: Form Login Normal (Kolom Input Username & Password)
        is_login_form_screen = False
        if d(className="android.widget.EditText").exists or d.xpath('//*[@password="true"]').exists:
            if not is_saved_accounts_screen:
                is_login_form_screen = True
                
        if is_login_form_screen:
            print("   [LOGIN FORM] Halaman form kredensial terdeteksi.")
            pw_field = None
            pw_field_exists = False
            try:
                pw_field = d.xpath('//*[@password="true"]')
                if pw_field.exists:
                    pw_field_exists = True
            except:
                pass
                
            edit_texts = d(className="android.widget.EditText")
            
            if (edit_texts.exists and edit_texts.count == 1) or (pw_field_exists and (not edit_texts.exists or edit_texts.count < 2)):
                # JIKA ini adalah form login kosong (ada petunjuk username/email/no telp), maka ini BUKAN halaman password akun orang lain!
                is_empty_login_form = any(kw in xml_lower for kw in ["username, email", "nama pengguna", "no. telepon", "phone number", "forgot password", "forgot details"])
                
                if not is_empty_login_form:
                    is_correct_user_screen = username_pencarian.lower() in xml_lower
                    if not is_correct_user_screen:
                        print("      -> Username salah di halaman password. Mencoba ganti akun...")
                        switch_clicked = False
                        for text_target in ["Ganti akun", "Switch accounts", "Masuk ke akun lain", "Log in to another account", "Bukan saya", "Not you"]:
                            btn = find_element_by_text_or_desc(d, f"(?i).*{text_target}.*", regex=True)
                            if btn and btn.exists:
                                print(f"         -> Mengklik tombol ganti akun: '{text_target}'")
                                btn.click()
                                switch_clicked = True
                                time.sleep(4.0)
                                break
                        if not switch_clicked:
                            d.press("back")
                            time.sleep(2.0)
                        continue
            
            user_by_res = d(resourceIdMatches=".*(?i)(username|login_username|email_or_phone|email|phone|phone_number).*")
            pw_by_res = d(resourceIdMatches=".*(?i)(password|password_edit_text).*")
            
            filled = False
            try:
                if user_by_res.exists and pw_by_res.exists:
                    print("      -> Mengisi via Resource ID.")
                    user_by_res.click()
                    time.sleep(0.5)
                    user_by_res.set_text(user)
                    time.sleep(1.0)
                    
                    pw_by_res.click()
                    time.sleep(0.5)
                    pw_by_res.set_text(password)
                    time.sleep(1.5)
                    filled = True
                elif pw_by_res.exists and not user_by_res.exists:
                    print("      -> Mengisi password via Resource ID (akun tersimpan).")
                    pw_by_res.click()
                    time.sleep(0.5)
                    pw_by_res.set_text(password)
                    time.sleep(1.5)
                    filled = True
                    
                if not filled and edit_texts.exists and edit_texts.count > 0:
                    if edit_texts.count == 1:
                        print("      -> Mengisi password akun tersimpan (1 kolom EditText).")
                        edit_texts[0].click()
                        time.sleep(0.5)
                        edit_texts[0].set_text(password)
                        time.sleep(1.5)
                        filled = True
                    elif edit_texts.count >= 2:
                        print("      -> Mengisi username & password (2+ kolom EditText).")
                        edit_texts[0].click()
                        time.sleep(0.5)
                        edit_texts[0].set_text(user)
                        time.sleep(1.0)
                        
                        edit_texts[1].click()
                        time.sleep(0.5)
                        edit_texts[1].set_text(password)
                        time.sleep(1.5)
                        filled = True
            except Exception as fill_err:
                print(f"      -> Warning Gagal mengisi form input secara langsung: {fill_err}")
            
            if not filled:
                try:
                    # Fallback koordinat input
                    print("      -> Menggunakan koordinat fallback input...")
                    d.click(int(width * 0.5), int(height * 0.23))
                    time.sleep(1.0)
                    d.send_keys(user)
                    time.sleep(1.0)
                    d.click(int(width * 0.5), int(height * 0.31))
                    time.sleep(1.0)
                    d.send_keys(password)
                    time.sleep(1.5)
                except Exception as fallback_err:
                    print(f"      -> Warning Gagal menggunakan koordinat fallback input: {fallback_err}")

            # Klik tombol submit login
            login_btn_clicked = False
            try:
                # 1. Cari via Resource ID
                for rid in [
                    "com.instagram.android:id/next_button",
                    "com.instagram.android:id/login_button",
                    "com.instagram.android:id/primary_button",
                    "com.instagram.android:id/button_text"
                ]:
                    if d(resourceId=rid).exists:
                        print(f"      -> Mengklik tombol submit login via ID: '{rid}'")
                        d(resourceId=rid).click()
                        login_btn_clicked = True
                        time.sleep(6.0)
                        break
                
                # 2. Cari via pencocokan eksak (Exact Match)
                if not login_btn_clicked:
                    for btn_txt in ["Log in", "Login", "Log In", "Masuk", "Next", "Selanjutnya"]:
                        btn = find_element_by_text_or_desc(d, btn_txt)
                        if btn and btn.exists:
                            print(f"      -> Mengklik tombol submit login (exact): '{btn_txt}'")
                            btn.click()
                            login_btn_clicked = True
                            time.sleep(6.0)
                            break
                
                # 3. Cari via pencocokan teks (contains=True) sebagai fallback terakhir
                if not login_btn_clicked:
                    for btn_txt in ["Log in", "Login", "Log In", "Masuk", "Next", "Selanjutnya"]:
                        btn = find_element_by_text_or_desc(d, btn_txt, contains=True)
                        if btn and btn.exists:
                            try:
                                el_text = btn.get_text() or ""
                            except:
                                el_text = ""
                            # Jika teks elemen terlalu panjang (lebih dari 15 karakter), abaikan karena kemungkinan itu adalah judul/deskripsi
                            if len(el_text) > 15:
                                continue
                            print(f"      -> Mengklik tombol submit login (contains): '{btn_txt}'")
                            btn.click()
                            login_btn_clicked = True
                            time.sleep(6.0)
                            break
                if not login_btn_clicked:
                    d.press("enter")
                    time.sleep(6.0)
            except Exception as btn_err:
                print(f"      -> Warning Gagal menekan submit login: {btn_err}")
            continue

        # CASE 6: Pop-up Pasca-Login
        any_dismiss = False
        dismiss_keywords = ["not now", "lain kali", "jangan sekarang", "tutup", "close", "batal", "cancel", "lewati", "skip", "paham", "got it"]
        for target in dismiss_keywords:
            if f'text="{target}"' in xml_lower or f'content-desc="{target}"' in xml_lower or f'text="{target.capitalize()}"' in xml_lower or f'text="{target.title()}"' in xml_lower:
                for sel in [d(textMatches=f"(?i)^{target}$"), d(descriptionMatches=f"(?i)^{target}$")]:
                    if sel.exists:
                        print(f"   [POP-UP DISMISS] Mengklik tombol penutup: '{target}'")
                        sel.click()
                        time.sleep(2.0)
                        any_dismiss = True
                        break
                if any_dismiss:
                    break
        if any_dismiss:
            continue

        print("   -> Menunggu halaman memuat / memantau layar...")
        time.sleep(2.0)

    


    # Sapu bersih sisa pop-up pasca login
    if success:
        print("\n--- MEMBERSIHKAN POP-UP PASCA LOGIN ---")
        clear_post_login_popups(d)
        
        print("\n--- MEMASTIKAN BERADA DI BERANDA ---")
        # Periksa activity aktif saat ini untuk memastikan bukan di Reels/Post Detail
        try:
            app_info = d.app_current()
            current_pkg = app_info.get('package', '')
            current_activity = app_info.get('activity', '')
            print(f"   -> Package aktif: '{current_pkg}' | Activity aktif: '{current_activity}'")
            
            if current_pkg == 'com.instagram.android' and 'MainActivity' not in current_activity:
                print(f"   -> Terdeteksi di luar MainActivity (sedang di '{current_activity}'). Mengirim tombol BACK...")
                d.press("back")
                time.sleep(2.5)
        except Exception as e:
            print(f"   -> Gagal memeriksa activity aktif: {e}")

        feed_tab = d(resourceId="com.instagram.android:id/feed_tab")
        if feed_tab.exists:
            print("   -> Mengklik feed_tab untuk kembali ke Beranda...")
            feed_tab.click()
            time.sleep(2.0)
        else:
            print("   -> feed_tab tidak ditemukan via resourceId, klik koordinat kiri bawah...")
            d.click(int(width * 0.1), int(height * 0.93))
            time.sleep(2.0)

        # Lakukan refresh Beranda (Swipe Down)
        print("   -> Melakukan swipe down untuk menyegarkan Beranda (refresh)...")
        d.swipe(0.5, 0.35, 0.5, 0.75, duration=0.20)
        time.sleep(2.5)
            
        # Bersihkan jika ada pop-up lagi setelah pindah ke Beranda
        clear_any_popup_fast(d)
        
        print("\n[FINISH] Proses login selesai secara sukses!")
        if log_id:
            log_complete(log_id, message="Login successful")
        sys.exit(0)
    else:
        print("\n[GAGAL] Batas waktu otentikasi login terlampaui.")
        if log_id:
            log_error(log_id, error="Batas waktu otentikasi login terlampaui")
        original_account = ORIGINAL_ACCOUNT_HOLDER[0]
        if d and original_account and original_account.lower() != user.lower():
            try:
                _kembali_ke_akun_asal(d, original_account, width, height)
            except Exception as rec_err:
                print(f"   -> Gagal memulihkan ke akun asal: {rec_err}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    has_dash = any(arg.startswith('-') for arg in sys.argv[1:])
    if has_dash:
        parser = argparse.ArgumentParser(description="Bot Login Instagram")
        parser.add_argument("--username", "--user", default="", help="Username Instagram")
        parser.add_argument("--password", "--pass", default="", help="Password Instagram")
        parser.add_argument("--device", "--device_id", "--device-id", default="all", help="Device ID")
        args = parser.parse_args()
        USER_AKUN = args.username
        PASSWORD_AKUN = args.password
        device_id = args.device
    else:
        USER_AKUN = sys.argv[1] if len(sys.argv) > 1 else ""
        PASSWORD_AKUN = sys.argv[2] if len(sys.argv) > 2 else ""
        device_id = sys.argv[3] if len(sys.argv) > 3 else "all"

    if USER_AKUN and PASSWORD_AKUN:
        if not device_id:
            device_id = "all"
        run_login_bot(USER_AKUN, PASSWORD_AKUN, device_id)
        sys.exit(0)

    # KONDISI 2: LOCAL / LAPTOP TERMINAL MODE (Interaktif, isatty == True)
    if sys.stdin.isatty():
        try:
            print("\n--- [LOKAL MODE] MENJALANKAN BOT LOGIN SECARA INTERAKTIF ---")
            if not USER_AKUN:
                USER_AKUN = input("Masukkan Username Instagram: ").strip()
            if not PASSWORD_AKUN:
                PASSWORD_AKUN = input("Masukkan Password Instagram: ").strip()
            if not device_id:
                ans_dev = input("Masukkan device ID (kosongkan/tekan Enter untuk 'all'): ").strip()
                device_id = ans_dev if ans_dev else "all"
            run_login_bot(USER_AKUN, PASSWORD_AKUN, device_id)
            sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\nEksekusi dibatalkan oleh user.")
            sys.exit(1)

    # KONDISI 3: SERVER BACKGROUND MODE (Non-TTY, isatty == False)
    else:
        print("\n--- [SERVER MODE] MENJALANKAN BOT LOGIN DI BACKGROUND/CRON ---")
        # Coba baca dari environment variables
        USER_AKUN = os.environ.get("IG_USERNAME", USER_AKUN)
        PASSWORD_AKUN = os.environ.get("IG_PASSWORD", PASSWORD_AKUN)
        device_id = os.environ.get("IG_DEVICE_ID", "all")
        
        # Coba baca dari default_post_config.json
        if (not USER_AKUN or not PASSWORD_AKUN) and os.path.exists("default_post_config.json"):
            try:
                import json
                with open("default_post_config.json", "r") as f:
                    config = json.load(f)
                    USER_AKUN = config.get("username", USER_AKUN)
                    PASSWORD_AKUN = config.get("password", PASSWORD_AKUN)
                    device_id = config.get("device_id", device_id)
                print("   -> Menggunakan konfigurasi dari default_post_config.json")
            except Exception as e:
                print(f"   -> Gagal membaca default_post_config.json: {e}")
                
        if not USER_AKUN or not PASSWORD_AKUN:
            # Fallback default untuk server testing
            USER_AKUN = "lukyytris13"
            PASSWORD_AKUN = "Bryant12345678"
            
        run_login_bot(USER_AKUN, PASSWORD_AKUN, device_id)
        sys.exit(0)