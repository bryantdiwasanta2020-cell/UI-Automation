import time
import threading
import re

def get_current_package_safe(d, timeout=1.5):
    """
    Mengambil package aplikasi aktif dengan jaring pengaman timeout agar tidak menggantung (hang).
    """
    result = {'package': ''}
    def target():
        try:
            result['package'] = d.app_current().get('package', '')
        except:
            pass
            
    t = threading.Thread(target=target)
    t.daemon = True
    t.start()
    t.join(timeout)
    return result['package']

def check_and_clear_daily_limit(d):
    """
    Mendeteksi dan menutup pop-up batas harian Instagram ('reached your daily limit').
    """
    try:
        limit_title = d(textMatches="(?i).*(reached your daily limit|batas harian|daily limit|reached).*")
        if not limit_title.exists:
            limit_title = d(descriptionMatches="(?i).*(reached your daily limit|batas harian|daily limit|reached).*")
            
        if limit_title.exists:
            print(" [Daily Limit] Mendeteksi pop-up batas harian Instagram!")
            
            # Cek jika tombol abaikan (Ignore limit) sudah terlihat langsung di pop-up pertama
            ignore_btn = None
            for regex in [
                r"(?i).*(ignore limit for today|abaikan untuk hari ini|abaikan batas hari ini).*",
                r"(?i).*(ignore limit|abaikan batas|ignore|abaikan).*"
            ]:
                for sel in [d(textMatches=regex), d(descriptionMatches=regex)]:
                    if sel.exists:
                        ignore_btn = sel
                        break
                if ignore_btn:
                    break
                    
            if ignore_btn:
                print(f"   -> Menemukan tombol abaikan langsung di pop-up: '{ignore_btn.info.get('text', 'Ignore limit')}'")
                ignore_btn.click()
                time.sleep(2.5)
                return True
                
            # Jika tidak ada tombol abaikan langsung, coba cari "More options" / "Opsi lainnya"
            more_opt = d(textMatches="(?i).*(more options|opsi lainnya|opsi).*")
            if not more_opt.exists:
                more_opt = d(descriptionMatches="(?i).*(more options|opsi lainnya|opsi).*")
                
            if more_opt.exists:
                print("   -> Mengklik 'More options'...")
                more_opt.click()
                time.sleep(2.5)
                
                # Cari tombol abaikan lagi di dalam submenu
                for regex in [
                    r"(?i).*(ignore limit for today|abaikan untuk hari ini|abaikan batas hari ini).*",
                    r"(?i).*(ignore limit|abaikan batas|ignore|abaikan).*"
                ]:
                    for sel in [d(textMatches=regex), d(descriptionMatches=regex)]:
                        if sel.exists:
                            ignore_btn = sel
                            break
                    if ignore_btn:
                        break
                        
                if ignore_btn:
                    print(f"   -> Mengklik opsi abaikan di submenu: '{ignore_btn.info.get('text', 'Ignore')}'")
                    ignore_btn.click()
                    time.sleep(2.5)
                    return True
                else:
                    print("   -> Tombol abaikan limit tidak ditemukan di submenu, menekan tombol Back...")
                    d.press("back")
                    time.sleep(1.0)
            else:
                print("   -> Tombol 'More options' tidak ditemukan, menekan Back...")
                d.press("back")
                time.sleep(1.0)
    except Exception as e:
        print(f"   -> Error saat membersihkan daily limit: {e}")
    return False

