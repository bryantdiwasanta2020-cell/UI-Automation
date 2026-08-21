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
    threads = []
    print(f"[*] Menjalankan {target_func.__name__} secara paralel pada device: {devices}")
    for dev in devices:
        t = threading.Thread(target=target_func, args=args, kwargs={**kwargs, "device_pilihan": dev})
        threads.append(t)
        t.start()
        time.sleep(1.0)
    for t in threads:
        t.join()


def checker(d):
    print('--- MENGECEK POPUP PADA INSTAGRAM ---')
    clear_any_popup_fast(d)
    print('--- MENCEK BATAS HARIAN INSTAGRAM ---')
    check_and_clear_daily_limit(d)
    print('--- MENCEK POPUP LOGIN INSTAGRAM ---')
    clear_post_login_popups(d)


# Import switch_instagram_account from switch_akun_ig
try:
    from switch_akun_ig import switch_instagram_account
except ImportError:
    def switch_instagram_account(target_username, device_pilihan="all"): return False

# ========================================================
# HELPER: KEMBALI KE BERANDA UTAMA
# ========================================================
def _kembali_ke_beranda(d, width, height):
    home_clicked = False
    for i in range(4):
        btn_home = None
        for rid in ["com.instagram.android:id/feed_tab", "com.instagram.android:id/home_tab"]:
            if d(resourceId=rid).exists:
                btn_home = d(resourceId=rid)
                break
        if not btn_home:
            for desc in ["Beranda", "Home", "Feed"]:
                el = d(descriptionMatches=f"(?i)^({desc}|tab {desc}|{desc} tab)$", packageName="com.instagram.android")
                if el.exists:
                    btn_home = el
                    break
        if btn_home:
            try:
                btn_home.click()
                home_clicked = True
                print("      -> Tab Beranda terdeteksi dan diklik.")
                break
            except Exception as e:
                print(f"      -> Gagal mengklik tab Beranda: {e}")
        print(f"      -> Tab Beranda belum terlihat, menekan BACK ke-{i+1}...")
        d.press("back")
        time.sleep(2.0)
    if not home_clicked:
        print("      -> Mengklik tab Beranda via koordinat fallback...")
        d.click(int(width * 0.095), int(height * 0.918))
    time.sleep(2.0)
    print("      -> Melakukan swipe down untuk me-refresh Beranda...")
    d.swipe(0.5, 0.35, 0.5, 0.75, duration=0.20)
    time.sleep(2.5)
    clear_any_popup_fast(d)


def find_element(d, descriptions=[], texts=[], resource_ids=[]):
    """
    Helper function to find UI elements with multiple fallback selectors.
    """
    for res_id in resource_ids:
        try:
            if d(resourceId=res_id).exists:
                return d(resourceId=res_id)
        except:
            pass
            
    for desc in descriptions:
        try:
            if d(description=desc).exists:
                return d(description=desc)
            if d(descriptionContains=desc).exists:
                return d(descriptionContains=desc)
        except:
            pass
            
    for text in texts:
        try:
            if d(text=text).exists:
                return d(text=text)
            if d(textContains=text).exists:
                return d(textContains=text)
        except:
            pass
            
    return None


def clear_popups_post(d):
    try:
        width, height = d.window_size()
    except Exception:
        width, height = 1080, 1920

    # Cek batas harian (Daily Limit)
    try:
        limit_title = d(textMatches="(?i).*(reached your daily limit|batas harian).*")
        more_opt = d(textMatches="(?i).*(more options|opsi lainnya).*")
        if limit_title.exists:
            print("      [Daily Limit] Mendeteksi pop-up batas harian Instagram!")
            if more_opt.exists:
                print("         -> Mengklik 'More options'...")
                more_opt.click()
                time.sleep(2.0)
                
                ignore_btn = None
                for regex in [r"(?i).*(ignore limit for today|abaikan untuk hari ini).*", r"(?i).*(ignore limit|abaikan batas).*"]:
                    sel = d(textMatches=regex) or d(descriptionMatches=regex)
                    if sel.exists:
                        ignore_btn = sel
                        break
                if ignore_btn:
                    print(f"         -> Mengklik opsi abaikan: 'Ignore limit'")
                    ignore_btn.click()
                    time.sleep(2.0)
                    return True
                else:
                    d.press("back")
                    time.sleep(1.0)
            else:
                d.press("back")
                time.sleep(1.0)
    except Exception as e:
        print(f"      -> Error saat membersihkan daily limit: {e}")
        
    # Cek jika layar terhalang oleh Google Smart Lock atau jendela sistem/credential chooser lain
    try:
        current_app = d.app_current()
        pkg = current_app.get('package', '')
        if pkg and pkg != 'com.instagram.android' and pkg != 'com.android.systemui' and pkg != 'com.sec.android.app.launcher' and 'launcher' not in pkg.lower():
            print(f"      -> Mendeteksi jendela sistem/non-Instagram: '{pkg}'. Mengirim tombol BACK untuk menutup dialog...")
            d.press("back")
            time.sleep(2.5)
            # Coba cari lagi setelah ditekan BACK
            current_app = d.app_current()
            pkg = current_app.get('package', '')
            if pkg == 'com.instagram.android':
                print("      -> Berhasil kembali ke Instagram.")
            else:
                return
    except Exception as err:
        print(f"      Gagal memeriksa app_current: {err}")
        
    # Coba cari tombol penutup persis terlebih dahulu (sangat handal & instan)
    for target in ["Lain kali", "Lain Kali", "Not Now", "Not now", "Jangan sekarang", "Jangan Sekarang", "Nanti saja", "Nanti Saja", "Tutup", "Close", "OK", "Oke", "Got it", "Got It"]:
        btn = d(text=target)
        if btn.exists:
            print(f"      -> Mendeteksi pop-up pengganggu persis '{target}'. Mengklik...")
            try:
                btn.click()
                time.sleep(1.2)
                return
            except Exception:
                pass
        btn_desc = d(description=target)
        if btn_desc.exists:
            print(f"      -> Mendeteksi pop-up pengganggu persis description '{target}'. Mengklik...")
            try:
                btn_desc.click()
                time.sleep(1.2)
                return
            except Exception:
                pass
        
    matches = []
    
    # 1. Cari via textMatches (Case-Insensitive Regex persis untuk menghindari salah klik kata seperti 'notification'/'phone number')
    try:
        selector_text = d(textMatches="(?i)^\\s*(not[- ]?now|lain[- ]?kali|jangan[- ]?sekarang|tutup|close|nanti saja|no[- ]?thanks|no|tidak|ok|oke|got[- ]?it)\\s*$")
        for i in range(selector_text.count):   
            elem = selector_text[i]
            if elem.exists:
                info = elem.info
                bounds = info.get('bounds')
                if bounds:
                    w = bounds['right'] - bounds['left']
                    h = bounds['bottom'] - bounds['top']
                    x_center = (bounds['left'] + bounds['right']) // 2
                    y_center = (bounds['top'] + bounds['bottom']) // 2
                    if w > 0 and h > 0 and 0 < x_center < width and 0 < y_center < height:
                        txt_val = info.get('text', '') or ''
                        if len(txt_val) < 30:
                            matches.append((elem, x_center, y_center, txt_val))
    except Exception as e:
        print(f"      Gagal mencari via textMatches: {e}")
        
    # 2. Cari via descriptionMatches (Case-Insensitive Regex persis)
    try:
        selector_desc = d(descriptionMatches="(?i)^\\s*(not[- ]?now|lain[- ]?kali|jangan[- ]?sekarang|tutup|close|nanti saja|no[- ]?thanks|no|tidak|ok|oke|got[- ]?it)\\s*$")
        for i in range(selector_desc.count):
            elem = selector_desc[i]
            if elem.exists:
                info = elem.info
                bounds = info.get('bounds')
                if bounds:
                    w = bounds['right'] - bounds['left']
                    h = bounds['bottom'] - bounds['top']
                    x_center = (bounds['left'] + bounds['right']) // 2
                    y_center = (bounds['top'] + bounds['bottom']) // 2
                    if w > 0 and h > 0 and 0 < x_center < width and 0 < y_center < height:
                        desc_val = info.get('contentDescription', '') or ''
                        if len(desc_val) < 30:
                            matches.append((elem, x_center, y_center, desc_val))
    except Exception as e:
        print(f"      Gagal mencari via descriptionMatches: {e}")

    # Klik semua yang terdeteksi secara unik
    if matches:
        unique_matches = []
        seen_coords = set()
        for elem, x, y, name in matches:
            coord_key = (x, y)
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                unique_matches.append((elem, x, y, name))
                
        for elem, x, y, name in unique_matches:
            print(f"      -> Mendeteksi pop-up pengganggu '{name}' pada ({x}, {y}). Mengklik...")
            try:
                # Coba klik native node terlebih dahulu
                elem.click()
                time.sleep(2)
            except Exception:
                try:
                    # Fallback ke klik koordinat
                    d.click(x, y)
                    time.sleep(2)
                except Exception as err:
                    print(f"      -> Gagal klik: {err}")
    else:
        # Debug: Dump semua teks tombol klik yang terdeteksi di layar jika tidak ditemukan kecocokan
        try:
            visible_texts = []
            for elem in d(clickable=True):
                if elem.exists:
                    txt = elem.info.get('text', '') or elem.info.get('contentDescription', '') or ''
                    if txt and len(txt) < 40 and txt not in visible_texts:
                        visible_texts.append(txt)
            if visible_texts:
                print(f"      [DEBUG DUMP] Tombol klik yang terdeteksi di layar: {visible_texts}")
        except Exception:
            pass


