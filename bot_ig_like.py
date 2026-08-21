import sys
import uiautomator2 as u2
import time
import random
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
    
# Import account switcher
try:
    from switch_akun_ig import switch_instagram_account
except ImportError:
    def switch_instagram_account(target_username, device_pilihan="all"): return False

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

def like_post_target(target_user, device_pilihan="all", my_account=""):
    log_id = log_activity("like_target", username=target_user, status="on_progress", mode="manual", device_id=device_pilihan, extra={"my_account": my_account})
    try:
        print("=========================================")
        print(f" JALANKAN BOT LIKE TARGET: @{target_user}")
        if my_account:
            print(f" Menggunakan Akun Saya: {my_account}")
        print("=========================================")
        
        d = connect_adb(device_pilihan, action="like", step_label="[1/5] Menghubungkan ke perangkat Android via ADB...")
        width, height = d.window_size()
        print(f"Terhubung ke perangkat: {d.device_info.get('brand', 'Unknown')} {d.device_info.get('model', 'Device')} ({width}x{height})")

        open_instagram(d, device_pilihan, action="like", delay=6, step_label="[2/5] Membuka aplikasi Instagram...")
        clear_any_popup_fast(d)

        # Pastikan di Beranda sebelum melakukan swap atau navigasi utama
        _kembali_ke_beranda(d, width, height)

        # === PROSES SWAP AKUN DI AWAL (JIKA PARAMETER DIBERIKAN) ===
        if my_account and my_account.strip() != "":
            print(f"[PRE-RUN] Mengganti akun ke: '{my_account}'...")
            
            # 1. Mengklik tombol Profil kanan bawah
            x_profile = int(width * 0.904)
            y_profile = int(height * 0.914)
            d.click(x_profile, y_profile)
            time.sleep(3.0)
            clear_any_popup_fast(d)
            
            # 2. Mengklik Nama Pengguna di pojok atas (tengah/kiri) untuk membuka menu ganti akun
            print("      -> Mengklik nama akun di bagian atas untuk membuka menu ganti akun...")
            action_bar_title = d(resourceId="com.instagram.android:id/action_bar_title")
            title_badge = d(resourceId="com.instagram.android:id/title_with_badge_container")
            if action_bar_title.exists:
                action_bar_title.click()
            elif title_badge.exists:
                title_badge.click()
            else:
                # Fallback koordinat atas (Bryant Kalibrasi: 0.25, 0.06)
                d.click(int(width * 0.25), int(height * 0.06))
            time.sleep(3.5)
            
            # 3. Cari nama akun dalam daftar pop-up bawah
            clean_acc = my_account.replace("@", "").strip()
            btn_acc = d(text=clean_acc)
            if not btn_acc.exists:
                btn_acc = d(textContains=clean_acc)
                
            if btn_acc.exists:
                print(f"      -> Akun '{clean_acc}' ditemukan di daftar. Mengklik untuk beralih...")
                btn_acc.click()
                time.sleep(6.0)
                clear_any_popup_fast(d)
                print(f"[PRE-RUN] Sukses beralih ke akun '{clean_acc}'. Melanjutkan perintah...")
            else:
                print(f"[PRE-RUN] Akun '{clean_acc}' tidak ditemukan di menu ganti akun!")
                print("      -> Menutup menu ganti akun (mengirim BACK)...")
                d.press("back")
                time.sleep(1.5)
                print("akun tidak ditemukan")
                print("=========================================\n")
                return

        is_direct_url = target_user.startswith("http://") or target_user.startswith("https://") or "instagram.com" in target_user

        if is_direct_url:
            print(f"[3/5] Membuka URL postingan secara langsung menggunakan Intent...")
            d.shell(f'am start -a android.intent.action.VIEW -d "{target_user}" com.instagram.android')
            time.sleep(6)
            clear_any_popup_fast(d)
        else:
            print(f"[3/5] Mencari profil target: @{target_user}...")
            log_step("search_target", status="complete", device_id=device_pilihan, action="like")
            
            # 1. Klik ikon Search bawah pake beberapa strategi robust
            print("      Mencari dan mengklik ikon pencarian (search tab)...")
            clear_any_popup_fast(d)
            if d(resourceId="com.instagram.android:id/search_tab").exists:
                d(resourceId="com.instagram.android:id/search_tab").click()
                print("      -> Ikon search diklik via Resource ID")
            elif d(descriptionContains="Cari").exists:
                d(descriptionContains="Cari").click()
                print("      -> Ikon search diklik via descriptionContains('Cari')")
            elif d(descriptionContains="Search").exists:
                d(descriptionContains="Search").click()
                print("      -> Ikon search diklik via descriptionContains('Search')")
            elif d(descriptionContains="Cari dan Jelajahi").exists:
                d(descriptionContains="Cari dan Jelajahi").click()
                print("      -> Ikon search diklik via descriptionContains('Cari dan Jelajahi')")
            elif d(descriptionContains="Search and Explore").exists:
                d(descriptionContains="Search and Explore").click()
                print("      -> Ikon search diklik via descriptionContains('Search and Explore')")
            else:
                d.click(int(width * 0.30), int(height * 0.96))
                print("      -> Ikon search diklik via persentase koordinat")
            time.sleep(4)

            # 2. Klik kotak input atas (Bypass koordinat, langsung cari elemen kotak teksnya)
            print("      Mengklik kotak input pencarian...")
            input_box = d(className="android.widget.EditText")
            if d(resourceId="com.instagram.android:id/action_bar_search_edit_text").exists:
                d(resourceId="com.instagram.android:id/action_bar_search_edit_text").click()
                print("      -> Kotak input diklik via action_bar_search_edit_text")
            elif d(resourceId="com.instagram.android:id/search_bar").exists:
                d(resourceId="com.instagram.android:id/search_bar").click()
                print("      -> Kotak input diklik via search_bar")
            elif input_box.exists:
                input_box.click()
                print("      -> Kotak input diklik via EditText class")
            else:
                d.click(int(width * 0.5), int(height * 0.06)) # Fallback atas
                print("      -> Kotak input diklik via koordinat fallback")
            time.sleep(2)

            # 3. Hapus teks lama jika ada, lalu ketik nama target dari web
            print(f"      Mengetik nama akun: {target_user}")
            try:
                if d(resourceId="com.instagram.android:id/action_bar_search_edit_text").exists:
                    d(resourceId="com.instagram.android:id/action_bar_search_edit_text").clear_text()
                elif input_box.exists:
                    input_box.clear_text()
            except Exception as e:
                print(f"      -> Gagal membersihkan teks lama: {e}")
            
            d.send_keys(target_user)
            time.sleep(3) 

            # 4. SOLUSI AMAN: Tekan tombol ENTER/CARI di keyboard HP biar daftar pencarian ke-refresh
            print("      Menekan tombol Enter pada keyboard...")
            d.press("enter")
            time.sleep(4) # Tunggu hasil pencarian keluar

            # 5. KLIK HASIL: Pilih profil teratas dari hasil pencarian
            print(f"      Memilih profil teratas untuk @{target_user}...")
            clear_any_popup_fast(d)
            
            user_container_1 = d(resourceId="com.instagram.android:id/row_search_user_info_container")
            user_container_2 = d(resourceId="com.instagram.android:id/row_search_user_container")
            akun_target_text = d(text=target_user, className="android.widget.TextView")
            akun_target_contains = d(textContains=target_user, className="android.widget.TextView")
            
            # Prioritaskan mengklik teks agar tidak tidak sengaja mengklik avatar yang memiliki lingkaran story aktif
            if akun_target_text.exists:
                akun_target_text.click()
                print("      -> Berhasil mengklik profil teratas via TextView exact match")
            elif akun_target_contains.exists:
                akun_target_contains.click()
                print("      -> Berhasil mengklik profil teratas via TextView contains match")
            elif user_container_1.exists:
                user_container_1.click()
                print("      -> Berhasil mengklik profil teratas via row_search_user_info_container")
            elif user_container_2.exists:
                user_container_2.click()
                print("      -> Berhasil mengklik profil teratas via row_search_user_container")
            else:
                # Jika semua selektor elemen gagal, klik koordinat baris pertama hasil pencarian (di bawah tab)
                print("      -> Elemen profil teratas tidak terdeteksi, mencoba fallback koordinat baris pertama...")
                d.click(int(width * 0.5), int(height * 0.24))
            
            time.sleep(5) # Tunggu profil target terbuka sempurna
            clear_any_popup_fast(d)

            print("[4/5] Membuka postingan terbaru target...")
            log_step("open_first_post", status="complete", device_id=device_pilihan, action="like")
            
            post_clicked = False
            
            # JALANKAN PROSES SEARCH DALAM SATU RPC CALL VIA XPATH (Sangat Cepat!)
            print("      -> Mendapatkan daftar postingan via XPath...")
            try:
                candidate_posts = []
                for el in d(clickable=True):
                    try:
                        info = el.info
                        bounds = info.get('bounds', {})
                        desc = info.get('contentDescription', '') or ''
                        if bounds:
                            left = bounds.get('left', 0)
                            top = bounds.get('top', 0)
                            right = bounds.get('right', 0)
                            bottom = bounds.get('bottom', 0)
                            
                            x_center = (left + right) // 2
                            y_center = (top + bottom) // 2
                            el_width = right - left
                            el_height = bottom - top
                            
                            # Validasi deskripsi postingan (bahasa Indonesia / Inggris)
                            is_post_desc = any(p in desc for p in ["Foto oleh", "Photo by", "Video oleh", "Video by", "Postingan oleh", "Post oleh", "Media oleh"])
                            if is_post_desc and int(height * 0.25) < y_center < int(height * 0.90) and el_width > int(width * 0.25):
                                print(f"      -> Menemukan postingan terbaru via deskripsi: '{desc}' pada koordinat ({x_center}, {y_center})")
                                el.click()
                                post_clicked = True
                                break
                                
                            # Simpan sebagai kandidat kolom pertama di grid
                            if (0 < x_center < int(width * 0.35) and 
                                int(height * 0.25) < y_center < int(height * 0.90) and 
                                int(width * 0.20) < el_width < int(width * 0.45) and
                                el_height > 100):
                                candidate_posts.append((y_center, el, x_center, y_center))
                    except:
                        pass
                
                if not post_clicked and candidate_posts:
                    candidate_posts.sort(key=lambda x: x[0])
                    print(f"      -> Menemukan {len(candidate_posts)} postingan grid. Mengklik postingan pertama...")
                    candidate_posts[0][1].click()
                    post_clicked = True
            except Exception as e:
                print(f"      -> Gagal mencari postingan di grid: {e}")
                
            # 3. STRATEGI CADANGAN 2: Klik via layout list grid item (Hanya jika koordinat berada di bawah header)
            if not post_clicked:
                print("      -> Mencari via susunan layout list (android:id/list)...")
                try:
                    grid_item = d(resourceId="android:id/list").child(className="android.widget.LinearLayout").child(className="android.widget.FrameLayout")
                    if grid_item.exists:
                        bounds = grid_item.info.get('bounds')
                        if bounds:
                            y_center = (bounds['top'] + bounds['bottom']) // 2
                            el_width = bounds['right'] - bounds['left']
                            if y_center > int(height * 0.35) and el_width > int(width * 0.28):
                                print("      -> Menemukan postingan terbaru via layout list grid item")
                                grid_item.click()
                                post_clicked = True
                                
                except Exception as e:
                    print(f"      -> Gagal mencari via layout list grid: {e}")
                    
            # 4. STRATEGI CADANGAN 3: Fallback ke koordinat presisi
            if not post_clicked:
                # Kita coba klik 2 titik koordinat yang paling umum untuk postingan pertama
                print("      -> Menggunakan koordinat presisi fallback pertama (tanpa sorotan)...")
                d.click(int(width * 0.168), int(height * 0.55))
                time.sleep(2)
                print("      -> Menggunakan koordinat presisi fallback kedua (dengan sorotan)...")
                d.click(int(width * 0.168), int(height * 0.741))
                post_clicked = True
                
            time.sleep(4)
            clear_any_popup_fast(d)

        print("[5/5] Melakukan Eksekusi LIKE...")
        log_step("like_post", status="complete", device_id=device_pilihan, action="like")
        
        # Cari tombol Like yang aktif di layar (posisi terlihat di area aktif)
        active_like_btn = None
        is_already_liked = False
        like_candidates = []
        
        # 1. Cari berdasarkan Resource ID (RegEx match agar fleksibel dengan berbagai nama ID)
        sel = d(resourceIdMatches=".*(?i)(button_like|like_button|row_feed_button_like).*")
        if sel.exists:
            for idx in range(sel.count):
                try:
                    elem = sel[idx]
                    # Proteksi 1: Hanya izinkan Button atau ImageView (menghindari FrameLayout/TextView/ViewGroup)
                    if elem.info.get("className") not in ["android.widget.Button", "android.widget.ImageView"]:
                        continue
                    # Proteksi 2: Hindari deskripsi terlalu panjang (seperti deskripsi postingan yang berisi info likes)
                    desc = elem.info.get("contentDescription", "") or ""
                    if len(desc) > 35:
                        continue
                    b = elem.info.get("bounds")
                    if b:
                        y_center = (b["top"] + b["bottom"]) // 2
                        if height * 0.15 < y_center < height * 0.88:
                            like_candidates.append(elem)
                except:
                    pass
                        
        if not like_candidates:
            # 2. Cari berdasarkan Deskripsi (RegEx match)
            sel = d(descriptionMatches=".*(?i)(like|suka|unlike|disukai|batal).*")
            if sel.exists:
                for idx in range(sel.count):
                    try:
                        elem = sel[idx]
                        if elem.info.get("className") not in ["android.widget.Button", "android.widget.ImageView"]:
                            continue
                        desc = elem.info.get("contentDescription", "") or ""
                        if len(desc) > 35:
                            continue
                        b = elem.info.get("bounds")
                        if b:
                            y_center = (b["top"] + b["bottom"]) // 2
                            if height * 0.15 < y_center < height * 0.88:
                                like_candidates.append(elem)
                    except:
                        pass

        if like_candidates:
            active_like_btn = like_candidates[0]
            desc_text = active_like_btn.info.get("contentDescription", "") or ""
            text_val = active_like_btn.info.get("text", "") or ""
            combined_like_info = (desc_text + " " + text_val).lower()
            if any(x in combined_like_info for x in ["liked", "batalkan suka", "unlike", "disukai", "suka batal", "batal suka"]):
                is_already_liked = True
                
        if is_already_liked:
            print("      -> Postingan ini sudah disukai sebelumnya. Melewati...")
            like_success = True
        else:
            like_success = False
            if active_like_btn:
                try:
                    # Klik via koordinat bounds (geser X ke kanan agar lolos dari perlindungan pinggiran melengkung Samsung / Palm Rejection)
                    b = active_like_btn.info.get("bounds")
                    if b:
                        x_click = int(b["left"] + (b["right"] - b["left"]) * 0.75)
                        y_click = (b["top"] + b["bottom"]) // 2
                        d.click(x_click, y_click)
                        print(f"      -> Mengklik tombol Like aktif via koordinat: ({x_click}, {y_click})")
                        like_success = True
                    else:
                        active_like_btn.click()
                        like_success = True
                except Exception as e:
                    print(f"      -> Gagal mengklik tombol Like aktif: {e}")
                    
            if not like_success:
                print("      -> Tombol Like aktif tidak terdeteksi langsung, melakukan Double Tap di tengah layar...")
                d.double_click(width // 2, height // 2)
                like_success = True
                
            print(" [SUCCESS] Postingan target berhasil di-LIKE!")
            
        time.sleep(3)

        # Kembali ke Beranda (Home)
        print(" Kembali ke Beranda (Force Restart Instagram)...")
        try:
            d.app_stop("com.instagram.android")
            time.sleep(2.0)
            d.shell("am force-stop com.instagram.android")
            time.sleep(2.0)
            d.app_start("com.instagram.android")
            time.sleep(6.0)
            clear_any_popup_fast(d)
        except Exception as opt_err:
            print(f"      -> Gagal melakukan restart/refresh Beranda: {opt_err}")
        print("=========================================\n")
        print("___BOT_RESULT_SUCCESS___")
        log_complete(log_id, message="Liked target post successfully")
        sys.exit(0)

    except Exception as e:
        print(f" Terjadi kesalahan pada bot: {e}")
        print(f"___BOT_RESULT_ERROR___{str(e)}")
        log_error(log_id, error=str(e))
        sys.exit(1)

def like_by_keyword(keyword, limit=10, device_pilihan="all", my_account=""):
    log_id = log_activity("like_keyword", username=keyword, status="on_progress", mode="manual", device_id=device_pilihan, extra={"limit": limit, "my_account": my_account})
    try:
        print("=========================================")
        print(f" JALANKAN BOT LIKE BY KEYWORD: '{keyword}'")
        print(f" Target Like: {limit} postingan")
        if my_account:
            print(f" Menggunakan Akun Saya: {my_account}")
        print("=========================================")
        
        d = connect_adb(device_pilihan, action="like", step_label="[1/5] Menghubungkan ke perangkat Android via ADB...")
        width, height = d.window_size()
        print(f"Terhubung ke perangkat: {d.device_info.get('brand', 'Unknown')} {d.device_info.get('model', 'Device')} ({width}x{height})")

        open_instagram(d, device_pilihan, action="like", delay=6, step_label="[2/5] Membuka aplikasi Instagram...")
        clear_any_popup_fast(d)

        # Pastikan di Beranda sebelum melakukan swap atau navigasi utama
        _kembali_ke_beranda(d, width, height)

        # === PROSES SWAP AKUN DI AWAL (JIKA PARAMETER DIBERIKAN) ===
        if my_account and my_account.strip() != "":
            print(f"[PRE-RUN] Mengganti akun ke: '{my_account}'...")
            success = switch_instagram_account(my_account, device_pilihan)
            if not success:
                print(f"[-] ERROR: Gagal beralih ke akun '{my_account}' pada perangkat '{device_pilihan}'. Menghentikan bot.")
                return
            time.sleep(3.0)
        
        # Alur Navigasi Aman ke Halaman Pencarian (Search Page)
        print("[3/5] Navigasi ke halaman Pencarian (Search Page)...")
        log_step("navigate_search", status="complete", device_id=device_pilihan, action="like")
        search_opened = False
        
        # Loop maksimal 8 kali percobaan/BACK press
        for step in range(8):
            clear_any_popup_fast(d)
            
            # Cek jika tidak sengaja keluar dari Instagram
            try:
                if d.app_current().get('package') != 'com.instagram.android':
                    print("      -> Terdeteksi di luar Instagram, membuka kembali...")
                    d.app_start("com.instagram.android")
                    time.sleep(4.0)
                    continue
            except:
                pass
                
            # Cek apakah kolom input pencarian di atas sudah terlihat (artinya kita sudah sukses masuk ke halaman search)
            is_search_page = d(resourceId="com.instagram.android:id/action_bar_search_edit_text").exists \
                or d(resourceId="com.instagram.android:id/search_bar").exists \
                or (d(className="android.widget.EditText").exists and d(descriptionContains="Search").exists)
                
            if is_search_page:
                print("      -> Sukses berada di halaman Pencarian.")
                search_opened = True
                break
                
            # Coba cari tombol search tab di bawah
            search_tab = None
            if d(resourceId="com.instagram.android:id/search_tab").exists:
                search_tab = d(resourceId="com.instagram.android:id/search_tab")
            else:
                for desc in ["Cari", "Search", "Cari dan Jelajahi", "Explore", "Jelajahi"]:
                    if d(descriptionMatches=f"(?i)^({desc}|tab {desc}|{desc} tab)$").exists:
                        search_tab = d(descriptionMatches=f"(?i)^({desc}|tab {desc}|{desc} tab)$")
                        break
                        
            # Jika tombol search tab ditemukan, klik!
            if search_tab:
                try:
                    search_tab.click()
                    print("      -> Mengklik tombol search tab...")
                    time.sleep(3.0)
                    continue
                except:
                    pass
                    
            # Jika tab bar utama terdeteksi (tapi tombol search tab gagal ketemu), 
            # coba klik koordinat fallback search tab di baris bawah (biasanya X=30%, Y=96%)
            has_nav_tabs = any(d(resourceId=rid).exists for rid in [
                "com.instagram.android:id/feed_tab", 
                "com.instagram.android:id/home_tab",
                "com.instagram.android:id/profile_tab",
                "com.instagram.android:id/clips_tab",
                "com.instagram.android:id/reels_tab"
            ])
            if has_nav_tabs:
                print("      -> Tab bar navigasi terdeteksi. Mengklik koordinat search tab fallback (x=30%, y=96%)...")
                d.click(int(width * 0.30), int(height * 0.96))
                time.sleep(3.0)
                continue
                
            # Jika tidak ada tab bar sama sekali (tersesat di settings, detail postingan, dll.), tekan BACK untuk mundur
            print(f"      -> Sedang di sub-halaman/terhalang (Langkah {step+1}). Mengirim BACK...")
            d.press("back")
            time.sleep(2.0)
            
        if not search_opened:
            print("      -> Fallback terakhir: Mengklik koordinat tab pencarian (x=30%, y=96%)...")
            d.click(int(width * 0.30), int(height * 0.96))
            time.sleep(4.0)

        # 2. Klik kotak input pencarian atas
        print("      Mengklik kotak input pencarian...")
        input_box = d(className="android.widget.EditText")
        if d(resourceId="com.instagram.android:id/action_bar_search_edit_text").exists:
            d(resourceId="com.instagram.android:id/action_bar_search_edit_text").click()
            print("      -> Kotak input diklik via action_bar_search_edit_text")
        elif d(resourceId="com.instagram.android:id/search_bar").exists:
            d(resourceId="com.instagram.android:id/search_bar").click()
            print("      -> Kotak input diklik via search_bar")
        elif input_box.exists:
            input_box.click()
            print("      -> Kotak input diklik via EditText")
        else:
            d.click(int(width * 0.5), int(height * 0.06))
            print("      -> Kotak input diklik via koordinat fallback")
        time.sleep(2)

        # Tentukan tipe pencarian (Hashtag vs Akun) berdasarkan keberadaan ikon '@'
        is_account_search = "@" in keyword
        search_text = keyword.replace("@", "").strip()

        # 3. Hapus teks lama, lalu ketik keyword
        print(f"      Mengetik kata kunci: '{search_text}'")
        try:
            target_input = None
            if d(resourceId="com.instagram.android:id/action_bar_search_edit_text").exists:
                target_input = d(resourceId="com.instagram.android:id/action_bar_search_edit_text")
            elif d(resourceId="com.instagram.android:id/search_bar").exists:
                target_input = d(resourceId="com.instagram.android:id/search_bar")
            elif input_box.exists:
                target_input = input_box
                
            if target_input:
                target_input.click()
                time.sleep(1.0)
                target_input.clear_text()
                time.sleep(0.5)
                target_input.set_text(search_text)
            else:
                d.send_keys(search_text)
        except Exception as e:
            print(f"      -> Gagal mengetik kata kunci: {e}")
            try:
                d.send_keys(search_text)
            except:
                print("eror pas ngepost!")
        time.sleep(3) 

        # 4. Tekan ENTER/CARI untuk refresh hasil pencarian
        print("      Menekan tombol Enter pada keyboard...")
        d.press("enter")
        time.sleep(4)

        # 5. Navigasi ke tab pencarian yang sesuai
        if is_account_search:
            print("      Mencari tab 'Accounts'/'Akun' untuk membatasi ke profil...")
            clear_any_popup_fast(d)
            accounts_tab = None
            for tab_label in ["Accounts", "Akun", "Profil", "Profiles", "AKUN", "ACCOUNTS"]:
                if d(text=tab_label).exists:
                    accounts_tab = d(text=tab_label)
                    break
                elif d(textContains=tab_label).exists:
                    el = d(textContains=tab_label)
                    if el.info.get("bounds", {}).get("top", 0) < int(height * 0.20):
                        accounts_tab = el
                        break
            if accounts_tab:
                print(f"      -> Mengklik tab: '{accounts_tab.info.get('text')}'")
                accounts_tab.click()
                time.sleep(3)
            else:
                print("      -> Tab Accounts/Akun tidak ditemukan secara langsung, klik koordinat baris tab (x=30%, y=13%)...")
                d.click(int(width * 0.30), int(height * 0.13))
                time.sleep(2)
        else:
            # Mode Pencarian Kata Kunci (Keyword): Langsung di halaman utama pencarian (For You / Top / Popular)
            # Menggulir sedikit ke bawah agar postingan/grid terlihat jika tertutup hasil akun
            print("      -> Menggulir sedikit ke bawah agar postingan/grid hasil pencarian terlihat...")
            d.swipe(int(width * 0.5), int(height * 0.7), int(width * 0.5), int(height * 0.45), duration=0.2)
            time.sleep(2.0)

        time.sleep(3)
        clear_any_popup_fast(d)

        print("[4/5] Membuka postingan pertama di grid...")
        log_step("open_first_post", status="complete", device_id=device_pilihan, action="like")
        post_clicked = False
        
        # 1. Cari via Resource ID grid postingan
        for rid in ["com.instagram.android:id/media_set_row_image", "com.instagram.android:id/grid_item_image", "com.instagram.android:id/image_button"]:
            btn = d(resourceId=rid)
            if btn.exists:
                try:
                    btn.click()
                    print(f"      -> Postingan pertama diklik via Resource ID: '{rid}'")
                    post_clicked = True
                    break
                except:
                    pass
                    
        # 2. Cari via XPath ImageView kandidat
        if not post_clicked:
            try:
                candidate_posts = []
                for el in d(clickable=True):
                    try:
                        info = el.info
                        bounds = info.get('bounds', {})
                        desc = info.get('contentDescription', '') or ''
                        if bounds:
                            left = bounds.get('left', 0)
                            top = bounds.get('top', 0)
                            right = bounds.get('right', 0)
                            bottom = bounds.get('bottom', 0)
                            
                            x_center = (left + right) // 2
                            y_center = (top + bottom) // 2
                            el_width = right - left
                            el_height = bottom - top
                            
                            is_post_desc = any(p in desc for p in ["Foto oleh", "Photo by", "Video oleh", "Video by", "Postingan oleh", "Post oleh", "Media oleh"])
                            if is_post_desc and int(height * 0.25) < y_center < int(height * 0.90) and el_width > int(width * 0.25):
                                print(f"      -> Menemukan postingan terbaru via deskripsi: '{desc}' pada ({x_center}, {y_center})")
                                el.click()
                                post_clicked = True
                                break
                                
                            # Simpan sebagai kandidat kolom pertama di grid
                            if (0 < x_center < int(width * 0.35) and 
                                int(height * 0.25) < y_center < int(height * 0.90) and 
                                int(width * 0.20) < el_width < int(width * 0.45) and
                                el_height > 100):
                                candidate_posts.append((y_center, el, x_center, y_center))
                    except:
                        pass
                            
                if not post_clicked and candidate_posts:
                    candidate_posts.sort(key=lambda x: x[0])
                    print(f"      -> Menemukan {len(candidate_posts)} postingan grid. Mengklik postingan pertama...")
                    candidate_posts[0][1].click()
                    post_clicked = True
            except Exception as e:
                print(f"      -> Gagal mencari postingan di grid: {e}")

        if not post_clicked:
            # Fallback ke koordinat grid baris 1 kolom 1 (biasanya x=17%, y=50% untuk grid setelah header)
            print("      -> Menggunakan koordinat fallback untuk postingan pertama (0.17, 0.50)...")
            d.click(int(width * 0.17), int(height * 0.50))
            post_clicked = True

        time.sleep(4)
        
        # Verifikasi apakah halaman detail postingan berhasil dibuka
        print("      -> Memverifikasi apakah halaman detail postingan berhasil dibuka...")
        for check_open in range(3):
            is_grid = d(textMatches="(?i)^(Teratas|Top|Terbaru|Recent)$").exists \
                or d(resourceId="com.instagram.android:id/row_hashtag_header_container").exists \
                or d(resourceId="com.instagram.android:id/row_profile_header").exists
            
            has_post_indicators = d(resourceIdMatches=".*(?i)(button_like|like_button|button_comment|comment_button|row_feed_button).*").exists
            
            if not is_grid and has_post_indicators:
                print("      -> Sukses masuk ke halaman detail postingan!")
                break
            else:
                print(f"      -> Percobaan {check_open + 1}: Halaman detail belum terbuka. Mengklik ulang postingan pertama...")
                for rid in ["com.instagram.android:id/media_set_row_image", "com.instagram.android:id/grid_item_image", "com.instagram.android:id/image_button"]:
                    if d(resourceId=rid).exists:
                        try: d(resourceId=rid).click(); break
                        except: pass
                else:
                    d.click(int(width * 0.17), int(height * 0.50))
                time.sleep(3.5)

        clear_any_popup_fast(d)

        print("[5/5] Memulai Proses Liking...")
        log_step("like_posts", status="on_progress", device_id=device_pilihan, action="like")
        liked_count = 0
        consecutive_skipped = 0
        max_attempts = limit * 2 # Mencegah infinite loop jika banyak postingan terlewati

        for attempt in range(max_attempts):
            if liked_count >= limit:
                print(f" [SUCCESS] Target limit disukai tercapai ({liked_count}/{limit})")
                break
            
            print(f"\n--- Memeriksa postingan ke-{liked_count + 1} (Percobaan {attempt + 1}) ---")
            clear_any_popup_fast(d)
            check_and_clear_daily_limit(d)

            # Safety Check: Pastikan kita tidak terlempar kembali ke halaman grid hashtag / halaman profil target
            try:
                is_grid_page = d(textMatches="(?i)^(Teratas|Top|Terbaru|Recent)$").exists \
                    or d(resourceId="com.instagram.android:id/row_hashtag_header_container").exists
                
                has_post_interaction = d(resourceIdMatches=".*(?i)(button_like|like_button|button_comment|comment_button).*").exists
                is_profile_grid = (
                    d(resourceId="com.instagram.android:id/row_profile_header").exists \
                    or d(descriptionContains="Postingan").exists \
                    or d(text="Postingan").exists \
                    or d(text="Posts").exists
                ) and not has_post_interaction
                
                if is_grid_page or is_profile_grid:
                    print("      [Safety] Terdeteksi terlempar ke halaman grid/profil target! Mencoba masuk kembali ke detail postingan...")
                    post_btn = None
                    for rid in ["com.instagram.android:id/image_button", "com.instagram.android:id/media_set_row_image", "com.instagram.android:id/grid_item_image"]:
                        if d(resourceId=rid).exists:
                            post_btn = d(resourceId=rid)
                            break
                    if post_btn:
                        post_btn.click()
                    else:
                        d.click(int(width * 0.17), int(height * 0.55))
                    time.sleep(3.5)
            except Exception as safety_err:
                print(f"      [Safety] Gagal menjalankan check grid: {safety_err}")

            # Cari tombol Like yang aktif di layar (posisi terlihat di area aktif)
            active_like_btn = None
            is_already_liked = False
            like_candidates = []
            
            # 1. Cari berdasarkan Resource ID (RegEx match)
            sel = d(resourceIdMatches=".*(?i)(button_like|like_button|row_feed_button_like).*")
            if sel.exists:
                for idx in range(sel.count):
                    try:
                        elem = sel[idx]
                        # Proteksi 1: Hanya izinkan Button atau ImageView
                        if elem.info.get("className") not in ["android.widget.Button", "android.widget.ImageView"]:
                            continue
                        # Proteksi 2: Hindari deskripsi terlalu panjang
                        desc = elem.info.get("contentDescription", "") or ""
                        if len(desc) > 35:
                            continue
                        b = elem.info.get("bounds")
                        if b:
                            y_center = (b["top"] + b["bottom"]) // 2
                            if height * 0.15 < y_center < height * 0.88:
                                like_candidates.append(elem)
                    except:
                        pass
                            
            if not like_candidates:
                # 2. Cari berdasarkan Deskripsi (RegEx match)
                sel = d(descriptionMatches=".*(?i)(like|suka|unlike|disukai|batal).*")
                if sel.exists:
                    for idx in range(sel.count):
                        try:
                            elem = sel[idx]
                            if elem.info.get("className") not in ["android.widget.Button", "android.widget.ImageView"]:
                                continue
                            desc = elem.info.get("contentDescription", "") or ""
                            if len(desc) > 35:
                                continue
                            b = elem.info.get("bounds")
                            if b:
                                y_center = (b["top"] + b["bottom"]) // 2
                                if height * 0.15 < y_center < height * 0.88:
                                    like_candidates.append(elem)
                        except:
                            pass

            if like_candidates:
                active_like_btn = like_candidates[0]
                desc_text = active_like_btn.info.get("contentDescription", "") or ""
                text_val = active_like_btn.info.get("text", "") or ""
                combined_like_info = (desc_text + " " + text_val).lower()
                if any(x in combined_like_info for x in ["liked", "batalkan suka", "unlike", "disukai", "suka batal"]):
                    is_already_liked = True
            
            if is_already_liked:
                print("      -> Postingan ini sudah disukai sebelumnya. Melewati...")
                consecutive_skipped += 1
            else:
                # Lakukan klik Like
                click_success = False
                if active_like_btn:
                    try:
                        # Klik via koordinat bounds (geser X ke kanan agar lolos dari Palm Rejection Samsung)
                        b = active_like_btn.info.get("bounds")
                        if b:
                            x_click = int(b["left"] + (b["right"] - b["left"]) * 0.75)
                            y_click = (b["top"] + b["bottom"]) // 2
                            d.click(x_click, y_click)
                            print(f"      -> Mengklik tombol Like aktif via koordinat: ({x_click}, {y_click})")
                            click_success = True
                        else:
                            active_like_btn.click()
                            click_success = True
                    except Exception as e:
                        print(f"      -> Gagal mengklik tombol Like aktif: {e}")
                        
                if not click_success:
                    print("      -> Tombol Suka tidak terdeteksi langsung, melakukan Double Tap di tengah layar...")
                    d.double_click(width // 2, height // 2)
                    click_success = True
                
                if click_success:
                    liked_count += 1
                    consecutive_skipped = 0
                    print(f"      -> Postingan berhasil disukai! (Total: {liked_count}/{limit})")
                    time.sleep(random.uniform(1.5, 3.0))

            # Batas toleransi skip berturut-turut untuk menghindari stuck
            if consecutive_skipped >= 15:
                print("      -> Terlalu banyak postingan yang sudah disukai berturut-turut (15 kali). Berhenti.")
                break

            # Ambil hierarki layar sebelum swipe untuk perbandingan
            try:
                before_xml = d.dump_hierarchy()
            except:
                before_xml = ""

            # Swipe ke postingan berikutnya (vertikal)
            print("      -> Menggulir ke postingan berikutnya (swipe up)...")
            d.swipe(0.5, 0.75, 0.5, 0.25, duration=0.15)
            time.sleep(random.uniform(1.0, 2.0))

            # Ambil hierarki layar setelah swipe
            try:
                after_xml = d.dump_hierarchy()
            except:
                after_xml = ""

            # Cek jika halaman tidak bergeser (artinya postingan habis)
            if before_xml and after_xml and before_xml == after_xml:
                print("      -> Deteksi akhir konten: Layar tidak berubah setelah digulir. Postingan habis!")
                break

        print("\n--- KEMBALI KE BERANDA ---")
        print(" Kembali ke Beranda (Force Restart Instagram)...")
        try:
            d.app_stop("com.instagram.android")
            time.sleep(2.0)
            d.shell("am force-stop com.instagram.android")
            time.sleep(2.0)
            d.app_start("com.instagram.android")
            time.sleep(6.0)
            clear_any_popup_fast(d)
        except Exception as opt_err:
            print(f"      -> Gagal melakukan restart/refresh Beranda: {opt_err}")
            
        time.sleep(1.5)
        print("=========================================")
        print(f" BOT JALAN SELESAI: Berhasil menyukai {liked_count} postingan.")
        print("=========================================\n")
        print("___BOT_RESULT_SUCCESS___")
        log_complete(log_id, message=f"Liked {liked_count} posts successfully", extra_update={"liked_count": liked_count})
        sys.exit(0)

    except Exception as e:
        print(f"[ERROR EXCEPTION] Terjadi kesalahan saat bot like: {e}")
        print(f"___BOT_RESULT_ERROR___{str(e)}")
        log_error(log_id, error=str(e))
        sys.exit(1)

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
        print("  1. Like Target URL:  python3 bot_ig_like.py <url> [device_id] [my_account] target_url")
        print("  2. Like Normal:      python3 bot_ig_like.py <keyword> [limit] [device_id] [my_account] normal")
        sys.exit(1)

    # Deteksi Mode Trailing (Paling Belakang)
    last_arg = sys.argv[-1].lower() if len(sys.argv) > 1 else ""
    first_arg = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    
    # 1. Mode Trailing
    if last_arg == "target_url":
        target = sys.argv[1] if len(sys.argv) > 2 else ""
        device_id = sys.argv[2] if len(sys.argv) > 3 and sys.argv[2].lower() != "target_url" else "all"
        my_account = sys.argv[3] if len(sys.argv) > 4 and sys.argv[3].lower() != "target_url" else ""
        
        if not target:
            print("ERROR: URL target wajib disertakan!")
            sys.exit(1)
            
        devices = resolve_devices(device_id)
        if len(devices) > 1:
            run_parallel_threads(like_post_target, devices, target_user=target, my_account=my_account)
        else:
            like_post_target(target, device_pilihan=devices[0], my_account=my_account)

    elif last_arg == "normal":
        keyword = sys.argv[1] if len(sys.argv) > 2 else ""
        limit_str = sys.argv[2] if len(sys.argv) > 3 and sys.argv[2].lower() != "normal" else "10"
        device_id = sys.argv[3] if len(sys.argv) > 4 and sys.argv[3].lower() != "normal" else "all"
        my_account = sys.argv[4] if len(sys.argv) > 5 and sys.argv[4].lower() != "normal" else ""
        
        if not keyword:
            print("ERROR: Kata kunci pencarian wajib disertakan!")
            sys.exit(1)
            
        try:
            limit = int(limit_str)
        except ValueError:
            # Jika limit dilewati: e.g. python3 bot_ig_like.py "kucing" R9RY801LRPW normal
            device_id = limit_str
            my_account = sys.argv[3] if len(sys.argv) > 4 and sys.argv[3].lower() != "normal" else ""
            limit = 10
            
        devices = resolve_devices(device_id)
        if len(devices) > 1:
            run_parallel_threads(like_by_keyword, devices, keyword=keyword, limit=limit, my_account=my_account)
        else:
            like_by_keyword(keyword, limit, device_pilihan=devices[0], my_account=my_account)

    # 2. Mode Eksplisit (Awalan / di Depan) - kompatibilitas
    elif first_arg in ["target_url", "url", "username", "target", "like_target"]:
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        device_id = sys.argv[3] if len(sys.argv) > 3 else "all"
        my_account = sys.argv[4] if len(sys.argv) > 4 else ""
        
        if not target:
            print("ERROR: Username/URL target wajib disertakan!")
            sys.exit(1)
            
        devices = resolve_devices(device_id)
        if len(devices) > 1:
            run_parallel_threads(like_post_target, devices, target_user=target, my_account=my_account)
        else:
            like_post_target(target, device_pilihan=devices[0], my_account=my_account)
        
    elif first_arg in ["keyword", "like_keyword", "normal"]:
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        limit_str = sys.argv[3] if len(sys.argv) > 3 else "10"
        device_id = sys.argv[4] if len(sys.argv) > 4 else "all"
        my_account = sys.argv[5] if len(sys.argv) > 5 else ""
        
        if not keyword:
            print("ERROR: Kata kunci pencarian wajib disertakan!")
            sys.exit(1)
            
        try:
            limit = int(limit_str)
        except ValueError:
            limit = 10
            
        devices = resolve_devices(device_id)
        if len(devices) > 1:
            run_parallel_threads(like_by_keyword, devices, keyword=keyword, limit=limit, my_account=my_account)
        else:
            like_by_keyword(keyword, limit, device_pilihan=devices[0], my_account=my_account)
            
    # 3. Mode Otomatis (Kompatibilitas Mundur Tanpa Keyword Mode)
    else:
        target_atau_keyword = sys.argv[1]
        is_keyword = target_atau_keyword.startswith("#") or (len(sys.argv) > 2 and sys.argv[2].isdigit())
        
        if is_keyword:
            limit_str = sys.argv[2] if len(sys.argv) > 2 else "10"
            device_id = sys.argv[3] if len(sys.argv) > 3 else "all"
            my_account = sys.argv[4] if len(sys.argv) > 4 else ""
            try:
                limit = int(limit_str)
            except ValueError:
                limit = 10
            devices = resolve_devices(device_id)
            if len(devices) > 1:
                run_parallel_threads(like_by_keyword, devices, keyword=target_atau_keyword, limit=limit, my_account=my_account)
            else:
                like_by_keyword(target_atau_keyword, limit, device_pilihan=devices[0], my_account=my_account)
        else:
            device_id = sys.argv[2] if len(sys.argv) > 2 else "all"
            my_account = sys.argv[3] if len(sys.argv) > 3 else ""
            devices = resolve_devices(device_id)
            if len(devices) > 1:
                run_parallel_threads(like_post_target, devices, target_user=target_atau_keyword, my_account=my_account)
            else:
                like_post_target(target_atau_keyword, device_pilihan=devices[0], my_account=my_account)