def handle_system_dialogs_and_permissions(d):
    """
    Mendeteksi dan menangani jendela sistem Android, dialog izin akses (permissions),
    atau Google Smart Lock yang menghalangi layar.
    """
    try:
        pkg = get_current_package_safe(d)
        
        # Jika bukan Instagram, bukan launcher bawaan HP, dan bukan systemui
        if pkg and pkg != 'com.instagram.android' and pkg != 'com.android.systemui' and 'launcher' not in pkg.lower():
            print(f" [+] Jendela sistem/non-Instagram terdeteksi: '{pkg}'")
            
            # 1. Cek apakah ini dialog izin akses (permission dialog)
            permission_clicked = False
            
            # Cek via Resource ID resmi terlebih dahulu
            for rid in [
                "com.android.permissioncontroller:id/permission_allow_all_button",
                "com.android.permissioncontroller:id/permission_allow_button",
                "com.android.permissioncontroller:id/permission_allow_foreground_only_button",
                "com.google.android.gms:id/allow",
                "com.google.android.gms:id/btn_allow",
                "com.google.android.gms:id/permission_allow_button",
                "com.google.android.gms:id/accept",
                "android:id/button1"
            ]:
                btn = d(resourceId=rid)
                if btn.exists:
                    print(f"   -> Mengklik izin akses via Resource ID: '{rid}'")
                    try:
                        btn.click()
                        time.sleep(2.0)
                        permission_clicked = True
                        break
                    except:
                        pass
                        
            if not permission_clicked:
                perm_regexes = [
                    r"(?i).*(allow access to all files|izinkan akses ke semua file|allow all|izinkan semua).*",
                    r"(?i).*(allow access to media|izinkan akses ke media|allow access to photos|izinkan akses ke foto|allow access to photos and videos|izinkan akses ke foto dan video|allow access to all photos|izinkan akses ke semua foto).*",
                    r"(?i).*(while using the app|saat aplikasinya digunakan|saat aplikasi digunakan).*",
                    r"(?i).*(allow.*read.*sms|izinkan.*membaca.*sms|allow.*receive.*sms|izinkan.*menerima.*sms).*",
                    r"(?i).*(sms.*consent|sms.*user.*consent|allow.*read.*verification.*code|izinkan.*membaca.*kode.*verifikasi).*",
                    r"(?i).*(autofill|isi.*otomatis|use.*verification.*code|gunakan.*kode.*verifikasi).*",
                    r"(?i).*(allow|izinkan).*",
                    r"(?i).*(only this time|hanya kali ini).*"
                ]
                for regex in perm_regexes:
                    for sel in [d(textMatches=regex), d(descriptionMatches=regex)]:
                        if sel.exists:
                            print(f"   -> Mengklik izin akses mencocokkan: '{regex}'")
                            sel.click()
                            time.sleep(2.0)
                            permission_clicked = True
                            break
                    if permission_clicked:
                        break
            
            # 2. Jika bukan permission dialog tapi aplikasi lain (misal Google Smart Lock), tekan BACK
            if not permission_clicked:
                print("   -> Mengirim tombol BACK untuk menutup dialog sistem...")
                d.press("back")
                time.sleep(2.0)
            return True
    except Exception as e:
        print(f"   -> Error saat memeriksa/menangani dialog sistem: {e}")
    return False

def clear_post_login_popups(d):
    """
    Menyapu bersih segala interupsi pop-up pasca-login secara dinamis
    (seperti 'Lain Kali', 'Not Now', 'Jangan sekarang', 'Paham', 'Got It', 'Skip', dll.)
    sampai aplikasi Instagram stabil di halaman Beranda.
    """
    check_and_clear_daily_limit(d)
    handle_system_dialogs_and_permissions(d)

    print("\n--- MENYAPU INTERUPSI POST-LOGIN & POP-UP TAMBAHAN ---")
    
    max_wait_seconds = 30
    start_time = time.time()
    
    print(" Memulai pemindaian pop-up dinamis (maksimal 30 detik)...")
    
    while time.time() - start_time < max_wait_seconds:
        clicked_any = clear_any_popup_fast(d)
        
        if not clicked_any:
            if (d(resourceId="com.instagram.android:id/feed_tab").exists or 
                d(resourceId="com.instagram.android:id/profile_tab").exists) and not d(className="android.widget.EditText").exists:
                print(" [SUKSES] Beranda utama sudah terlihat dan stabil.")
                break
            time.sleep(1.5)
        else:
            time.sleep(1.0)
        
    print("\n ========================================================")
    print(" [MISSION ACCOMPLISHED] PROSES MEMBERSIHKAN POP-UP SELESAI!")
    print("======================================================== \n")