def clear_popups_story(d):
    try:
        width, height = d.window_size()
    except Exception:
        width, height = 1080, 1920

    # Tutup dialog persetujuan Google Smart Lock / simpan sandi jika terdeteksi
    try:
        current_pkg = d.app_current().get('package', '')
        if current_pkg and 'credentialmanager' in current_pkg.lower():
            print("      [Smart Lock] Terdeteksi dialog pengelola kredensial sistem. Mengirim BACK...")
            d.press("back")
            time.sleep(2)
    except:
        pass

    # Kumpulan label tombol penutup pop-up pengganggu/pemberitahuan
    targets = [
        "Lain kali", "Lain Kali", "Not Now", "Not now", "Jangan sekarang", 
        "Jangan Sekarang", "Nanti saja", "Nanti Saja", "Tutup", "Close", 
        "OK", "Oke", "Got it", "Got It", "Batal", "Cancel"
    ]
    
    for t in targets:
        btn = d(text=t)
        if btn.exists:
            print(f"      -> Mendeteksi pop-up tombol teks '{t}'. Mengklik...")
            try:
                btn.click()
                time.sleep(1.2)
                return
            except:
                pass
                
        btn_desc = d(description=t)
        if btn_desc.exists:
            print(f"      -> Mendeteksi pop-up deskripsi '{t}'. Mengklik...")
            try:
                btn_desc.click()
                time.sleep(1.2)
                return
            except:
                pass

    # Regex robust case-insensitive
    try:
        sel_text = d(textMatches="(?i)^\\s*(not[- ]?now|lain[- ]?kali|jangan[- ]?sekarang|tutup|close|nanti saja|batal|cancel|ok|oke|got[- ]?it)\\s*$")
        if sel_text.exists:
            print(f"      -> Klik pop-up regex: '{sel_text.info.get('text', 'pop')}'")
            sel_text.click()
            time.sleep(1.5)
            return
    except:
        pass


