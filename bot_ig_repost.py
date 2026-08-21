import sys
import uiautomator2 as u2
import time
import random
import re
import os
import urllib.request
import urllib.parse
import html as html_lib
import argparse
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
    threads = []
    print(f"[*] Menjalankan {target_func.__name__} secara paralel pada device: {devices}")
    for dev in devices:
        t = threading.Thread(target=target_func, args=args, kwargs={**kwargs, "device_pilihan": dev})
        threads.append(t)
        t.start()
        time.sleep(1.0)
    for t in threads:
        t.join()

def download_instagram_media(post_url):
    """
    Downloads media and original caption using ddinstagram.com proxy.
    Returns: (local_file_path, original_caption, is_video)
    """
    try:
        print(f"[*] Memulai pengunduhan media dari URL: {post_url}")
        
        match = re.search(r'/(p|reel)/([A-Za-z0-9_-]+)', post_url)
        if not match:
            print("[-] URL postingan tidak mengandung kode post valid.")
            return None, None, False
            
        post_type = match.group(1)
        code = match.group(2)
        dd_url = f"https://www.ddinstagram.com/{post_type}/{code}/"
        
        print(f"[*] Menghubungi proxy ddinstagram: {dd_url}...")
        
        req = urllib.request.Request(
            dd_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
        )
        
        with urllib.request.urlopen(req, timeout=20) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
            
        image_match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html_content)
        video_match = re.search(r'<meta\s+property=["\']og:video(?::secure_url)?["\']\s+content=["\']([^"\']+)["\']', html_content)
        desc_match = re.search(r'<meta\s+(?:property|name)=["\']og:description["\']\s+content=["\']([^"\']+)["\']', html_content)
        
        media_url = None
        is_video = False
        
        if video_match:
            media_url = video_match.group(1)
            is_video = True
            print("[+] Mendeteksi media tipe Video.")
        elif image_match:
            media_url = image_match.group(1)
            print("[+] Mendeteksi media tipe Gambar.")
            
        original_caption = ""
        if desc_match:
            original_caption = html_lib.unescape(desc_match.group(1))
            original_caption = re.sub(r'\s*•\s*Photos\s+from\s+@[A-Za-z0-9_.]+\'s\s+post.*', '', original_caption, flags=re.IGNORECASE)
            original_caption = re.sub(r'\s*•\s*Share\s+your\s+videos\s+with\s+friends.*', '', original_caption, flags=re.IGNORECASE)
            original_caption = original_caption.strip()
            print(f"[+] Berhasil mengambil caption asli: '{original_caption[:50]}...'")
            
        if not media_url:
            print("[-] Gagal mengekstrak URL media dari ddinstagram.")
            return None, original_caption, False
            
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
            
        ext = ".mp4" if is_video else ".jpg"
        filename = f"repost_{code}_{int(time.time())}{ext}"
        local_path = os.path.join("uploads", filename)
        
        print(f"[*] Mengunduh file dari: {media_url[:60]}...")
        media_req = urllib.request.Request(media_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(media_req, timeout=30) as media_res:
            with open(local_path, "wb") as f:
                f.write(media_res.read())
                
        print(f"[+] File berhasil diunduh dan disimpan di: {local_path}")
        return local_path, original_caption, is_video
        
    except Exception as e:
        print(f"[-] Terjadi kesalahan saat mengunduh media: {e}")
        return None, None, False

def swap_account_if_needed(d, width, height, my_account=""):
    """
    Melakukan proses ganti/swap akun di awal jika parameter my_account diberikan.
    """
    if not my_account or my_account.strip() == "":
        return
        
    print(f"[PRE-RUN] Mengganti akun ke: '{my_account}'...")
    
    # 1. Mengklik tombol Profil kanan bawah
    x_profile = int(width * 0.904)
    y_profile = int(height * 0.914)
    d.click(x_profile, y_profile)
    time.sleep(3.0)
    clear_any_popup_fast(d)
    
    # 2. Mengklik Nama Pengguna di pojok atas untuk membuka menu ganti akun
    print("      -> Mengklik nama akun di bagian atas untuk membuka menu ganti akun...")
    action_bar_title = d(resourceId="com.instagram.android:id/action_bar_title")
    title_badge = d(resourceId="com.instagram.android:id/title_with_badge_container")
    if action_bar_title.exists:
        action_bar_title.click()
    elif title_badge.exists:
        title_badge.click()
    else:
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
        sys.exit(1)

def do_repost_post(d, width, height):
    """
    Eksekusi penekanan ikon/tombol Repost pada postingan yang sedang terbuka.
    Returns True jika tombol repost/share berhasil diklik.
    """
    repost_clicked = False
    
    # Cari berdasarkan description / resourceId
    for selector in [
        d(description="Repost"),
        d(description="Posting ulang"),
        d(description="Posting Ulang"),
        d(descriptionContains="Repost"),
        d(descriptionContains="Posting ulang"),
        d(resourceId="com.instagram.android:id/row_feed_button_repost"),
        d(resourceIdMatches=".*repost.*")
    ]:
        if selector.exists:
            try:
                selector.click()
                print("      -> Ikon Repost langsung diklik.")
                repost_clicked = True
                time.sleep(3)
                break
            except:
                pass
                
    if not repost_clicked:
        print("      Ikon Repost langsung tidak ditemukan. Menggunakan fallback via menu Share...")
        share_clicked = False
        for desc in ["Kirim", "Send", "Share"]:
            el = d(descriptionContains=desc)
            if el.exists:
                try:
                    el.click()
                    share_clicked = True
                    break
                except:
                    pass
        if not share_clicked:
            if d(resourceId="com.instagram.android:id/row_feed_button_share").exists:
                try:
                    d(resourceId="com.instagram.android:id/row_feed_button_share").click()
                    share_clicked = True
                except:
                    pass
            else:
                d.click(int(width * 0.89), int(height * 0.65))
                share_clicked = True
        time.sleep(4)
        
        repost_btn = None
        try:
            selector = d(textMatches="(?i).*(repost|posting ulang).*")
            if selector.exists:
                repost_btn = selector
        except:
            pass
            
        if not repost_btn:
            try:
                selector = d(descriptionMatches="(?i).*(repost|posting ulang).*")
                if selector.exists:
                    repost_btn = selector
            except:
                pass
                
        if not repost_btn:
            print("      Tombol tidak terlihat, mencoba geser menu share...")
            d.swipe(0.8, 0.85, 0.2, 0.85, duration=0.2)
            time.sleep(2)
            try:
                selector = d(textMatches="(?i).*(repost|posting ulang).*")
                if selector.exists:
                    repost_btn = selector
            except:
                pass
                
        if repost_btn:
            try:
                repost_btn.click()
                print("      -> Tombol Repost/Posting Ulang di menu share diklik.")
                repost_clicked = True
                time.sleep(3)
            except:
                pass
        else:
            print("      -> Tombol tidak ditemukan via teks/deskripsi, mencoba klik koordinat perkiraan (fallback)...")
            d.click(int(width * 0.5), int(height * 0.85))
            repost_clicked = True
            time.sleep(3)

    # Dialog Konfirmasi
    confirm_btn = None
    for txt in ["Repost", "Posting ulang", "Posting Ulang", "Ya", "Yes"]:
        elem = d(text=txt)
        if elem.exists:
            confirm_btn = elem
            break
        elem = d(textContains=txt)
        if elem.exists:
            confirm_btn = elem
            break
            
    if confirm_btn:
        try:
            confirm_btn.click()
            print(f"      -> Konfirmasi Repost diklik: '{confirm_btn.info.get('text', '')}'")
            time.sleep(3.5)
        except:
            pass
            
    # Cek jika ada popup sukses dengan pilihan "Close" / "Tutup"
    for close_txt in ["Close", "Tutup", "Dismiss"]:
        btn_close = d(text=close_txt)
        if not btn_close.exists:
            btn_close = d(textMatches=f"(?i)^{close_txt}$")
        if not btn_close.exists:
            btn_close = d(descriptionMatches=f"(?i)^{close_txt}$")
        if btn_close.exists:
            try:
                btn_close.click()
                print(f"      -> Menutup popup sukses repost: '{close_txt}'")
                time.sleep(1.5)
                break
            except:
                pass
                
    return repost_clicked

def return_to_home_and_refresh(d, width, height):
    """
    Kembali ke halaman Beranda setelah repost selesai & Refresh feed.
    """
    print("[8] Kembali ke halaman Beranda & Refresh...")
    home_clicked = False
    for i in range(4):
        btn_home = None
        for rid in ["com.instagram.android:id/feed_tab", "com.instagram.android:id/home_tab"]:
            if d(resourceId=rid).exists:
                btn_home = d(resourceId=rid)
                break
        
        if not btn_home:
            for desc in ["Beranda", "Home", "Feed"]:
                el = d(descriptionContains=desc, packageName="com.instagram.android")
                if el.exists:
                    btn_home = el
                    break
        
        if btn_home:
            print("      -> Tab Beranda terdeteksi. Mengklik...")
            try:
                btn_home.click()
                home_clicked = True
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

def repost_by_url(post_url, caption_type="credit", custom_caption="", device_pilihan="all", my_account=""):
    """
    KONDISI 1: Repost berdasarkan Direct URL Postingan Instagram
    """
    log_id = log_activity("repost_url", username=post_url, status="on_progress", mode="manual", device_id=device_pilihan, extra={"my_account": my_account})
    try:
        print("=========================================")
        print(" BOT REPOST MODE: BY URL")
        print(f" Target URL: {post_url}")
        print(f" Tipe Caption: {caption_type}")
        print(f" Device: {device_pilihan}")
        if my_account:
            print(f" Akun Saya: {my_account}")
        print("=========================================")

        d = connect_adb(device_pilihan, action="repost", step_label="[1] Menghubungkan ke perangkat Android...")
        width, height = d.window_size()

        open_instagram(d, device_pilihan, action="repost", delay=6.0, step_label="[2] Membuka aplikasi Instagram...")
        clear_any_popup_fast(d)

        swap_account_if_needed(d, width, height, my_account)

        print(f"[3] Target berupa URL langsung. Membuka postingan via intent...")
        log_step("open_url", status="complete", device_id=device_pilihan, action="repost")
        d.shell(f'am start -a android.intent.action.VIEW -d "{post_url}" com.instagram.android')
        time.sleep(6.0)

        print("[4] Melakukan proses Repost...")
        log_step("repost_media", status="complete", device_id=device_pilihan, action="repost")
        do_repost_post(d, width, height)

        return_to_home_and_refresh(d, width, height)

        print("[+] REPOST BY URL SELESAI DENGAN SUKSES!")
        print("___BOT_RESULT_SUCCESS___")
        log_complete(log_id, message="Reposted URL successfully")
        return True

    except Exception as e:
        print(f"[-] ERROR REPOST BY URL: {e}")
        print(f"___BOT_RESULT_ERROR___{str(e)}")
        log_error(log_id, error=str(e))
        sys.exit(1)

def repost_by_username(target_user, caption_type="credit", custom_caption="", device_pilihan="all", my_account=""):
    """
    KONDISI 2: Repost berdasarkan Username Instagram Target
    """
    log_id = log_activity("repost_username", username=target_user, status="on_progress", mode="manual", device_id=device_pilihan, extra={"my_account": my_account})
    try:
        clean_user = target_user.replace("@", "").strip()
        print("=========================================")
        print(" BOT REPOST MODE: BY USERNAME")
        print(f" Target User: @{clean_user}")
        print(f" Tipe Caption: {caption_type}")
        print(f" Device: {device_pilihan}")
        if my_account:
            print(f" Akun Saya: {my_account}")
        print("=========================================")

        d = connect_adb(device_pilihan, action="repost", step_label="[1] Menghubungkan ke perangkat Android...")
        width, height = d.window_size()

        open_instagram(d, device_pilihan, action="repost", delay=6.0, step_label="[2] Membuka aplikasi Instagram...")
        clear_any_popup_fast(d)

        swap_account_if_needed(d, width, height, my_account)

        print(f"[3] Mencari profil username: @{clean_user}...")
        icon_search = d(resourceId="com.instagram.android:id/search_tab")
        if icon_search.exists:
            icon_search.click()
        elif d(descriptionContains="Cari").exists:
            d(descriptionContains="Cari").click()
        elif d(descriptionContains="Search").exists:
            d(descriptionContains="Search").click()
        else:
            d.click(int(width * 0.30), int(height * 0.96))
        time.sleep(4.0)

        print("      Mengklik kotak input pencarian...")
        if d(resourceId="com.instagram.android:id/action_bar_search_edit_text").exists:
            d(resourceId="com.instagram.android:id/action_bar_search_edit_text").click()
        elif d(className="android.widget.EditText").exists:
            d(className="android.widget.EditText").click()
        else:
            d.click(int(width * 0.5), int(height * 0.06))
        time.sleep(2.0)

        print(f"      Mengetik username: {clean_user}")
        d.send_keys(clean_user)
        time.sleep(3.0)
        d.press("enter")
        time.sleep(4.0)

        print("      Memilih profil teratas...")
        akun_target_text = d(text=clean_user, className="android.widget.TextView")
        akun_target_contains = d(textContains=clean_user, className="android.widget.TextView")

        if akun_target_text.exists:
            akun_target_text.click()
        elif akun_target_contains.exists:
            akun_target_contains.click()
        elif d(resourceId="com.instagram.android:id/row_search_user_info_container").exists:
            d(resourceId="com.instagram.android:id/row_search_user_info_container").click()
        else:
            d.click(int(width * 0.5), int(height * 0.24))
        # Tunggu sampai halaman profil/grid termuat sepenuhnya (maksimal 8 detik)
        print("      -> Menunggu grid postingan profil termuat...")
        grid_loaded = False
        for _ in range(8):
            if d(resourceIdMatches=".*(?i)(media_set_row_image|grid_item_image|image_button).*").exists or len(d.xpath('//*[contains(name(), "ImageView")]').all()) > 5:
                grid_loaded = True
                break
            time.sleep(1.0)

        print("[4] Membuka postingan terbaru di profil...")
        log_step("open_first_post", status="complete", device_id=device_pilihan, action="repost")
        post_clicked = False

        try:
            elements = d.xpath('//*[@clickable="true"]').all()
            candidate_posts = []
            for el in elements:
                desc = el.attrib.get('content-desc', '') or ''
                bounds = getattr(el, 'rect', None)
                if not bounds and 'bounds' in el.attrib:
                    m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', el.attrib['bounds'])
                    if m:
                        bounds = {
                            'left': int(m.group(1)),
                            'top': int(m.group(2)),
                            'right': int(m.group(3)),
                            'bottom': int(m.group(4))
                        }
                if bounds:
                    if isinstance(bounds, (list, tuple)):
                        left, top, right, bottom = bounds
                    else:
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
                        el.click()
                        post_clicked = True
                        break
                    
                    # Simpan sebagai kandidat kolom pertama di grid
                    if (0 < x_center < int(width * 0.35) and 
                        int(height * 0.25) < y_center < int(height * 0.90) and 
                        int(width * 0.20) < el_width < int(width * 0.45) and
                        el_height > 100):
                        candidate_posts.append((y_center, el, x_center, y_center))
            
            if not post_clicked and candidate_posts:
                candidate_posts.sort(key=lambda x: x[0])
                print(f"      -> Menemukan {len(candidate_posts)} postingan grid. Mengklik postingan pertama...")
                candidate_posts[0][1].click()
                post_clicked = True
        except Exception as e:
            print(f"      -> Gagal mencari postingan di grid: {e}")

        if not post_clicked:
            try:
                grid_item = d(resourceId="android:id/list").child(className="android.widget.LinearLayout").child(className="android.widget.FrameLayout")
                if grid_item.exists:
                    bounds = grid_item.info.get('bounds')
                    if bounds:
                        y_center = (bounds['top'] + bounds['bottom']) // 2
                        el_width = bounds['right'] - bounds['left']
                        if y_center > int(height * 0.35) and el_width > int(width * 0.28):
                            grid_item.click()
                            post_clicked = True
            except Exception as e:
                print(f"      -> Gagal mencari via layout list: {e}")

        if not post_clicked:
            print("      -> Menggunakan koordinat presisi fallback pertama...")
            d.click(int(width * 0.168), int(height * 0.55))
            time.sleep(2.0)
            print("      -> Menggunakan koordinat presisi fallback kedua...")
            d.click(int(width * 0.168), int(height * 0.741))
            post_clicked = True
        time.sleep(4.0)
        
        # Verifikasi apakah detail postingan berhasil terbuka
        detail_opened = False
        for check_detail in range(3):
            if d(resourceIdMatches=".*(?i)(button_like|like_button|button_comment|comment_button).*").exists:
                detail_opened = True
                break
            else:
                print(f"      -> Detail postingan belum terbuka (percobaan {check_detail+1}/3). Mencoba klik ulang postingan...")
                if 'candidate_posts' in locals() and candidate_posts:
                    candidate_posts[0][1].click()
                else:
                    d.click(int(width * 0.168), int(height * 0.55))
                time.sleep(3.5)
                clear_any_popup_fast(d)
                
        if not detail_opened:
            raise Exception("Gagal membuka halaman detail postingan di profil")

        print("[5] Melakukan proses Repost...")
        log_step("repost_media", status="complete", device_id=device_pilihan, action="repost")
        do_repost_post(d, width, height)

        return_to_home_and_refresh(d, width, height)

        print("[+] REPOST BY USERNAME SELESAI DENGAN SUKSES!")
        print("___BOT_RESULT_SUCCESS___")
        log_complete(log_id, message="Reposted username latest post successfully")
        return True

    except Exception as e:
        print(f"[-] ERROR REPOST BY USERNAME: {e}")
        print(f"___BOT_RESULT_ERROR___{str(e)}")
        log_error(log_id, error=str(e))
        sys.exit(1)

def repost_by_keyword(keyword, limit=5, device_pilihan="all", my_account=""):
    """
    KONDISI 3: Repost berdasarkan Kata Kunci (Keyword / Hashtag / Target User Tag)
    """
    log_id = log_activity("repost_keyword", username=keyword, status="on_progress", mode="manual", device_id=device_pilihan, extra={"limit": limit, "my_account": my_account})
    try:
        print("=========================================")
        print(f" BOT REPOST MODE: BY KEYWORD ('{keyword}')")
        print(f" Target Limit Repost: {limit} postingan")
        print(f" Device: {device_pilihan}")
        if my_account:
            print(f" Akun Saya: {my_account}")
        print("=========================================")

        d = connect_adb(device_pilihan, action="repost", step_label="[1/5] Menghubungkan ke perangkat Android via ADB...")
        width, height = d.window_size()
        print(f"Terhubung ke perangkat: {d.device_info.get('brand', 'Unknown')} {d.device_info.get('model', 'Device')} ({width}x{height})")

        open_instagram(d, device_pilihan, action="repost", delay=4.0, step_label="[2/5] Membuka aplikasi Instagram...")
        clear_any_popup_fast(d)

        swap_account_if_needed(d, width, height, my_account)

        print("[3/5] Navigasi ke halaman Pencarian (Search Page)...")
        log_step("navigate_search", status="complete", device_id=device_pilihan, action="repost")
        search_opened = False

        for step in range(8):
            clear_any_popup_fast(d)
            try:
                if d.app_current().get('package') != 'com.instagram.android':
                    print("      -> Terdeteksi di luar Instagram, membuka kembali...")
                    d.app_start("com.instagram.android")
                    time.sleep(4.0)
                    continue
            except:
                pass

            is_search_page = d(resourceId="com.instagram.android:id/action_bar_search_edit_text").exists \
                or d(resourceId="com.instagram.android:id/search_bar").exists \
                or (d(className="android.widget.EditText").exists and d(descriptionContains="Search").exists)

            if is_search_page:
                print("      -> Sukses berada di halaman Pencarian.")
                search_opened = True
                break

            search_tab = None
            if d(resourceId="com.instagram.android:id/search_tab").exists:
                search_tab = d(resourceId="com.instagram.android:id/search_tab")
            else:
                for desc in ["Cari", "Search", "Cari dan Jelajahi", "Explore", "Jelajahi"]:
                    if d(descriptionMatches=f"(?i)^({desc}|tab {desc}|{desc} tab)$").exists:
                        search_tab = d(descriptionMatches=f"(?i)^({desc}|tab {desc}|{desc} tab)$")
                        break

            if search_tab:
                try:
                    search_tab.click()
                    print("      -> Mengklik tombol search tab...")
                    time.sleep(3.0)
                    continue
                except:
                    pass

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

            print(f"      -> Sedang di sub-halaman/terhalang (Langkah {step+1}). Mengirim BACK...")
            d.press("back")
            time.sleep(2.0)

        if not search_opened:
            print("      -> Fallback terakhir: Mengklik koordinat tab pencarian (x=30%, y=96%)...")
            d.click(int(width * 0.30), int(height * 0.96))
            time.sleep(4.0)

        print("      Mengklik kotak input pencarian...")
        input_box = d(className="android.widget.EditText")
        if d(resourceId="com.instagram.android:id/action_bar_search_edit_text").exists:
            d(resourceId="com.instagram.android:id/action_bar_search_edit_text").click()
        elif d(resourceId="com.instagram.android:id/search_bar").exists:
            d(resourceId="com.instagram.android:id/search_bar").click()
        elif input_box.exists:
            input_box.click()
        else:
            d.click(int(width * 0.5), int(height * 0.06))
        time.sleep(2.0)

        is_account_search = "@" in keyword
        search_text = keyword.replace("@", "").strip()

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
                pass
        time.sleep(3.0)

        print("      Menekan tombol Enter pada keyboard...")
        d.press("enter")
        time.sleep(4.0)

        if is_account_search:
            print("      Mencari tab 'Accounts'/'Akun'...")
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
                time.sleep(3.0)
            else:
                print("      -> Tab Accounts/Akun tidak ditemukan, klik koordinat (x=30%, y=13%)...")
                d.click(int(width * 0.30), int(height * 0.13))
                time.sleep(2.0)

            print("      Mengklik profil hasil pencarian pertama...")
            clear_any_popup_fast(d)
            profile_item = None
            for rid in [
                "com.instagram.android:id/row_search_user_info_container",
                "com.instagram.android:id/row_search_user_container",
                "com.instagram.android:id/row_search_user_username",
                "com.instagram.android:id/title"
            ]:
                if d(resourceId=rid).exists:
                    profile_item = d(resourceId=rid)
                    break
            if not profile_item or not profile_item.exists:
                profile_item = d(textMatches=f"(?i).*{re.escape(search_text)}.*")

            profile_clicked = False
            if profile_item and profile_item.exists:
                try:
                    profile_item.click()
                    profile_clicked = True
                except:
                    pass
            if not profile_clicked:
                print("      -> Elemen profil tidak ditemukan, klik koordinat (x=50%, y=25%)...")
                d.click(int(width * 0.5), int(height * 0.25))
        else:
            # Mode Pencarian Kata Kunci (Keyword): Langsung di halaman utama pencarian (For You / Top / Popular)
            # Menggulir sedikit ke bawah agar postingan/grid terlihat jika tertutup hasil akun
            print("      -> Menggulir sedikit ke bawah agar postingan/grid hasil pencarian terlihat...")
            d.swipe(int(width * 0.5), int(height * 0.7), int(width * 0.5), int(height * 0.45), duration=0.2)
            time.sleep(2.0)

        # Tunggu sampai halaman hashtag/grid termuat sepenuhnya (maksimal 8 detik)
        print("      -> Menunggu grid postingan termuat...")
        grid_loaded = False
        for _ in range(8):
            if d(resourceIdMatches=".*(?i)(media_set_row_image|grid_item_image|image_button).*").exists or len(d.xpath('//*[contains(name(), "ImageView")]').all()) > 5:
                grid_loaded = True
                break
            time.sleep(1.0)
            
        clear_any_popup_fast(d)

        print("[4/5] Membuka postingan pertama di grid...")
        log_step("open_first_post", status="complete", device_id=device_pilihan, action="repost")
        post_clicked = False
        for rid in ["com.instagram.android:id/media_set_row_image", "com.instagram.android:id/grid_item_image", "com.instagram.android:id/image_button"]:
            btn = d(resourceId=rid)
            if btn.exists:
                try:
                    btn.click()
                    post_clicked = True
                    break
                except:
                    pass

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
            print("      -> Menggunakan koordinat fallback postingan pertama (0.17, 0.50)...")
            d.click(int(width * 0.17), int(height * 0.50))
            post_clicked = True

        time.sleep(4.0)
        clear_any_popup_fast(d)

        # Verifikasi apakah detail postingan berhasil terbuka
        detail_opened = False
        for check_detail in range(3):
            # Di halaman detail postingan, tombol-tombol interaksi (Like, Comment, Share) harus ada,
            # dan grid pencarian / hashtag header sudah tidak ada atau ada tombol BACK khas detail.
            if d(resourceIdMatches=".*(?i)(button_like|like_button|button_comment|comment_button).*").exists:
                detail_opened = True
                break
            else:
                print(f"      -> Detail postingan belum terbuka (percobaan {check_detail+1}/3). Mencoba klik ulang postingan pertama...")
                if 'candidate_posts' in locals() and candidate_posts:
                    candidate_posts[0][1].click()
                else:
                    d.click(int(width * 0.17), int(height * 0.50))
                time.sleep(3.5)
                clear_any_popup_fast(d)
                
        if not detail_opened:
            raise Exception("Gagal membuka halaman detail postingan pertama di grid")

        print("[5/5] Memulai Proses Reposting...")
        log_step("repost_media_loop", status="on_progress", device_id=device_pilihan, action="repost")
        repost_count = 0
        max_attempts = limit * 2
        
        stopper_device = f"stop_farming_{device_pilihan}.txt"
        stopper_global = "stop_farming_all.txt"

        for attempt in range(max_attempts):
            if repost_count >= limit:
                print(f" [SUCCESS] Target limit repost tercapai ({repost_count}/{limit})")
                break
                
            if os.path.exists(stopper_device) or os.path.exists(stopper_global):
                print(f"\n[STOP] Terdeteksi file stopper. Menghentikan proses...")
                for fpath in [stopper_device, stopper_global]:
                    if os.path.exists(fpath):
                        try:
                            os.remove(fpath)
                        except:
                            pass
                break

            print(f"\n--- Memeriksa postingan ke-{repost_count + 1} (Percobaan {attempt + 1}) ---")
            clear_any_popup_fast(d)
            check_and_clear_daily_limit(d)

            # Safety Check grid/profile
            try:
                is_grid_page = d(textMatches="(?i)^(Teratas|Top|Terbaru|Recent)$").exists \
                    or d(resourceId="com.instagram.android:id/row_hashtag_header_container").exists
                
                is_profile_grid = d(resourceId="com.instagram.android:id/row_profile_header").exists \
                    or d(descriptionContains="Postingan").exists \
                    or d(text="Postingan").exists \
                    or d(text="Posts").exists
                
                if is_grid_page or is_profile_grid:
                    print("      [Safety] Terdeteksi terlempar ke halaman grid/profil target! Mencoba masuk kembali...")
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

            do_repost_post(d, width, height)

            repost_count += 1
            print(f"      [SUKSES] Postingan berhasil di-repost! (Total: {repost_count}/{limit})")
            time.sleep(1.5)

            print("      -> Menggulir ke postingan berikutnya (swipe up)...")
            d.swipe(0.5, 0.75, 0.5, 0.25, duration=0.25)
            time.sleep(random.uniform(2.5, 4.5))

        print("\n[+] OPTIMALISASI: Melakukan Force Stop Instagram...")
        try:
            d.app_stop("com.instagram.android")
            time.sleep(2.0)
            d.shell("am force-stop com.instagram.android")
            time.sleep(2.0)
            d.app_start("com.instagram.android")
            time.sleep(5.0)
            clear_any_popup_fast(d)
        except Exception as opt_err:
            print(f"      -> Gagal melakukan optimalisasi cache: {opt_err}")

        print("=========================================")
        print(f" BOT REPOST BY KEYWORD SELESAI")
        print(f" Total Repost Sukses: {repost_count}")
        print("=========================================\n")
        print("___BOT_RESULT_SUCCESS___")
        log_complete(log_id, message=f"Reposted {repost_count} keyword posts successfully", extra_update={"repost_count": repost_count})
        return True

    except Exception as e:
        print(f"[ERROR EXCEPTION] Terjadi kesalahan saat bot repost: {e}")
        print(f"___BOT_RESULT_ERROR___{str(e)}")
        log_error(log_id, error=str(e))
        sys.exit(1)

def run_repost(target, mode=None, caption_type="credit", custom_caption="", device_pilihan="all", my_account="", limit=5):
    """
    Master function untuk memilih & mengoperasikan mode repost (username, url, atau keyword)
    """
    if not target:
        print("[-] Error: Target (username, URL, atau keyword) wajib disertakan.")
        sys.exit(1)

    # Deteksi otomatis mode jika belum ditentukan
    if not mode or mode in ["auto", "none", ""]:
        if target.startswith("http://") or target.startswith("https://") or "instagram.com" in target:
            mode = "url"
        elif target.startswith("#") or " " in target:
            mode = "keyword"
        else:
            mode = "username"

    mode = mode.lower().replace("by_", "")

    if mode == "url":
        return repost_by_url(target, caption_type, custom_caption, device_pilihan, my_account)
    elif mode == "keyword":
        return repost_by_keyword(target, limit, device_pilihan, my_account)
    elif mode == "username":
        return repost_by_username(target, caption_type, custom_caption, device_pilihan, my_account)
    else:
        print(f"[-] Mode '{mode}' tidak dikenal. Menggunakan mode fallback: username")
        return repost_by_username(target, caption_type, custom_caption, device_pilihan, my_account)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Bot Instagram Repost Unified (Username, URL, & Keyword)")
    parser.add_argument("pos_args", nargs="*", help="Positional arguments untuk kompatibilitas mundur")
    parser.add_argument("--mode", "-m", choices=["username", "url", "keyword", "by_username", "by_url", "by_keyword", "auto", "normal", "target_url", "user"], default=None, help="Mode repost: username, url, atau keyword")
    parser.add_argument("--target", "--target_url", "--target-url", "--url", "--keyword", "-t", default=None, help="Target username, URL, atau keyword search")
    parser.add_argument("--caption-type", "--caption_type", default="credit", choices=["credit", "custom", "blank"], help="Tipe caption")
    parser.add_argument("--custom-caption", "--custom_caption", "--caption", "--komentar", default="", help="Teks custom caption jika caption_type=custom")
    parser.add_argument("--limit", "--count", "-l", type=int, default=5, help="Jumlah post yang di-repost (khusus mode keyword)")
    parser.add_argument("--device", "--device-id", "--device_id", "-d", default="all", help="Device ID atau 'all'")
    parser.add_argument("--my-account", "--my_account", "--account", "-a", default="", help="Username akun saya untuk beralih akun")
    
    args, unknown = parser.parse_known_args() if hasattr(parser, 'parse_known_args') else (parser.parse_args(), [])
    
    target = args.target
    mode = args.mode
    caption_type = args.caption_type
    custom_caption = args.custom_caption
    limit = args.limit
    device_id = args.device
    my_account = args.my_account
    
    pos = args.pos_args

    if pos:
        # 1. Cek Trailing Mode (Mode di paling akhir)
        last_arg = pos[-1].lower() if pos else ""
        if last_arg in ["username", "url", "keyword", "target_url", "normal"]:
            if last_arg == "target_url":
                mode = "url"
            elif last_arg == "normal":
                mode = "keyword"
            else:
                mode = last_arg
            pos.pop() # Buang argumen mode dari list positional
            
            if pos:
                target = pos[0]
                if mode == "keyword" or last_arg == "normal":
                    if len(pos) > 1:
                        if pos[1].isdigit():
                            limit = int(pos[1])
                        else:
                            device_id = pos[1]
                    if len(pos) > 2:
                        if pos[1].isdigit():
                            device_id = pos[2]
                        else:
                            my_account = pos[2]
                    if len(pos) > 3:
                        my_account = pos[3]
                else:
                    # mode in ["username", "url"]
                    if len(pos) == 2:
                        if pos[1].lower() in ["credit", "blank", "custom"]:
                            caption_type = pos[1].lower()
                        else:
                            device_id = pos[1]
                    elif len(pos) == 3:
                        if pos[1].lower() in ["credit", "blank", "custom"]:
                            caption_type = pos[1].lower()
                            device_id = pos[2]
                        else:
                            caption_type = "custom"
                            custom_caption = pos[1]
                            device_id = pos[2]
                    elif len(pos) >= 4:
                        caption_type = pos[1]
                        custom_caption = pos[2]
                        device_id = pos[3]
                        if len(pos) > 4:
                            my_account = pos[4]
                            
        # 2. Cek Leading Mode (Mode di posisi pertama)
        elif pos[0].lower().replace("by_", "") in ["username", "url", "keyword"]:
            mode = pos[0].lower().replace("by_", "")
            if len(pos) > 1:
                target = pos[1]
            if mode == "keyword":
                if len(pos) > 2 and pos[2].isdigit():
                    limit = int(pos[2])
                if len(pos) > 3:
                    device_id = pos[3]
                if len(pos) > 4:
                    my_account = pos[4]
            else:
                pos_sub = pos[1:] # sub-arguments without mode keyword
                if len(pos_sub) == 2:
                    if pos_sub[1].lower() in ["credit", "blank", "custom"]:
                        caption_type = pos_sub[1].lower()
                    else:
                        device_id = pos_sub[1]
                elif len(pos_sub) == 3:
                    if pos_sub[1].lower() in ["credit", "blank", "custom"]:
                        caption_type = pos_sub[1].lower()
                        device_id = pos_sub[2]
                    else:
                        caption_type = "custom"
                        custom_caption = pos_sub[1]
                        device_id = pos_sub[2]
                elif len(pos_sub) >= 4:
                    caption_type = pos_sub[1]
                    custom_caption = pos_sub[2]
                    device_id = pos_sub[3]
                    if len(pos_sub) > 4:
                        my_account = pos_sub[4]
                        
        # 3. Auto-detect Tanpa Mode Keyword (Kompatibilitas Mundur)
        else:
            target = pos[0]
            # Cek jika arg2 adalah angka limit -> mode keyword
            if len(pos) > 1 and pos[1].isdigit() and pos[1].lower() not in ["credit", "blank", "custom"]:
                mode = "keyword"
                limit = int(pos[1])
                if len(pos) > 2:
                    device_id = pos[2]
                if len(pos) > 3:
                    my_account = pos[3]
            else:
                # Mode username atau URL
                if len(pos) == 2:
                    arg2 = pos[1]
                    if arg2.lower() in ["credit", "blank", "custom"]:
                        caption_type = arg2.lower()
                    else:
                        device_id = arg2
                elif len(pos) == 3:
                    arg2, arg3 = pos[1], pos[2]
                    if arg2.lower() in ["credit", "blank", "custom"]:
                        caption_type = arg2.lower()
                        device_id = arg3
                    else:
                        caption_type = "custom"
                        custom_caption = arg2
                        device_id = arg3
                elif len(pos) >= 4:
                    caption_type = pos[1]
                    custom_caption = pos[2]
                    device_id = pos[3]
                    if len(pos) > 4:
                        my_account = pos[4]

    if mode:
        mode_lower = mode.lower().strip()
        if mode_lower in ["normal", "by_keyword", "keyword"]:
            mode = "keyword"
        elif mode_lower in ["target_url", "by_url", "url"]:
            mode = "url"
        elif mode_lower in ["by_username", "username", "user"]:
            mode = "username"

    return target, mode, caption_type, custom_caption, limit, device_id, my_account

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
    target, mode, caption_type, custom_caption, limit, device_id, my_account = parse_arguments()

    if not target:
        if not sys.stdin.isatty():
            print("[-] Error: Target (username, URL, atau keyword) wajib disertakan.")
            sys.exit(1)
        try:
            print("\n==================================================")
            print("           BOT INSTAGRAM REPOST AUTOMATION        ")
            print("==================================================")
            print("Pilih Mode Repost:")
            print("  1. By Username (Repost postingan terbaru dari username target)")
            print("  2. By URL (Repost postingan langsung via link IG)")
            print("  3. By Keyword / Hashtag (Repost beberapa postingan via pencarian keyword/hashtag)")
            pilihan = input("Masukkan pilihan mode (1/2/3, default 1): ").strip()
            
            if pilihan == "2":
                mode = "url"
                target = input("Masukkan URL postingan target: ").strip()
            elif pilihan == "3":
                mode = "keyword"
                target = input("Masukkan keyword / hashtag pencarian: ").strip()
                ans_limit = input("Masukkan jumlah repost (default 5): ").strip()
                if ans_limit and ans_limit.isdigit():
                    limit = int(ans_limit)
            else:
                mode = "username"
                target = input("Masukkan username target (tanpa @): ").strip()

            if mode in ["username", "url"]:
                ans_cap = input("Pilih caption type ('credit' / 'custom' / 'blank', default 'credit'): ").strip()
                if ans_cap:
                    caption_type = ans_cap
                if caption_type == 'custom':
                    custom_caption = input("Masukkan custom caption text: ").strip()

            ans_dev = input("Masukkan device ID (kosongkan/press Enter untuk 'all'): ").strip()
            if ans_dev:
                device_id = ans_dev

            ans_acc = input("Masukkan nama akun Anda (kosongkan jika tidak ganti akun): ").strip()
            if ans_acc:
                my_account = ans_acc

        except (EOFError, KeyboardInterrupt):
            print("\nEksekusi dibatalkan.")
            sys.exit(1)

    devices = resolve_devices(device_id)
    if len(devices) > 1:
        run_parallel_threads(
            run_repost,
            devices,
            target=target,
            mode=mode,
            caption_type=caption_type,
            custom_caption=custom_caption,
            my_account=my_account,
            limit=limit
        )
    else:
        run_repost(
            target=target,
            mode=mode,
            caption_type=caption_type,
            custom_caption=custom_caption,
            device_pilihan=devices[0],
            my_account=my_account,
            limit=limit
        )