def clear_any_popup_fast(d):
    """
    Melakukan pemindaian cepat satu kali (tanpa looping/sleep lama) 
    untuk menutup pop-up mengganggu yang tiba-tiba muncul di layar.
    Menggunakan XML dump agar sangat cepat dan anti-hang.
    """
    try:
        xml_src = d.dump_hierarchy()
    except Exception as e:
        print(f' error apa {e}')
        return False
    
    xml_lower = xml_src.lower()

    # Jangan bersihkan pop-up jika ini adalah dialog konfirmasi Logout atau Hapus Akun resmi
    if any(kw in xml_lower for kw in [
        "log out of", "keluar dari", "any drafts you've saved", "draf yang anda simpan",
        "remove account", "hapus akun", "remove profile", "hapus profil"
    ]):
        return False

    try:
        # 1. Cek batas harian
        if "daily limit" in xml_lower or "batas harian" in xml_lower:
            if check_and_clear_daily_limit(d):
                return True

        # 2. Cek jendela sistem & dapatkan activity aktif
        current_app = {}
        try:
            current_app = d.app_current()
        except:
            pass
        pkg = current_app.get('package', '')
        act = current_app.get('activity', '')
        
        if pkg and pkg != 'com.instagram.android' and pkg != 'com.android.systemui' and 'launcher' not in pkg.lower():
            if handle_system_dialogs_and_permissions(d):
                return True
 
        # 2.5. Cek layar penyiapan layanan lokasi (Location Services onboarding)
        if any(kw in xml_lower for kw in ["location services", "access your location", "layanan lokasi", "akses lokasi anda"]):
            for btn_txt in ["Continue", "Lanjutkan"]:
                btn = d(text=btn_txt)
                if btn.exists:
                    print(f" [Auto-Dismiss Fast] Mengklik tombol izin lokasi: '{btn_txt}'")
                    btn.click()
                    time.sleep(2.0)
                    # Langsung bersihkan dialog perizinan sistem Android setelah klik Continue
                    handle_system_dialogs_and_permissions(d)
                    return True

        is_in_main = "mainactivity" in act.lower() if act else True
 
        # Tentukan apakah ada EditText di layar (berarti sedang di form input/editor)
        has_edit_text = d(className="android.widget.EditText").exists
 
        # 3. Cari tombol dismiss reguler yang aman (diperbolehkan meskipun ada EditText)
        safe_dismiss_keywords = ["not now", "lain kali", "jangan sekarang", "nanti saja", "no thanks", "no, thanks", "no, thank you", "lewati", "skip", "paham", "got it", "ok", "oke", "agree", "setuju"]
        for target in safe_dismiss_keywords:
            if target in xml_lower:
                clicked = False
                for sel in [d(textMatches=f"(?i)^\\s*{re.escape(target)}\\s*$"), d(descriptionMatches=f"(?i)^\\s*{re.escape(target)}\\s*$")]:
                    if sel.exists:
                        print(f" [Auto-Dismiss Fast] Mengklik tombol dismiss aman (exact): '{target}'")
                        sel.click()
                        time.sleep(1.5)
                        clicked = True
                        break
                        
                if not clicked:
                    # Fallback jika matches tidak ketemu tapi contains ada
                    # Hanya gunakan contains untuk keyword yang panjangnya >= 5 karakter (menghindari kecocokan substring acak seperti 'ok' di 'books')
                    if len(target) >= 5:
                        for sel_contains in [d(textContains=target), d(descriptionContains=target)]:
                            if sel_contains.exists:
                                try:
                                    txt_val = sel_contains.info.get('text', '') or sel_contains.info.get('contentDescription', '') or ''
                                    if len(txt_val.strip()) <= 25:
                                        print(f" [Auto-Dismiss Fast] Mengklik tombol dismiss aman (contains): '{txt_val}'")
                                        sel_contains.click()
                                        time.sleep(1.5)
                                        clicked = True
                                        break
                                except:
                                    pass
                if clicked:
                    return True
 
        # Langkah sensitif (draf/kamera, tombol close/cancel, resource_id negatif) hanya dijalankan jika TIDAK ada EditText
        # Dan untuk tombol dismiss sensitif / resource_id negatif, kita hanya bersihkan jika berada di MainActivity (bukan sedang di form login)
        if not has_edit_text:
            # 4. Dialog draf/kamera khusus
            special_keywords = ["archive", "arsip", "camera", "kamera", "reel", "cerita", "story", "draf", "draft"]
            if any(kw in xml_lower for kw in special_keywords):
                for draft_btn_text in ["mulai baru", "start new", "hapus draf", "discard draft", "hapus", "discard"]:
                    if draft_btn_text in xml_lower:
                        for sel in [d(textMatches=f"(?i)^\\s*{re.escape(draft_btn_text)}\\s*$"), d(descriptionMatches=f"(?i)^\\s*{re.escape(draft_btn_text)}\\s*$")]:
                            if sel.exists:
                                print(f" [Auto-Dismiss Fast] Mengklik tombol draf/kamera khusus: '{draft_btn_text}'")
                                sel.click()
                                time.sleep(1.5)
                                return True
 
            # 5. Cari tombol dismiss sensitif/berbahaya (seperti close, cancel, tutup, batal)
            # Hanya jalankan jika kita berada di MainActivity (bukan sedang login/ganti akun)
            if is_in_main:
                dangerous_dismiss_keywords = ["tutup", "close", "batal", "cancel", "tidak"]
                for target in dangerous_dismiss_keywords:
                    if target in xml_lower:
                        for sel in [d(textMatches=f"(?i)^\\s*{re.escape(target)}\\s*$"), d(descriptionMatches=f"(?i)^\\s*{re.escape(target)}\\s*$")]:
                            if sel.exists:
                                print(f" [Auto-Dismiss Fast] Mengklik tombol dismiss sensitif: '{target}' (Activity: {act})")
                                sel.click()
                                time.sleep(1.5)
                                return True
 
                # 6. Cek resource-id penting jika ada di XML
                resource_ids = [
                    "igds_headline_secondary_action_text_button",
                    "skip_button",
                    "igds_alert_dialog_cancel_button",
                    "igds_headline_primary_action_button",
                    "negative_button",
                    "button_negative"
                ]
                for res_id in resource_ids:
                    if res_id in xml_lower:
                        try:
                            sel = d(resourceIdMatches=f".*{res_id}.*")
                            if sel.exists:
                                print(f" [Auto-Dismiss Fast] Mengklik tombol via Resource ID: '{res_id}' (Activity: {act})")
                                sel.click()
                                time.sleep(1.5)
                                return True
                        except:
                            pass

    except Exception as e:
        print(f" [Auto-Dismiss Fast] Gagal memproses popup: {e}")
        
    return False