def bot_post(file_path, caption, device_pilihan=None, my_account=""):
    if device_pilihan is None:
        device_pilihan = "all"
    file_name = os.path.basename(file_path)

    log_id = log_activity("post", username=file_name, message="media", status="on_progress", mode="manual", device_id=device_pilihan)
    try:
        print("=========================================")
        print(" JALANKAN BOT POST (FEED)")
        print("=========================================")

        # Cek ketersediaan file di PC
        if not file_path or not os.path.exists(file_path):
            print(f"ERROR: File '{file_path}' tidak ditemukan di PC/server!")
            raise FileNotFoundError(f"File '{file_path}' tidak ditemukan!")

        d = connect_adb(device_pilihan, action="post", step_label="[1] Menghubungkan ke perangkat Android...")
        width, height = d.window_size()

        # Kirim file dari PC ke folder Galeri HP agar bisa dibaca Instagram
        remote_path = f"/sdcard/DCIM/Camera/{file_name}"
        print(f"[*] Mengirim media ke HP: {remote_path}...")
        try:
            d.push(file_path, remote_path)
            # Scan media library agar terdaftar di galeri HP
            d.shell(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://{remote_path}"')
            d.shell(f'media scan-file "{remote_path}"')
            print("      -> Upload media & media scanner scan berhasil")
            time.sleep(3)
        except Exception as upload_err:
            print(f"      -> Warning Gagal upload media ke DCIM: {upload_err}")
            try:
                # Coba folder Pictures sebagai fallback
                remote_path = f"/sdcard/Pictures/{file_name}"
                d.push(file_path, remote_path)
                d.shell(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://{remote_path}"')
                d.shell(f'media scan-file "{remote_path}"')
                print("      -> Upload media & media scanner scan berhasil (fallback Pictures)")
                time.sleep(3)
            except Exception as e2:
                print(f"      -> Gagal mengunggah media ke HP: {e2}")

        open_instagram(d, device_pilihan, action="post", delay=6, step_label="[2] Membuka aplikasi Instagram...")

        # Pastikan di Beranda sebelum melakukan swap atau navigasi
        _kembali_ke_beranda(d, width, height)

        # === PROSES SWAP AKUN DI AWAL (JIKA PARAMETER DIBERIKAN) ===
        if my_account and my_account.strip() != "":
            print(f"[PRE-RUN] Mengganti akun ke: '{my_account}'...")
            success = switch_instagram_account(my_account, device_pilihan)
            if not success:
                print(f"[-] ERROR: Gagal beralih ke akun '{my_account}' pada perangkat '{device_pilihan}'. Menghentikan bot.")
                return False
            time.sleep(3.0)

        # Pastikan berada di Halaman Profil untuk memulai postingan
        print("[3] Membuka Halaman Profil...")
        log_step("open_profile", status="complete", device_id=device_pilihan, action="post")
        profile_clicked = False
        for step in range(5):
            clear_popups_post(d)
            # Coba cari tombol Profil tab di kanan bawah
            profile_tab = None
            for rid in ["com.instagram.android:id/profile_tab", "com.instagram.android:id/profile_tab_avatar"]:
                if d(resourceId=rid).exists:
                    profile_tab = d(resourceId=rid)
                    break
            if not profile_tab:
                for desc in ["Profil", "Profile"]:
                    if d(descriptionContains=desc).exists:
                        profile_tab = d(descriptionContains=desc)
                        break
            if profile_tab:
                try:
                    profile_tab.click()
                    profile_clicked = True
                    print("      -> Sukses membuka Halaman Profil.")
                    break
                except:
                    pass
            # Fallback klik koordinat profil (x=90%, y=93%)
            print("      -> Mencoba mengklik koordinat profil (0.9, 0.93)...")
            d.click(int(width * 0.9), int(height * 0.93))
            time.sleep(2.5)
            
        time.sleep(3.0)
        clear_popups_post(d)

        print("[4] Membuka menu Buat Postingan (+) di Profil...")
        log_step("open_creation_menu", status="complete", device_id=device_pilihan, action="post")
        plus_clicked = False
        
        # Coba klik tombol plus di Profil via selector
        for rid in ["com.instagram.android:id/new_post_button", "com.instagram.android:id/action_bar_button_new_post"]:
            if d(resourceId=rid).exists:
                try:
                    d(resourceId=rid).click()
                    print(f"      -> Mengklik tombol plus via ID: {rid}")
                    plus_clicked = True
                    break
                except:
                    pass
                    
        if not plus_clicked:
            for desc in ["Buat", "Create", "New post", "New Post", "Tambah", "+"]:
                if d(descriptionContains=desc).exists:
                    try:
                        d(descriptionContains=desc).click()
                        print(f"      -> Mengklik tombol plus via deskripsi: {desc}")
                        plus_clicked = True
                        break
                    except:
                        pass
                        
        if not plus_clicked:
            # Klik koordinat plus di atas pojok kiri / pojok kanan
            print("      -> Menggunakan koordinat fallback untuk plus (kiri atas x=8%, y=6% / kanan atas x=88%, y=6%)...")
            d.click(int(width * 0.08), int(height * 0.06)) # Kiri atas
            time.sleep(1.5)
            d.click(int(width * 0.88), int(height * 0.06)) # Kanan atas
            plus_clicked = True

        time.sleep(3)
        clear_popups_post(d)

        # Klik pilihan "Postingan" / "Post" dari menu popup/bottom sheet
        print("[4.5] Memilih opsi 'Postingan' dari menu...")
        log_step("select_feed_option", status="complete", device_id=device_pilihan, action="post")
        option_clicked = False
        for text_opt in ["Postingan", "Post", "Postingan Feed", "Feed Post"]:
            sel = d(text=text_opt)
            if sel.exists:
                try:
                    sel.click()
                    print(f"      -> Opsi '{text_opt}' berhasil diklik")
                    option_clicked = True
                    break
                except:
                    pass
        if not option_clicked:
            # Fallback koordinat baris pertama pilihan menu di bottom sheet
            print("      -> Opsi tidak ditemukan, menggunakan koordinat fallback menu postingan (0.5, 0.72)...")
            d.click(int(width * 0.5), int(height * 0.72))
            
        time.sleep(4)

        print(f"[4.6] Memilih media dari Galeri...")
        log_step("select_media", status="complete", device_id=device_pilihan, action="post")
        media_selected = False
        
        # 1. Coba menggunakan Resource ID + child index (ViewGroup[2] -> index 1) dari input user
        grid_view = d(resourceId="com.instagram.android:id/media_picker_grid_view")
        if grid_view.exists:
            photo_item = grid_view.child(className="android.view.ViewGroup", index=1)
            if photo_item.exists:
                photo_item.click()
                print("      -> Foto terbaru dipilih via media_picker_grid_view child index 1")
                media_selected = True

        # 2. Fallback pencarian bounds pintar
        if not media_selected:
            try:
                image_views = d(className="android.widget.ImageView")
                for i in range(image_views.count):
                    img = image_views[i]
                    bounds = img.info.get('bounds', {})
                    left = bounds.get('left', 0)
                    top = bounds.get('top', 0)
                    right = bounds.get('right', 0)
                    bottom = bounds.get('bottom', 0)
                    img_width = right - left
                    if top >= int(height * 0.48) and img_width < int(width * 0.35) and img_width > 30:
                        img.click()
                        print("      -> Foto terbaru dipilih via pencarian bounds")
                        media_selected = True
                        break
            except Exception as bounds_err:
                print(f"      -> Gagal menganalisis bounds ImageView: {bounds_err}")

        # 3. Fallback koordinat persentase presisi yang diberikan oleh user (0.354, 0.649)
        if not media_selected:
            d.click(int(width * 0.354), int(height * 0.649))
            print("      -> Foto terbaru dipilih via koordinat presisi user (0.354, 0.649)")
        time.sleep(3)

        # Step 5: First confirmation (Next dari Galeri ke Edit screen)
        print("[5] Melanjutkan ke halaman edit (Next 1)...")
        log_step("edit_media", status="complete", device_id=device_pilihan, action="post")
        next_clicked = False
        
        btn1 = d(resourceId="com.instagram.android:id/next_button_textview")
        if btn1.exists:
            btn1.click()
            print("      -> Klik Next 1 via next_button_textview")
            next_clicked = True
        else:
            for selector in [d(text="Selanjutnya"), d(text="Berikutnya"), d(text="Next"), d(descriptionContains="Selanjutnya"), d(descriptionContains="Next")]:
                if selector.exists:
                    selector.click()
                    print("      -> Klik Next 1 via selector")
                    next_clicked = True
                    break
        if not next_clicked:
            d.click(int(width * 0.827), int(height * 0.052))
            print("      -> Klik Next 1 via koordinat presisi user (0.827, 0.052)")
        time.sleep(4)

        # Step 6: Second confirmation (Next dari Edit screen ke Share screen)
        print("[6] Melanjutkan ke halaman posting (Next 2)...")
        log_step("write_caption", status="complete", device_id=device_pilihan, action="post")
        next_clicked_2 = False
        
        btn2 = d(resourceId="com.instagram.android:id/creation_next_button")
        if btn2.exists:
            btn2.click()
            print("      -> Klik Next 2 via creation_next_button")
            next_clicked_2 = True
        else:
            for selector in [d(text="Selanjutnya"), d(text="Berikutnya"), d(text="Next"), d(descriptionContains="Selanjutnya"), d(descriptionContains="Next")]:
                if selector.exists:
                    selector.click()
                    print("      -> Klik Next 2 via selector")
                    next_clicked_2 = True
                    break
        if not next_clicked_2:
            d.click(int(width * 0.945), int(height * 0.916))
            print("      -> Klik Next 2 via koordinat presisi user (0.945, 0.916)")
        time.sleep(4)

        # Step 7: Input caption di halaman Share screen
        print(f"[7] Mengetik caption: '{caption}'...")
        clear_popups_post(d)
        
        caption_filled = False
        caption_field = d(resourceId="com.instagram.android:id/caption_input_text_view")
        if caption_field.exists:
            caption_field.click()
            time.sleep(1.5)
            clear_popups_post(d)
            caption_field.set_text(caption)
            print("      -> Caption diisi via caption_input_text_view")
            caption_filled = True
        else:
            for selector in [d(resourceId="com.instagram.android:id/caption_text_view"), d(resourceId="com.instagram.android:id/caption"), d(className="android.widget.EditText")]:
                if selector.exists:
                    selector.click()
                    time.sleep(1.5)
                    clear_popups_post(d)
                    selector.set_text(caption)
                    print("      -> Caption diisi via selector cadangan")
                    caption_filled = True
                    break
        if not caption_filled:
            d.click(int(width * 0.336), int(height * 0.356))
            time.sleep(1.5)
            clear_popups_post(d)
            d.send_keys(caption)
            print("      -> Caption diisi via koordinat presisi user (0.336, 0.356) + send_keys")
        time.sleep(3)

        # Step 7.5: Konfirmasi Penulisan Caption
        print("[7.5] Mengonfirmasi penulisan caption (Klik Oke)...")
        ok_clicked = False
        btn_ok = d(resourceId="com.instagram.android:id/next_button_textview")
        if btn_ok.exists:
            btn_ok.click()
            print("      -> Klik Oke via next_button_textview")
            ok_clicked = True
        else:
            for txt in ["Oke", "OK", "Done", "Selesai"]:
                btn_txt = d(text=txt)
                if btn_txt.exists:
                    btn_txt.click()
                    print(f"      -> Klik Oke via text: {txt}")
                    ok_clicked = True
                    break
        if not ok_clicked:
            d.click(int(width * 0.909), int(height * 0.057))
            print("      -> Klik Oke via koordinat presisi user (0.909, 0.057)")
        time.sleep(3)

        # Step 8: Publikasikan postingan
        print("[8] Mempublikasikan postingan (Bagikan)...")
        log_step("share_post", status="on_progress", device_id=device_pilihan, action="post")
        share_clicked = False
        
        btn_share = d(resourceId="com.instagram.android:id/share_footer_button")
        if btn_share.exists:
            btn_share.click()
            print("      -> Klik Bagikan via share_footer_button")
            share_clicked = True
        else:
            for selector in [d(text="Bagikan"), d(text="Share"), d(resourceId="com.instagram.android:id/share_button"), d(descriptionContains="Bagikan"), d(descriptionContains="Share")]:
                if selector.exists:
                    selector.click()
                    print("      -> Klik Bagikan via selector")
                    share_clicked = True
                    break
        if not share_clicked:
            d.click(int(width * 0.668), int(height * 0.904))
            print("      -> Klik Bagikan via koordinat presisi user (0.668, 0.904)")
        time.sleep(6)

        print("[9] Kembali ke Beranda...")
        home_clicked = False
        for i in range(5):
            clear_popups_post(d)
            if d(resourceId="com.instagram.android:id/feed_tab").exists or \
               d(resourceId="com.instagram.android:id/home_tab").exists or \
               d(descriptionContains="Beranda").exists or \
               d(descriptionContains="Home").exists:
                d.click(int(width * 0.095), int(height * 0.918))
                time.sleep(1.5)
                home_clicked = True
                break
            d.press("back")
            time.sleep(2.5)

        if not home_clicked:
            d.click(int(width * 0.095), int(height * 0.918))
            time.sleep(3)

        print("=========================================")
        print(f" POSTING BERHASIL: {caption}")
        print("=========================================\n")
        log_complete(log_id, message="Post feed uploaded successfully")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        log_error(log_id, error=str(e))
        return False


def bot_post_reels(file_path, caption, device_pilihan=None, my_account=""):
    if device_pilihan is None:
        device_pilihan = "all"
    file_name = os.path.basename(file_path)

    log_id = log_activity("post_reels", username=file_name, message="media", status="on_progress", mode="manual", device_id=device_pilihan)
    try:
        print("=========================================")
        print(" JALANKAN BOT POST REELS INSTAGRAM")
        print(f" Media File : {file_path}")
        print(f" Caption    : {caption}")
        print("=========================================")

        # Validasi file di PC
        if not file_path or not os.path.exists(file_path):
            print(f"ERROR: File '{file_path}' tidak ditemukan di PC/server!")
            raise FileNotFoundError(f"File '{file_path}' tidak ditemukan!")

        d = connect_adb(device_pilihan, action="post_reels", step_label="\n--- TAHAP 1: BUKA INSTAGRAM / CEK ---")
        checker(d)
        width, height = d.window_size()
        try:
            d.settings['wait_for_idle'] = False
            d.settings.wait_for_idle = False
            d.settings['click_post_delay'] = 0
            d.settings['key_post_delay'] = 0
        except Exception as e:
            print(f"      -> Gagal menyetel u2 settings: {e}")
        try:
            d.wait_timeout = 3.0
        except Exception as e:
            print(f"      -> Gagal menyetel wait_timeout: {e}")

        print(f"Terhubung ke perangkat: {d.device_info.get('brand', 'Unknown')} {d.device_info.get('model', 'Device')} ({width}x{height})")

        # Kirim file video dari PC ke folder Galeri HP
        print(f"[*] Mengirim video ke HP...")
        media_uploaded = False
        for parent_folder in ["/sdcard/DCIM/Camera", "/sdcard/Pictures"]:
            remote_path = f"{parent_folder}/{file_name}"
            try:
                d.push(file_path, remote_path)
                d.shell(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://{remote_path}"')
                d.shell(f'media scan-file "{remote_path}"')
                print(f"      -> Upload & Scan berhasil di: {remote_path}")
                media_uploaded = True
            except Exception as e:
                print(f"      -> Warning upload ke {parent_folder}: {e}")
        
        if not media_uploaded:
            print("WARNING: Gagal mengunggah media ke HP. Melanjutkan dengan media yang sudah ada di galeri...")

        time.sleep(3)

        open_instagram(d, device_pilihan, action="post_reels", delay=6, step_label="[SYSTEM] Membuka aplikasi Instagram...")

        # Pastikan di Beranda sebelum melakukan swap atau navigasi
        _kembali_ke_beranda(d, width, height)

        # === PROSES SWAP AKUN DI AWAL (JIKA PARAMETER DIBERIKAN) ===
        if my_account and my_account.strip() != "":
            print(f"[PRE-RUN] Mengganti akun ke: '{my_account}'...")
            success = switch_instagram_account(my_account, device_pilihan)
            if not success:
                print(f"[-] ERROR: Gagal beralih ke akun '{my_account}' pada perangkat '{device_pilihan}'. Menghentikan bot.")
                return False
            time.sleep(3.0)

        # TAHAP 2: KLIK PROFIL
        print("\n--- TAHAP 2: KLIK PROFIL ---")
        log_step("open_profile", status="complete", device_id=device_pilihan, action="post_reels")
        clear_any_popup_fast(d)
        profile_clicked = False
        
        xpath_profile = '//*[@resource-id="com.instagram.android:id/profile_tab"]/android.view.ViewGroup[1]/android.widget.FrameLayout[1]'
        try:
            if d.xpath(xpath_profile).exists:
                d.xpath(xpath_profile).click()
                profile_clicked = True
                print("      -> Klik ikon profil via XPath")
        except:
            pass
            
        if not profile_clicked:
            for descriptor in ["Profil", "Profile", "Profile tab", "Tab profil", "Self profile"]:
                elem = d(descriptionContains=descriptor)
                if elem.exists:
                    elem.click()
                    profile_clicked = True
                    print(f"      -> Klik ikon profil via deskripsi '{descriptor}'")
                    break
        
        if not profile_clicked:
            if d(resourceId="com.instagram.android:id/profile_tab").exists:
                d(resourceId="com.instagram.android:id/profile_tab").click()
                profile_clicked = True
                print("      -> Klik ikon profil via resourceId profile_tab")
                
        if not profile_clicked:
            d.click(int(width * 0.90), int(height * 0.95))
            profile_clicked = True
            print("      -> Klik ikon profil via koordinat fallback (0.90, 0.95)")
            
        time.sleep(4)

        # TAHAP 3: KLIK IKON PLUS DI POJOK KIRI ATAS
        print("\n--- TAHAP 3: KLIK IKON PLUS ---")
        log_step("open_creation_menu", status="complete", device_id=device_pilihan, action="post_reels")
        clear_any_popup_fast(d)
        plus_clicked = False
        
        print("      -> Mencoba mengklik koordinat pojok kiri atas (x=8%, y=6%)...")
        d.click(int(width * 0.08), int(height * 0.06))
        time.sleep(3)

        creation_menu_exists = d(textContains="Reel").exists or d(textContains="Post").exists or d(textContains="Cerita").exists or d(textContains="Story").exists
        
        if not creation_menu_exists:
            print("      -> Menu pembuatan belum muncul. Mencoba selector UI...")
            for descriptor in ["Buat", "Create", "Post", "Tambah", "+"]:
                elem = d(descriptionContains=descriptor)
                if elem.exists:
                    elem.click()
                    print(f"      -> Mengklik tombol plus via deskripsi: {descriptor}")
                    plus_clicked = True
                    break
                    
            if not plus_clicked:
                if d(resourceId="com.instagram.android:id/creation_tab").exists:
                    d(resourceId="com.instagram.android:id/creation_tab").click()
                    print("      -> Klik creation_tab")
                    plus_clicked = True
            time.sleep(3)

        # TAHAP 4: PILIH OPSI REELS DI PILIHAN
        print("\n--- TAHAP 4: PILIH OPSI REELS ---")
        log_step("select_reels_option", status="complete", device_id=device_pilihan, action="post_reels")
        clear_any_popup_fast(d)
        reels_selected = False
        
        for label in ["Reel", "Reels"]:
            btn = d(className="android.widget.TextView", text=label)
            if btn.exists:
                btn.click()
                print(f"      -> Memilih opsi Reels via TextView text: '{label}'")
                reels_selected = True
                break
                
            btn = d(className="android.widget.TextView", description=label)
            if btn.exists:
                btn.click()
                print(f"      -> Memilih opsi Reels via TextView description: '{label}'")
                reels_selected = True
                break

        if not reels_selected:
            for res_id in ["com.instagram.android:id/menu_item_text", "com.instagram.android:id/row_text", "com.instagram.android:id/menu_item_title"]:
                for label in ["Reel", "Reels"]:
                    btn = d(resourceId=res_id, text=label)
                    if btn.exists:
                        btn.click()
                        print(f"      -> Memilih opsi Reels via resourceId '{res_id}' dan text '{label}'")
                        reels_selected = True
                        break
                if reels_selected:
                    break

        if not reels_selected:
            try:
                el = d(textMatches="(?i)^(reel|reels)$")
                if el.exists:
                    el.click()
                    print("      -> Memilih opsi Reels via textMatches regex")
                    reels_selected = True
            except:
                pass

        if not reels_selected:
            for label in ["Reel", "Reels"]:
                btn = d(textContains=label)
                res_name = (btn.info.get("resourceName") or "") if btn.exists else ""
                if btn.exists and "tab" not in res_name.lower():
                    btn.click()
                    print(f"      -> Memilih opsi Reels via textContains: '{label}'")
                    reels_selected = True
                    break

        if not reels_selected:
            print("      -> Gagal mencari tombol Reels. Mencoba klik koordinat default (x=50%, y=85%)...")
            d.click(int(width * 0.5), int(height * 0.85))
            time.sleep(2)

        time.sleep(4)

        # TAHAP 5: PILIH FOTO/VIDEO TERBARU
        print("\n--- TAHAP 5: PILIH MEDIA ---")
        log_step("select_media", status="complete", device_id=device_pilihan, action="post_reels")
        media_selected = False
        
        for attempt in range(3):
            clear_any_popup_fast(d)
            grid_view = d(resourceId="com.instagram.android:id/gallery_recycler_view")
            if not grid_view.exists:
                grid_view = d(resourceId="com.instagram.android:id/media_picker_grid_view")
    
            if grid_view.exists:
                for test_idx in [1, 0, 2]:
                    photo_item = grid_view.child(index=test_idx)
                    if photo_item.exists:
                        desc = photo_item.info.get("contentDescription", "") or ""
                        text = photo_item.info.get("text", "") or ""
                        if any(x in (desc + text).lower() for x in ["select", "pilih", "multiple", "camera", "kamera"]):
                            continue
                        try:
                            photo_item.click()
                            print(f"      -> Media terbaru dipilih via grid view child index {test_idx}")
                            media_selected = True
                            break
                        except Exception as click_err:
                            pass
            
            if not media_selected:
                image_views = d(className="android.widget.ImageView")
                if image_views.exists and image_views.count > 1:
                    for idx in range(1, min(image_views.count, 6)):
                        desc = image_views[idx].info.get("contentDescription", "") or ""
                        text = image_views[idx].info.get("text", "") or ""
                        if any(x in (desc + text).lower() for x in ["select", "pilih", "multiple", "camera", "kamera"]):
                            continue
                        bounds = image_views[idx].info.get('bounds', {})
                        if bounds.get('top', 0) > int(height * 0.30):
                            try:
                                image_views[idx].click()
                                print(f"      -> Media terbaru dipilih via ImageView index {idx}")
                                media_selected = True
                                break
                            except:
                                pass
                                
            if not media_selected:
                print("      -> Mencoba memilih media menggunakan koordinat fallback (0.25, 0.40)...")
                d.click(int(width * 0.25), int(height * 0.40))
                media_selected = True
    
            time.sleep(3.5)
            
            gallery_still_open = (
                d(resourceId="com.instagram.android:id/gallery_recycler_view").exists or 
                d(resourceId="com.instagram.android:id/media_picker_grid_view").exists or 
                d(text="Galeri").exists or 
                d(text="Gallery").exists
            )
            try:
                current_pkg = d.app_current().get('package', '')
                if 'permissioncontroller' in current_pkg.lower():
                    gallery_still_open = True
            except:
                pass
                
            if not gallery_still_open:
                print("      -> Berhasil masuk ke editor/preview Reel!")
                break
            else:
                print(f"      -> Gagal masuk ke editor (percobaan {attempt+1}/3). Mencoba klik ulang...")
                media_selected = False
                
        time.sleep(2)

        # TAHAP 6: LALU KLIK BERIKUTNYA (EDIT/PREVIEW)
        print("\n--- TAHAP 6: KLIK BERIKUTNYA ---")
        log_step("edit_media", status="complete", device_id=device_pilihan, action="post_reels")
        
        for step in range(1, 4):
            print(f"   -> Percobaan klik 'Berikutnya' tahap {step}...")
            clear_any_popup_fast(d)
            
            caption_field = d(resourceId="com.instagram.android:id/caption_input_text_view")
            if not caption_field.exists:
                caption_field = d(resourceId="com.instagram.android:id/caption")
            if not caption_field.exists:
                caption_field = d(className="android.widget.EditText")
                
            if caption_field.exists:
                print("      -> Sudah sampai di halaman pengisian deskripsi.")
                break
                
            next_clicked = False
            for label in ["Berikutnya", "Next", "Selanjutnya"]:
                for selector in [d(text=label), d(textContains=label), d(descriptionContains=label)]:
                    if selector.exists:
                        try:
                            selector.click()
                            print(f"      -> Klik tombol '{label}'")
                            next_clicked = True
                            break
                        except:
                            pass
                if next_clicked:
                    break
                    
            if not next_clicked:
                for res_id in ["com.instagram.android:id/next_button_textview", "com.instagram.android:id/creation_next_button", "com.instagram.android:id/next_button"]:
                    btn = d(resourceId=res_id)
                    if btn.exists:
                        try:
                            btn.click()
                            print(f"      -> Klik Next via resourceId: {res_id}")
                            next_clicked = True
                            break
                        except:
                            pass

            if not next_clicked:
                print("      -> Mencoba koordinat fallback Next (x=90%, y=92%)...")
                d.click(int(width * 0.90), int(height * 0.92))
                next_clicked = True
                
            time.sleep(4)
            clear_any_popup_fast(d)

        # TAHAP 7: MENULIS DESKRIPSI/CAPTIONS
        print("\n--- TAHAP 7: MENULIS DESKRIPSI ---")
        log_step("write_caption", status="complete", device_id=device_pilihan, action="post_reels")
        caption_filled = False
        clear_any_popup_fast(d)
        
        caption_field = find_element(d,
                                     descriptions=["Tulis teks...", "Tulis deskripsi...", "Write a caption...", "Write a description..."],
                                     texts=["Tulis teks...", "Tulis deskripsi...", "Write a caption...", "Write a description..."],
                                     resource_ids=[
                                         "com.instagram.android:id/caption_input_text_view",
                                         "com.instagram.android:id/caption_text_view",
                                         "com.instagram.android:id/caption"
                                     ])
        if not caption_field:
            caption_field = d(className="android.widget.EditText")

        if caption_field.exists:
            try:
                caption_field.click()
                time.sleep(1.5)
                clear_any_popup_fast(d)
                caption_field.set_text(caption)
                print(f"      -> Deskripsi berhasil diisi: '{caption}'")
                caption_filled = True
            except Exception as set_txt_err:
                print(f"      -> Gagal mengisi deskripsi via set_text: {set_txt_err}")
                
        if not caption_filled:
            print("      -> Mencoba klik koordinat fallback area caption (x=30%, y=30%) & send_keys...")
            d.click(int(width * 0.30), int(height * 0.30))
            time.sleep(1.5)
            clear_any_popup_fast(d)
            try:
                d.send_keys(caption)
                print(f"      -> Deskripsi berhasil diisi via send_keys")
                caption_filled = True
            except Exception as keys_err:
                print(f"      -> Gagal set text via send_keys: {keys_err}")

        time.sleep(3)

        # Centang/OK di pojok kanan atas setelah mengetik caption
        ok_clicked = False
        btn_ok = d(resourceId="com.instagram.android:id/next_button_textview")
        if btn_ok.exists:
            btn_ok.click()
            print("      -> Klik Oke via next_button_textview")
            ok_clicked = True
        else:
            for txt in ["Oke", "OK", "Done", "Selesai"]:
                btn_txt = d(text=txt)
                if btn_txt.exists:
                    btn_txt.click()
                    print(f"      -> Klik Oke via text: {txt}")
                    ok_clicked = True
                    break
        if not ok_clicked:
            d.click(int(width * 0.909), int(height * 0.057))
            print("      -> Klik Oke via koordinat presisi (0.909, 0.057)")
        time.sleep(3)

        # TAHAP 8: PUBLISH (KLIK BAGIKAN)
        print("\n--- TAHAP 8: LALU KLIK BAGIKAN ---")
        log_step("share_post", status="on_progress", device_id=device_pilihan, action="post_reels")
        clear_any_popup_fast(d)
        share_clicked = False
        
        share_btn = find_element(d,
                                 descriptions=["Bagikan", "Share", "Bagikan Reel", "Share Reel", "Share to Reels"],
                                 texts=["Bagikan", "Share", "Bagikan Reel", "Share Reel", "Share to Reels"],
                                 resource_ids=[
                                     "com.instagram.android:id/share_footer_button",
                                     "com.instagram.android:id/share_button",
                                     "com.instagram.android:id/share"
                                 ])
        if share_btn:
            share_btn.click()
            print("      -> Klik Bagikan via selector")
            share_clicked = True
        else:
            for target in ["Bagikan", "Share"]:
                el = d(textContains=target)
                if el.exists:
                    el.click()
                    print(f"      -> Klik Bagikan via textContains '{target}'")
                    share_clicked = True
                    break

        if not share_clicked:
            print("      -> Mencoba koordinat fallback Bagikan (x=50%, y=92%)...")
            d.click(int(width * 0.50), int(height * 0.92))
            share_clicked = True

        # TAHAP 9: KEMBALI KE BERANDA
        print("\n--- TAHAP 9: KEMBALI KE BERANDA ---")
        home_clicked = False
        for res_id in ["com.instagram.android:id/feed_tab", "com.instagram.android:id/home_tab"]:
            btn_home = d(resourceId=res_id)
            if btn_home.exists:
                btn_home.click()
                print("      -> Kembali ke Beranda via resourceId")
                home_clicked = True
                break
                
        if not home_clicked:
            d.click(int(width * 0.1), int(height * 0.93))
            print("      -> Kembali ke Beranda via koordinat fallback")
            home_clicked = True

        time.sleep(1)
        clear_any_popup_fast(d)

        # TAHAP 10: REFRESH BERANDA (FAST REFRESH) & SELESAI
        print("\n--- TAHAP 10: REFRESH BERANDA ---")
        print("      -> Melakukan swipe down untuk me-refresh Beranda...")
        d.swipe(0.5, 0.3, 0.5, 0.8, duration=0.15)
        time.sleep(1)
        
        for res_id in ["com.instagram.android:id/feed_tab", "com.instagram.android:id/home_tab"]:
            btn_home = d(resourceId=res_id)
            if btn_home.exists:
                btn_home.click()
                break
        
        print("=========================================")
        print(" POSTING REELS INSTAGRAM SELESAI & BERHASIL")
        print("=========================================\n")
        log_complete(log_id, message="Reels uploaded successfully")
        return True

    except Exception as e:
        print(f"\nERROR saat posting Reels: {e}")
        log_error(log_id, error=str(e))
        return False


def bot_post_story(file_path, device_pilihan=None, my_account=""):
    if device_pilihan is None:
        device_pilihan = "all"
    file_name = os.path.basename(file_path)

    log_id = log_activity("post_story", username=file_name, message="media", status="on_progress", mode="manual", device_id=device_pilihan)
    try:
        print("=========================================")
        print(" JALANKAN BOT POST STORY INSTAGRAM")
        print(f" Media File : {file_path}")
        print("=========================================")

        # Cek ketersediaan file di PC
        if not file_path or not os.path.exists(file_path):
            print(f"ERROR: File '{file_path}' tidak ditemukan di PC/server!")
            raise FileNotFoundError(f"File '{file_path}' tidak ditemukan!")

        d = connect_adb(device_pilihan, action="post_story", step_label="[1] Menghubungkan ke perangkat Android...")
        width, height = d.window_size()
        print(f"Terhubung ke perangkat: {d.device_info.get('brand', 'Unknown')} {d.device_info.get('model', 'Device')}")

        # Kirim file ke kedua folder agar terindeks oleh galeri HP
        print(f"[*] Mengirim media ke HP...")
        for parent_folder in ["/sdcard/Pictures", "/sdcard/DCIM/Camera"]:
            remote_path = f"{parent_folder}/{file_name}"
            try:
                d.push(file_path, remote_path)
                d.shell(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://{remote_path}"')
                d.shell(f'media scan-file "{remote_path}"')
                print(f"      -> Upload & Scan berhasil di: {remote_path}")
            except Exception as e:
                print(f"      -> Gagal di {parent_folder}: {e}")
        time.sleep(3)

        open_instagram(d, device_pilihan, action="post_story", delay=6, step_label="[2] Membuka aplikasi Instagram...")
            
        # Pastikan di Beranda sebelum melakukan swap atau navigasi
        _kembali_ke_beranda(d, width, height)

        # === PROSES SWAP AKUN DI AWAL (JIKA PARAMETER DIBERIKAN) ===
        if my_account and my_account.strip() != "":
            print(f"[PRE-RUN] Mengganti akun ke: '{my_account}'...")
            success = switch_instagram_account(my_account, device_pilihan)
            if not success:
                print(f"[-] ERROR: Gagal beralih ke akun '{my_account}' pada perangkat '{device_pilihan}'. Menghentikan bot.")
                return False
            time.sleep(3.0)

        clear_popups_story(d)

        # Pastikan di Beranda sebelum swipe ke kanan
        print("[3] Memastikan berada di Beranda...")
        log_step("ensure_home", status="complete", device_id=device_pilihan, action="post_story")
        home_clicked = False
        for sel in [d(resourceId="com.instagram.android:id/feed_tab"), d(descriptionContains="Beranda"), d(descriptionContains="Home")]:
            if sel.exists:
                try:
                    sel.click()
                    home_clicked = True
                    time.sleep(2)
                    break
                except Exception:
                    pass
        if not home_clicked:
            d.click(int(width * 0.1), int(height * 0.93))
            time.sleep(2)

        # Buka kamera story dengan geser swipe langsung ke kanan
        print("[4] Membuka kamera Story (geser swipe ke kanan)...")
        log_step("open_story_camera", status="complete", device_id=device_pilihan, action="post_story")
        d.swipe(0.05, 0.5, 0.95, 0.5, duration=0.1)
        time.sleep(4)

        # Cek jika kamera terbuka, cari tombol galeri
        print("[5] Membuka Galeri di kamera Story...")
        log_step("select_media", status="complete", device_id=device_pilihan, action="post_story")
        is_already_in_gallery = (
            d(text="Galeri").exists or 
            d(text="Gallery").exists or 
            d(resourceId="com.instagram.android:id/media_picker_grid_view").exists
        )
        
        if is_already_in_gallery:
            print("      -> Sudah langsung berada di halaman Galeri. Melewati pembukaan galeri...")
        else:
            gallery_clicked = False
            for sel in [d(resourceId="com.instagram.android:id/gallery_button"), d(resourceId="com.instagram.android:id/gallery_button_avatar")]:
                if sel.exists:
                    try:
                        sel.click()
                        gallery_clicked = True
                        break
                    except:
                        pass
            if not gallery_clicked:
                print("      -> Tombol galeri tidak terdeteksi, menggunakan koordinat fallback (0.10, 0.91)...")
                d.click(int(width * 0.10), int(height * 0.91))
            time.sleep(3)

        print("[6] Memilih media terbaru...")
        media_selected = False
        
        # Loop mencoba klik foto teratas hingga 3 kali
        for attempt in range(3):
            grid_view = d(resourceId="com.instagram.android:id/gallery_recycler_view")
            if not grid_view.exists:
                grid_view = d(resourceId="com.instagram.android:id/media_picker_grid_view")

            if grid_view.exists:
                for test_idx in [1, 0, 2]:
                    photo_item = grid_view.child(index=test_idx)
                    if photo_item.exists:
                        desc = photo_item.info.get("contentDescription", "") or ""
                        text = photo_item.info.get("text", "") or ""
                        if any(x in (desc + text).lower() for x in ["select", "pilih", "multiple"]):
                            continue
                        try:
                            photo_item.click()
                            print(f"      -> Media dipilih via grid view child index {test_idx}")
                            media_selected = True
                            break
                        except:
                            pass
                if media_selected:
                    time.sleep(1.5)

            if not media_selected:
                image_views = d(className="android.widget.ImageView")
                if image_views.exists and image_views.count > 1:
                    for idx in range(1, min(image_views.count, 6)):
                        desc = image_views[idx].info.get("contentDescription", "") or ""
                        text = image_views[idx].info.get("text", "") or ""
                        if any(x in (desc + text).lower() for x in ["select", "pilih", "multiple"]):
                            continue
                        bounds = image_views[idx].info.get('bounds', {})
                        if bounds.get('top', 0) > int(height * 0.30):
                            try:
                                image_views[idx].click()
                                print(f"      -> Media dipilih via ImageView index {idx}")
                                media_selected = True
                                break
                            except:
                                pass
                    if media_selected:
                        time.sleep(1.5)

            if not media_selected:
                print("      -> Menggunakan koordinat fallback memilih media (0.481, 0.321)...")
                d.click(int(width * 0.481), int(height * 0.321))
                media_selected = True
            
            time.sleep(3)
            gallery_still_open = (
                d(resourceId="com.instagram.android:id/gallery_recycler_view").exists or 
                d(resourceId="com.instagram.android:id/media_picker_grid_view").exists or 
                d(text="Galeri").exists or 
                d(text="Gallery").exists
            )
            if not gallery_still_open:
                print("      -> Berhasil masuk to editor Story!")
                break
            else:
                print(f"      -> Gagal masuk ke editor (percobaan {attempt+1}/3). Mencoba klik ulang...")
                media_selected = False
        time.sleep(2)

        print("[7] Mempublikasikan ke Cerita Anda...")
        log_step("share_story", status="on_progress", device_id=device_pilihan, action="post_story")
        shared = False
        
        for label in ["Cerita Anda", "Your story", "Your Story"]:
            for sel in [d(text=label), d(descriptionContains=label)]:
                if sel.exists:
                    try:
                        sel.click()
                        print(f"      -> Klik tombol langsung '{label}'")
                        shared = True
                        break
                    except:
                        pass
            if shared:
                break

        if not shared:
            for rid in ["com.instagram.android:id/zero_rating_story_button", "com.instagram.android:id/share_button"]:
                btn_story = d(resourceId=rid)
                if btn_story.exists:
                    btn_story.click()
                    print(f"      -> Klik tombol share via ID '{rid}'")
                    shared = True
                    break

        if not shared:
            next_clicked = False
            for sel in [d(descriptionContains="Kirim ke"), d(descriptionContains="Send to"), d(resourceId="com.instagram.android:id/next_button")]:
                if sel.exists:
                    try:
                        sel.click()
                        next_clicked = True
                        time.sleep(2)
                        break
                    except:
                        pass
            if next_clicked:
                share_clicked = False
                for sel in [d(text="Bagikan"), d(text="Share"), d(resourceId="com.instagram.android:id/share_button")]:
                    if sel.exists:
                        try:
                            sel.click()
                            share_clicked = True
                            time.sleep(2)
                            break
                        except:
                            pass
                
                for sel in [d(text="Selesai"), d(text="Done"), d(resourceId="com.instagram.android:id/done_button")]:
                    if sel.exists:
                        try:
                            sel.click()
                            shared = True
                            print("      -> Publikasi story via alur Send to -> Share -> Done berhasil")
                            break
                        except:
                            pass

        if not shared:
            print("      -> Menggunakan koordinat fallback untuk tombol langsung 'Cerita Anda' (0.22, 0.93)...")
            d.click(int(width * 0.22), int(height * 0.93))
            shared = True
            time.sleep(3)

        print("[8] Menunggu proses unggah story selesai...")
        time.sleep(6)

        print("[9] Kembali ke Beranda...")
        home_clicked = False
        for i in range(4):
            clear_popups_story(d)
            if d(resourceId="com.instagram.android:id/feed_tab").exists or \
               d(descriptionContains="Beranda").exists or \
               d(descriptionContains="Home").exists:
                d.click(int(width * 0.1), int(height * 0.93))
                time.sleep(1.5)
                home_clicked = True
                break
            d.press("back")
            time.sleep(2.0)

        if not home_clicked:
            d.click(int(width * 0.1), int(height * 0.93))
            time.sleep(2)

        print("=========================================")
        print(" POST STORY BERHASIL DILAKUKAN")
        print("=========================================\n")
        log_complete(log_id, message="Story uploaded successfully")
        return True

    except Exception as e:
        print(f"[ERROR EXCEPTION] Terjadi kesalahan saat post story: {e}")
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
        print("ERROR: Argumen kurang!")
        print("Penggunaan:")
        print("  - Post Story:  python3 bot_ig_post.py <file_path> [device_id] [my_account]")
        print("  - Post Feed/Reels: python3 bot_ig_post.py <file_path> <caption_text> [device_id] [my_account]")
        sys.exit(1)

    first_arg = sys.argv[1]
    
    # Deteksi jika argumen pertama secara eksplisit mendefinisikan tipe post
    if first_arg.lower() in ["feed", "reels", "story", "post"]:
        post_type = first_arg.lower()
        file_path = sys.argv[2] if len(sys.argv) > 2 else ""
        
        if post_type == "story":
            device_id = sys.argv[3] if len(sys.argv) > 3 else "all"
            my_account = ""
            if len(sys.argv) > 4:
                my_account = sys.argv[4]
            
            devices = resolve_devices(device_id)
            if len(devices) > 1:
                run_parallel_threads(bot_post_story, devices, file_path=file_path, my_account=my_account)
            else:
                bot_post_story(file_path, device_pilihan=devices[0], my_account=my_account)
        elif post_type == "reels":
            caption = sys.argv[3] if len(sys.argv) > 3 else ""
            device_id = sys.argv[4] if len(sys.argv) > 4 else "all"
            my_account = sys.argv[5] if len(sys.argv) > 5 else ""
            
            devices = resolve_devices(device_id)
            if len(devices) > 1:
                run_parallel_threads(bot_post_reels, devices, file_path=file_path, caption=caption, my_account=my_account)
            else:
                bot_post_reels(file_path, caption, device_pilihan=devices[0], my_account=my_account)
        else: # feed / post
            caption = sys.argv[3] if len(sys.argv) > 3 else ""
            device_id = sys.argv[4] if len(sys.argv) > 4 else "all"
            my_account = sys.argv[5] if len(sys.argv) > 5 else ""
            
            devices = resolve_devices(device_id)
            if len(devices) > 1:
                run_parallel_threads(bot_post, devices, file_path=file_path, caption=caption, my_account=my_account)
            else:
                bot_post(file_path, caption, device_pilihan=devices[0], my_account=my_account)
    else:
        # Pendeteksian Otomatis (Tanpa keyword tipe post)
        file_path = first_arg
        ext = os.path.splitext(file_path.lower())[1]
        is_video = ext in [".mp4", ".mov", ".avi", ".mkv", ".3gp", ".webm", ".flv"]
        
        if len(sys.argv) <= 2:
            # Hanya file_path -> Otomatis Story Post
            device_id = sys.argv[2] if len(sys.argv) > 2 else "all"
            devices = resolve_devices(device_id)
            if len(devices) > 1:
                run_parallel_threads(bot_post_story, devices, file_path=file_path)
            else:
                bot_post_story(file_path, device_pilihan=devices[0])
        elif len(sys.argv) == 3:
            # 2 argumen: python3 bot_ig_post.py <file_path> <arg2>
            arg2 = sys.argv[2]
            # Cek apakah arg2 adalah device_id (seperti "all", "Semua...", atau serial number)
            is_device = (
                arg2.lower() == "all" or 
                "semua" in arg2.lower() or 
                "," in arg2 or
                (len(arg2) == 11 and arg2.isalnum())
            )
            if is_device or not arg2:
                # Argumen kedua adalah device_id, berarti caption kosong -> Otomatis Story Post
                devices = resolve_devices(arg2)
                if len(devices) > 1:
                    run_parallel_threads(bot_post_story, devices, file_path=file_path)
                else:
                    bot_post_story(file_path, device_pilihan=devices[0])
            else:
                # Argumen kedua adalah caption -> Otomatis Feed / Reels (device_id="all")
                caption = arg2
                device_id = "all"
                devices = resolve_devices(device_id)
                if len(devices) > 1:
                    if is_video:
                        run_parallel_threads(bot_post_reels, devices, file_path=file_path, caption=caption)
                    else:
                        run_parallel_threads(bot_post, devices, file_path=file_path, caption=caption)
                else:
                    if is_video:
                        bot_post_reels(file_path, caption, device_pilihan=devices[0])
                    else:
                        bot_post(file_path, caption, device_pilihan=devices[0])
        else:
            # 3 argumen atau lebih: python3 bot_ig_post.py <file_path> <caption> <device_id> [my_account]
            caption = sys.argv[2]
            device_id = sys.argv[3] if len(sys.argv) > 3 else "all"
            my_account = sys.argv[4] if len(sys.argv) > 4 else ""
            devices = resolve_devices(device_id)
            if len(devices) > 1:
                if is_video:
                    run_parallel_threads(bot_post_reels, devices, file_path=file_path, caption=caption, my_account=my_account)
                else:
                    run_parallel_threads(bot_post, devices, file_path=file_path, caption=caption, my_account=my_account)
            else:
                if is_video:
                    bot_post_reels(file_path, caption, device_pilihan=devices[0], my_account=my_account)
                else:
                    bot_post(file_path, caption, device_pilihan=devices[0], my_account=my_account)
