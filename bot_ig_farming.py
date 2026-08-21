import sys
import uiautomator2 as u2
import time
import random
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
    from bot_instagram_clear_popups import clear_any_popup_fast, clear_post_login_popups
except ImportError:
    def clear_any_popup_fast(d, *args, **kwargs):
        return False
    def clear_post_login_popups(d, *args, **kwargs):
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

def is_currently_comment_thread(d):
    """
    Mendeteksi secara andal apakah laci/halaman komentar sedang terbuka di layar (bahkan setelah keyboard ditutup).
    """
    return d(text="Reply").exists \
        or d(text="Balas").exists \
        or d(text="Edit").exists \
        or d(textMatches="(?i).*(No comments yet|Belum ada komentar|Start the conversation).*").exists \
        or d(className="android.widget.EditText").exists \
        or d(resourceId="com.instagram.android:id/layout_comment_thread_edittext").exists \
        or d(resourceId="com.instagram.android:id/layout_comment_thread_edittext_container").exists \
        or d(resourceId="com.instagram.android:id/comment_composer_container").exists \
        or d(resourceId="com.instagram.android:id/layout_comment_thread_post_button").exists \
        or d(resourceId="com.instagram.android:id/layout_comment_thread_post_button_icon").exists \
        or d(resourceId="com.instagram.android:id/comment_thread_list").exists \
        or d(resourceId="com.instagram.android:id/comment_thread_recyclerview").exists \
        or d(resourceId="com.instagram.android:id/row_comment_textview_comment").exists \
        or d(resourceId="com.instagram.android:id/row_comment_textview_reply_button").exists \
        or d(resourceId="com.instagram.android:id/row_comment_like_button").exists \
        or d(resourceId="com.instagram.android:id/comment_like_button").exists \
        or d(resourceId="com.instagram.android:id/comment_reply_button").exists \
        or d(resourceId="com.instagram.android:id/comment_composer_gif_button").exists \
        or d(resourceId="com.instagram.android:id/gif_button").exists \
        or d(resourceId="com.instagram.android:id/emoji_palette").exists \
        or d(textMatches="(?i)^(Comments|Komentar|Replies|Balasan)$").exists

def click_element_robust(d, selector_list):
    for selector in selector_list:
        if selector.exists:
            try:
                bounds = selector.info.get('bounds')
                if bounds:
                    x_center = (bounds['left'] + bounds['right']) // 2
                    y_center = (bounds['top'] + bounds['bottom']) // 2
                    # Pastikan berada di dalam layar vertikal yang wajar
                    height = d.window_size()[1]
                    if int(height * 0.1) < y_center < int(height * 0.95):
                        d.click(x_center, y_center)
                        return True
                else:
                    selector.click()
                    return True
            except Exception:
                try:
                    selector.click()
                    return True
                except Exception:
                    pass
    return False

def find_feed_buttons(d, width):
    # Cari like button sebagai patokan baris tombol interaksi
    btn_like = d(resourceIdMatches=".*(?i)(button_like|like_button).*")
    if not btn_like.exists:
        for desc in ["Suka", "Like", "Suka Icon", "Like Icon"]:
            if d(description=desc).exists:
                btn_like = d(description=desc)
                break
                
    if btn_like.exists:
        try:
            bounds = btn_like.info.get('bounds')
            if bounds:
                y_center = (bounds['top'] + bounds['bottom']) // 2
                
                # Deteksi apakah tombol repost (panah berputar) ada di layar
                btn_repost = d(resourceIdMatches=".*(?i)(button_repost|repost_button).*")
                if not btn_repost.exists:
                    for desc in ["Repost", "Posting Ulang", "Posting ulang"]:
                        if d(description=desc).exists:
                            btn_repost = d(description=desc)
                            break
                            
                # Jika tombol repost terdeteksi di bar, susunan tombolnya ada 5 (Like, Comment, Repost, Share, Save)
                if btn_repost.exists:
                    return {
                        "like": ( (bounds['left'] + bounds['right']) // 2, y_center ),
                        "comment": ( int(width * 0.22), y_center ),
                        "repost": ( int(width * 0.36), y_center ),
                        "share": ( int(width * 0.50), y_center ),
                        "save": ( int(width * 0.92), y_center )
                    }
                else:
                    # Susunan standar 4 tombol (Like, Comment, Share, Save)
                    return {
                        "like": ( (bounds['left'] + bounds['right']) // 2, y_center ),
                        "comment": ( int(width * 0.22), y_center ),
                        "repost": ( int(width * 0.36), y_center ), # Fallback saja
                        "share": ( int(width * 0.36), y_center ),
                        "save": ( int(width * 0.92), y_center )
                    }
        except Exception:
            pass
            
    # Fallback jika tidak terdeteksi
    y_fallback = int(d.window_size()[1] * 0.65)
    return {
        "like": ( int(width * 0.08), y_fallback ),
        "comment": ( int(width * 0.22), y_fallback ),
        "repost": ( int(width * 0.36), y_fallback ),
        "share": ( int(width * 0.36), y_fallback ),
        "save": ( int(width * 0.92), y_fallback )
    }

def print_farming_summary(stats, beranda_count, reels_count):
    print("\n=========================================")
    print("--- RINGKASAN AKTIVITAS FARMING ---")
    print(f" - Total Postingan Beranda: {beranda_count}")
    print(f"   * Disukai (Like): {stats.get('like', 0)}")
    print(f"   * Dikomentari (Comment): {stats.get('comment', 0)}")
    print(f"   * Diposting Ulang (Repost): {stats.get('repost', 0)}")
    print(f"   * Disimpan (Save): {stats.get('save', 0)}")
    print(f"   * Hanya Dibaca (Scroll): {stats.get('scroll', 0)}")
    print(f" - Total Postingan Reels: {reels_count}")
    print(f"   * Disukai (Like): {stats.get('reels_like', 0)}")
    print(f"   * Dikomentari (Comment): {stats.get('reels_comment', 0)}")
    print(f"   * Diposting Ulang (Repost): {stats.get('reels_repost', 0)}")
    print(f"   * Hanya Ditonton (Scroll): {stats.get('reels_scroll', 0)}")
    print("=========================================\n")

def run_farming_bot(device_pilihan="all", total_posts=10):
    import os
    log_id = log_activity("farming", username="system", status="on_progress", mode="farming", device_id=device_pilihan, extra={"total_posts": total_posts})
    try:
        # Tentukan pembagian jumlah postingan antara Beranda dan Reels
        loop_infinite = (total_posts <= 0)
        if loop_infinite:
            num_beranda_target = random.randint(3, 5)
            num_reels_target = -1  # Tak terbatas
        else:
            if total_posts >= 2:
                num_beranda_target = min(random.randint(3, 5), total_posts - 1)
                num_reels_target = total_posts - num_beranda_target
            else:
                num_beranda_target = total_posts
                num_reels_target = 0

        # Nama file stopper khusus perangkat dan global
        stopper_device = f"stop_farming_{device_pilihan}.txt"
        stopper_global = "stop_farming_all.txt"
        
        # Reset stopper lama di awal eksekusi
        for fpath in [stopper_device, stopper_global]:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                    print(f"      -> Menghapus file stopper lama: {fpath}")
                except Exception as e:
                    print(f"      -> Gagal menghapus {fpath}: {e}")

        print("=========================================")
        print(f" JALANKAN INSTAGRAM FARMING BOT ")
        print(f" Device: {device_pilihan}")
        print(f" Pembagian Target: Beranda ({num_beranda_target} post) | Reels ({'Tak terbatas' if num_reels_target < 0 else f'{num_reels_target} post'})")
        if loop_infinite:
            print(f" Stopper: Buat file '{stopper_device}' atau '{stopper_global}' untuk berhenti.")
        print("=========================================")

        print("[1/4] Menghubungkan ke perangkat Android via ADB...")
        log_step("connect_device", status="complete", device_id=device_pilihan, action="farming")
        d = connect_adb(device_pilihan)
        width, height = d.window_size()
        print(f"Terhubung ke perangkat: {d.device_info.get('brand', 'Unknown')} {d.device_info.get('model', 'Device')}")

        print("[2/4] Membuka kembali Instagram secara bersih (Force Close & Restart)...")
        log_step("open_app", status="complete", device_id=device_pilihan, action="farming")
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

        # Jaring pengaman: Jika berada di dalam sub-halaman (detail post/comment/keyboard terbuka), tekan BACK sampai tab bar terlihat
        try:
            d.keyboard_dismiss()
            time.sleep(0.5)
        except:
            pass

        for back_attempt in range(5):
            main_tabs_exist = (
                d(resourceId="com.instagram.android:id/feed_tab").exists or
                d(resourceId="com.instagram.android:id/profile_tab").exists or
                d(resourceId="com.instagram.android:id/search_tab").exists or
                d(descriptionMatches="(?i).*(Profil|Profile|Beranda|Home|Search|Reels|Search and Explore).*").exists
            )
            if main_tabs_exist:
                break
            print(f"      -> Terdeteksi berada di sub-halaman/postingan. Mengirim BACK ke-{back_attempt+1}...")
            d.press("back")
            time.sleep(2.0)

        # Pastikan posisi di Beranda (Home)
        print("Mengecek dan memastikan berada di halaman Beranda...")
        home_clicked = False
        for rid in ["com.instagram.android:id/feed_tab", "com.instagram.android:id/home_tab"]:
            if d(resourceId=rid).exists:
                d(resourceId=rid).click()
                home_clicked = True
                break
        
        if not home_clicked:
            for desc in ["Beranda", "Home", "Feed"]:
                sel = d(descriptionContains=desc, packageName="com.instagram.android")
                if sel.exists:
                    sel.click()
                    home_clicked = True
                    break
                    
        if not home_clicked:
            # Fallback koordinat tab Beranda (kiri bawah) - disesuaikan ke tinggi 0.95 agar presisi di bar tab
            d.click(int(width * 0.10), int(height * 0.95))
        time.sleep(4.0)
        
        # Sapu bersih pop-up di awal aktivitas agar aman
        print("Membersihkan interupsi pop-up awal agar Beranda bersih...")
        try:
            clear_post_login_popups(d)
        except Exception as pop_err:
            print(f"      -> Gagal menjalankan pembersihan pop-up: {pop_err}")
            
        # Scroll sedikit di awal agar postingan pertama terfokus penuh
        print("Menggulir layar sedikit di awal agar postingan pertama terlihat penuh...")
        d.swipe(0.5, 0.70, 0.5, 0.45, duration=0.20)
        time.sleep(2)
        
        print("[3/4] Mulai proses farming postingan secara acak...")
        log_step("farming_loop", status="on_progress", device_id=device_pilihan, action="farming")

        comments_pool = [
            "Keren banget! 🔥", "Mantap kak! 👍", "Info menarik nih", "Suka banget sama postingan ini", 
            "Wow, amazing!", "Inspiratif sekali kak", "Top banget!", "Super sekali", "Luar biasa! 😮", 
            "Bagus sekali!", "Kreatif banget!", "Menginspirasi 👍", "Keren abis 🔥", "Semangat terus kak!"
        ]

        stats = {
            "like": 0, "comment": 0, "repost": 0, "save": 0, "scroll": 0,
            "reels_like": 0, "reels_comment": 0, "reels_repost": 0, "reels_scroll": 0
        }
        total_beranda = 0
        total_reels = 0

        # === TAHAP 1: FARMING BERANDA ===
        print(f"\n--- [STAGE 1] MEMULAI FARMING BERANDA ({num_beranda_target} POSTINGAN) ---")
        for i in range(1, num_beranda_target + 1):
            if os.path.exists(stopper_device) or os.path.exists(stopper_global):
                print(f"\n[STOP] Terdeteksi file stopper. Menghentikan proses farming secara aman...")
                for fpath in [stopper_device, stopper_global]:
                    if os.path.exists(fpath):
                        try:
                            os.remove(fpath)
                        except:
                            pass
                print_farming_summary(stats, total_beranda, total_reels)
                sys.exit(0)

            total_beranda = i
            print(f"\n--- Postingan Beranda #{i}/{num_beranda_target} ---")
            
            # Safety Check: Pastikan aplikasi Instagram tetap aktif di layar depan (foreground)
            try:
                if d.app_current().get('package') != 'com.instagram.android':
                    print("      -> Terdeteksi di luar Instagram, membuka kembali aplikasi...")
                    d.app_start("com.instagram.android")
                    time.sleep(5.0)
                    clear_any_popup_fast(d)
            except Exception as app_err:
                print(f"      -> Gagal memeriksa status package: {app_err}")
                
            # Deteksi jika postingan ini adalah postingan/rekomendasi Threads
            is_threads = False
            try:
                xml_lower = d.dump_hierarchy().lower()
                threads_keywords = [
                    "threads.net", "buka threads", "open threads", 
                    "suggested for you from threads", "rekomendasi dari threads", 
                    "suggested on threads", "rekomendasi di threads", 
                    "instal threads", "install threads", "view on threads", 
                    "lihat di threads"
                ]
                if any(kw in xml_lower for kw in threads_keywords):
                    is_threads = True
            except Exception:
                pass

            if is_threads:
                print("      [INFO] Terdeteksi postingan/rekomendasi Threads di layar. Melewati...")
                # Lakukan scroll ke postingan berikutnya tanpa melakukan aksi apa pun
                d.swipe(0.5, 0.75, 0.5, 0.25, duration=0.15)
                time.sleep(2.0)
                continue
            
            btn_like = d(resourceIdMatches=".*(?i)(button_like|like_button).*")
            if not btn_like.exists:
                for desc in ["Suka", "Like", "Suka Icon", "Like Icon"]:
                    if d(description=desc).exists:
                        btn_like = d(description=desc)
                        break
            
            scroll_attempts = 0
            while not btn_like.exists and scroll_attempts < 3:
                print("Tombol interaksi tidak terlihat di layar. Menggulir sedikit ke bawah...")
                d.swipe(0.5, 0.70, 0.5, 0.55, duration=0.15)
                time.sleep(1.5)
                scroll_attempts += 1
                btn_like = d(resourceIdMatches=".*(?i)(button_like|like_button).*")
                if not btn_like.exists:
                    for desc in ["Suka", "Like", "Suka Icon", "Like Icon"]:
                        if d(description=desc).exists:
                            btn_like = d(description=desc)
                            break
                            
            coords = find_feed_buttons(d, width)
            aksi = random.choices(
                ["like", "comment", "repost", "save", "scroll"],
                weights=[40, 25, 15, 15, 5],
                k=1
            )[0]

            print(f"Aksi terpilih secara acak: {aksi.upper()}")

            available_actions = []
            chk_like = d(resourceIdMatches=".*(?i)(button_like|like_button).*")
            if not chk_like.exists:
                for desc in ["Suka", "Like", "Suka Icon", "Like Icon"]:
                    if d(description=desc).exists:
                        chk_like = d(description=desc)
                        break
            if chk_like.exists:
                available_actions.append("like")
                
            chk_comment = d(resourceIdMatches=".*(?i)(button_comment|comment_button).*")
            if not chk_comment.exists:
                for desc in ["Komentar", "Comment", "Comment Icon"]:
                    if d(description=desc).exists:
                        chk_comment = d(description=desc)
                        break
            if chk_comment.exists:
                available_actions.append("comment")
                
            chk_repost = d(resourceIdMatches=".*(?i)(button_repost|repost_button).*")
            if not chk_repost.exists:
                for desc in ["Repost", "Posting Ulang", "Posting ulang"]:
                    if d(description=desc).exists:
                        chk_repost = d(description=desc)
                        break
            if chk_repost.exists:
                available_actions.append("repost")
                
            chk_save = d(resourceIdMatches=".*(?i)(save_button|button_save).*")
            if not chk_save.exists:
                for desc in ["Simpan", "Save", "Save Icon", "Simpan Icon"]:
                    if d(description=desc).exists:
                        chk_save = d(description=desc)
                        break
            if chk_save.exists:
                available_actions.append("save")
                
            available_actions.append("scroll")
            
            print(f"Tombol interaksi yang terdeteksi aktif di layar: {available_actions}")
            
            if aksi not in available_actions:
                print(f"Aksi '{aksi.upper()}' tidak tersedia karena tombolnya tidak ditemukan di layar.")
                if aksi == "comment":
                    aksi = "like" if "like" in available_actions else "save"
                elif aksi == "like":
                    aksi = "comment" if "comment" in available_actions else "save"
                elif aksi == "repost":
                    aksi = "like" if "like" in available_actions else "save"
                elif aksi == "save":
                    aksi = "like" if "like" in available_actions else "comment"
                
                if aksi not in available_actions:
                    aksi = available_actions[0]
                
                print(f"Beralih ke aksi fallback: {aksi.upper()}")

            if aksi == "like":
                print("Mencoba melakukan LIKE...")
                like_success = False
                btn_like = d(resourceIdMatches=".*(?i)(button_like|like_button).*")
                if btn_like.exists:
                    try:
                        desc_like = btn_like.info.get('contentDescription', '') or ''
                        if "Liked" in desc_like or "Suka" in desc_like and "Batal" in desc_like:
                            print("Postingan sudah disukai sebelumnya. Melewati.")
                            like_success = True
                    except Exception:
                        pass
                
                if not like_success:
                    like_success = click_element_robust(d, [
                        d(resourceIdMatches=".*(?i)(button_like|like_button).*"),
                        d(descriptionMatches="(?i)(like|suka).*")
                    ])
                
                if not like_success:
                    d.click(coords["like"][0], coords["like"][1])
                    like_success = True
                
                if like_success:
                    print("[SUKSES] Postingan disukai (LIKE).")
                    stats["like"] += 1

            elif aksi == "comment":
                print("Mencoba melakukan COMMENT...")
                comment_clicked = click_element_robust(d, [
                    d(resourceIdMatches=".*(?i)(button_comment|comment_button).*"),
                    d(descriptionMatches="(?i)(comment|komentar).*")
                ])
                
                if not comment_clicked:
                    d.click(coords["comment"][0], coords["comment"][1])
                    
                time.sleep(3)
                
                # Cek jika kolom komentar dinonaktifkan atau dibatasi oleh pembuat postingan
                comments_limited = (
                    d(textMatches="(?i).*(limited|dibatasi|disabled|dinonaktifkan).*").exists or
                    d(descriptionMatches="(?i).*(limited|dibatasi|disabled|dinonaktifkan).*").exists
                )
                # Cek apakah ada input field di layar
                has_input_box = (
                    d(className="android.widget.EditText").exists or
                    d(resourceId="com.instagram.android:id/layout_comment_thread_edittext").exists or
                    d(resourceId="com.instagram.android:id/comment_composer_text").exists
                )
                
                if comments_limited or not has_input_box:
                    print("      [Farming] Kolom komentar dibatasi, dinonaktifkan, atau tidak ditemukan. Menutup laci komentar...")
                    try:
                        d.keyboard_dismiss()
                        time.sleep(0.5)
                    except:
                        pass
                    d.press("back")
                    time.sleep(2.0)
                    stats["scroll"] += 1
                    print("Menggulir layar ke postingan selanjutnya...")
                    d.swipe(0.5, 0.75, 0.5, 0.25, duration=0.15)
                    time.sleep(1.5)
                    continue

                comment_text = random.choice(comments_pool)
                kolom_teks = d(className="android.widget.EditText")
                if kolom_teks.exists:
                    kolom_teks.click()
                    time.sleep(1.0)
                    kolom_teks.set_text(comment_text)
                else:
                    d.click(width // 2, int(height * 0.92))
                    time.sleep(1.5)
                    d.send_keys(comment_text)
                time.sleep(2)
                
                btn_send = d(resourceId="com.instagram.android:id/layout_comment_thread_post_button_icon")
                if btn_send.exists:
                    btn_send.click()
                    print(f"[SUKSES] Memberikan komentar: '{comment_text}'")
                    stats["comment"] += 1
                else:
                    sent_via_bounds = False
                    kolom_teks = d(className="android.widget.EditText")
                    if kolom_teks.exists:
                        try:
                            bounds = kolom_teks.info.get('bounds')
                            if bounds:
                                x_send = bounds['right'] + (width - bounds['right']) / 2
                                y_send = (bounds['top'] + bounds['bottom']) / 2
                                d.click(int(x_send), int(y_send))
                                sent_via_bounds = True
                        except:
                            pass
                    if not sent_via_bounds:
                        d.click(int(width * 0.89), int(height * 0.92))
                    print(f"[SUKSES] Memberikan komentar (coords): '{comment_text}'")
                    stats["comment"] += 1
                # Gunakan multi-strategi penutupan laci komentar yang aman
                time.sleep(3.5)
                print("      -> Menutup thread komentar...")
                try:
                    d.keyboard_dismiss()
                    time.sleep(1.0)
                except:
                    pass
                    
                comment_closed = False
                for back_attempt in range(4):
                    is_comment_thread = is_currently_comment_thread(d)
                    if not is_comment_thread:
                        comment_closed = True
                        break
                        
                    # Strategi 1: Clicks by ID
                    for rid in [
                        "com.instagram.android:id/action_bar_button_back",
                        "com.instagram.android:id/comment_composer_back_button",
                        "com.instagram.android:id/comments_back_button",
                        "com.instagram.android:id/back_button"
                    ]:
                        btn = d(resourceId=rid)
                        if btn.exists:
                            try:
                                btn.click()
                                time.sleep(1.5)
                                break
                            except:
                                pass
                                
                    # Strategi 2: Clicks by text/description
                    if is_currently_comment_thread(d):
                        for desc in ["Back", "Kembali", "Close", "Tutup"]:
                            btn = d(descriptionContains=desc)
                            if not btn.exists:
                                btn = d(textContains=desc)
                            if btn.exists:
                                try:
                                    btn.click()
                                    time.sleep(1.5)
                                    break
                                except:
                                    pass
                                    
                    # Strategi 3: BACK key
                    if is_currently_comment_thread(d):
                        d.press("back")
                        time.sleep(1.0)
                        
                    # Strategi 4: Swipe down
                    if is_currently_comment_thread(d):
                        d.swipe(0.5, 0.35, 0.5, 0.90, duration=0.25)
                        time.sleep(1.5)

            elif aksi == "repost":
                print("Mencoba melakukan REPOST (Posting Ulang)...")
                repost_clicked = click_element_robust(d, [
                    d(resourceIdMatches=".*(?i)(button_repost|repost_button).*"),
                    d(descriptionMatches="(?i)(repost|posting ulang).*")
                ])
                if not repost_clicked:
                    d.click(coords["repost"][0], coords["repost"][1])
                    repost_clicked = True
                if repost_clicked:
                    time.sleep(2.5)
                    confirm_repost = d(textMatches="(?i).*(repost|posting ulang).*")
                    if not confirm_repost.exists:
                        confirm_repost = d(descriptionMatches="(?i).*(repost|posting ulang).*")
                    if confirm_repost.exists:
                        confirm_repost.click()
                        print("[SUKSES] Konfirmasi repost berhasil diklik.")
                    else:
                        print("[SUKSES] Repost berhasil dikirim.")
                    stats["repost"] += 1
                    time.sleep(3)
                else:
                    print("Tombol Repost tidak terdeteksi. Mencoba lewat menu Share...")
                    share_clicked = click_element_robust(d, [
                        d(resourceIdMatches=".*(?i)(button_share|share_button|send_button|button_send).*"),
                        d(descriptionMatches="(?i)(share|kirim).*")
                    ])
                    if not share_clicked:
                        d.click(coords["share"][0], coords["share"][1])
                        share_clicked = True
                    if share_clicked:
                        time.sleep(3.5)
                        btn_repost_share = d(textMatches="(?i).*(repost|posting ulang).*")
                        if not btn_repost_share.exists:
                            btn_repost_share = d(descriptionMatches="(?i).*(repost|posting ulang).*")
                        if btn_repost_share.exists:
                            btn_repost_share.click()
                            print("[SUKSES] Repost berhasil dari menu Share.")
                            stats["repost"] += 1
                            time.sleep(3)
                        else:
                            print("Opsi repost tidak ditemukan di menu Share. Menutup menu...")
                            d.press("back")
                            time.sleep(2)
                            stats["scroll"] += 1
                    else:
                        stats["scroll"] += 1

            elif aksi == "save":
                print("Mencoba melakukan SAVE (Simpan)...")
                save_clicked = click_element_robust(d, [
                    d(resourceIdMatches=".*(?i)(save_button|button_save).*"),
                    d(descriptionMatches="(?i)(save|simpan).*")
                ])
                if not save_clicked:
                    d.click(coords["save"][0], coords["save"][1])
                    save_clicked = True
                if save_clicked:
                    print("[SUKSES] Postingan disimpan (SAVE).")
                    stats["save"] += 1
                    time.sleep(1.5)
                    d.press("back")
                    time.sleep(1.0)
                else:
                    print("Tombol simpan tidak ditemukan. Melewati.")
                    stats["scroll"] += 1
            else:
                print("[SUKSES] Membaca postingan (SCROLL).")
                stats["scroll"] += 1

            time.sleep(random.uniform(1.0, 3.0))
            # Sapu pop-up jika ada interupsi di tengah jalan (seperti pop-up Threads)
            clear_any_popup_fast(d)
            print("Menggulir layar ke postingan selanjutnya...")
            d.swipe(0.5, 0.75, 0.5, 0.25, duration=0.15)
            time.sleep(1.5) 

        # === TAHAP 2: BERGESER KE HALAMAN REELS ===
        print("\n--- [STAGE 2] TRANSISI: BERPINDAH KE HALAMAN REELS ---")
        reels_clicked = False
        for rid in ["com.instagram.android:id/reels_tab", "com.instagram.android:id/clips_tab", "com.instagram.android:id/tab_reels"]:
            btn = d(resourceId=rid)
            if btn.exists:
                print(f"      -> Mengklik Reels tab via ID: '{rid}'")
                btn.click()
                reels_clicked = True
                break
        if not reels_clicked:
            for desc in ["Reels", "Clips", "Video", "Klip", "Tonton Klip"]:
                btn = d(descriptionContains=desc)
                if btn.exists:
                    print(f"      -> Mengklik Reels tab via description: '{desc}'")
                    btn.click()
                    reels_clicked = True
                    break
        if not reels_clicked:
            print("      -> Tombol Reels tidak terdeteksi, klik koordinat fallback (0.7, 0.93)...")
            d.click(int(width * 0.7), int(height * 0.93))
            reels_clicked = True
        time.sleep(5.0)

        # === TAHAP 3: FARMING REELS ===
        if num_reels_target != 0:
            print(f"\n--- [STAGE 3] MEMULAI FARMING REELS ({'TAK TERBATAS' if num_reels_target < 0 else f'{num_reels_target} POSTINGAN'}) ---")
            reels_index = 1
            while True:
                if os.path.exists(stopper_device) or os.path.exists(stopper_global):
                    print(f"\n[STOP] Terdeteksi file stopper. Menghentikan proses farming Reels secara aman...")
                    for fpath in [stopper_device, stopper_global]:
                        if os.path.exists(fpath):
                            try:
                                os.remove(fpath)
                            except:
                                pass
                    break
                total_reels = reels_index
                print(f"\n--- Reel #{reels_index}{f'/{num_reels_target}' if num_reels_target > 0 else ''} ---")
                
                # Safety Check: Pastikan aplikasi Instagram tetap aktif di layar depan (foreground)
                try:
                    if d.app_current().get('package') != 'com.instagram.android':
                        print("      -> Terdeteksi di luar Instagram, membuka kembali aplikasi...")
                        d.app_start("com.instagram.android")
                        time.sleep(5.0)
                        clear_any_popup_fast(d)
                except Exception as app_err:
                    print(f"      -> Gagal memeriksa status package: {app_err}")
                # Cek apakah ada ikon interaksi Reels di layar
                btn_like_check = d(resourceIdMatches=".*(?i)(like_button|button_like).*")
                btn_comment_check = d(resourceIdMatches=".*(?i)(comment_button|button_comment).*")
                btn_share_check = d(resourceIdMatches=".*(?i)(share_button|button_share|send_button|button_send).*")
                repost_exists_check = False
                for selector in [
                    d(description="Repost"),
                    d(description="Posting ulang"),
                    d(description="Posting Ulang"),
                    d(descriptionContains="Repost"),
                    d(descriptionContains="Posting ulang"),
                    d(resourceIdMatches=".*(?i)repost.*")
                ]:
                    if selector.exists:
                        repost_exists_check = True
                        break
                        
                has_any_interaction_icon = btn_like_check.exists or btn_comment_check.exists or btn_share_check.exists or repost_exists_check
                
                if not has_any_interaction_icon:
                    for desc in ["Like", "Suka", "Comment", "Komentar", "Share", "Kirim", "Repost", "Posting ulang"]:
                        if d(descriptionMatches=f"(?i).*{desc}.*").exists:
                            has_any_interaction_icon = True
                            break
                            
                aksi = random.choices(["like", "comment", "repost", "scroll"], weights=[35, 20, 15, 30], k=1)[0]
                
                if not has_any_interaction_icon:
                    print("   [WARNING] Layar tidak menampilkan ikon interaksi Reels (kemungkinan rekomendasi teman). Dipaksa skip/scroll...")
                    aksi = "scroll"
                    
                print(f"Aksi Reels terpilih: {aksi.upper()}")
                if aksi == "like":
                    print("   -> Mencoba LIKE Reel...")
                    like_success = False
                    btn_like = d(resourceIdMatches=".*(?i)(like_button|button_like).*")
                    if not btn_like.exists:
                        for desc in ["Like", "Suka", "Like Button", "Tombol Suka"]:
                            if d(descriptionMatches=f"(?i)^{desc}$").exists:
                                btn_like = d(descriptionMatches=f"(?i)^{desc}$")
                                break
                    if btn_like.exists:
                        try:
                            desc = btn_like.info.get('contentDescription', '') or ''
                            if "Liked" in desc or "disukai" in desc.lower():
                                print("      -> Reel sudah disukai sebelumnya. Melewati.")
                                like_success = True
                        except:
                            pass
                        if not like_success:
                            try:
                                btn_like.click()
                                like_success = True
                            except:
                                pass
                    else:
                        print("      -> Tombol Like tidak terdeteksi via ID, menggunakan koordinat fallback (0.9, 0.55)...")
                        d.click(int(width * 0.9), int(height * 0.55))
                        like_success = True
                    if like_success:
                        print("   [SUKSES] Reel disukai (LIKE).")
                        stats["reels_like"] += 1
                elif aksi == "comment":
                    print("   -> Mencoba COMMENT Reel...")
                    btn_comment = d(resourceIdMatches=".*(?i)(comment_button|button_comment).*")
                    if not btn_comment.exists:
                        for desc in ["Comment", "Komentar", "Comment Button", "Tombol Komentar"]:
                            if d(descriptionMatches=f"(?i)^{desc}$").exists:
                                btn_comment = d(descriptionMatches=f"(?i)^{desc}$")
                                break
                    comment_clicked = False
                    if btn_comment.exists:
                        try:
                            btn_comment.click()
                            comment_clicked = True
                        except:
                            pass
                    else:
                        print("      -> Tombol Comment tidak terdeteksi via ID, menggunakan koordinat fallback (0.9, 0.65)...")
                        d.click(int(width * 0.9), int(height * 0.65))
                        comment_clicked = True
                    if comment_clicked:
                        time.sleep(3.0)
                        
                        # Cek jika kolom komentar dinonaktifkan atau dibatasi oleh pembuat postingan
                        comments_limited = (
                            d(textMatches="(?i).*(limited|dibatasi|disabled|dinonaktifkan).*").exists or
                            d(descriptionMatches="(?i).*(limited|dibatasi|disabled|dinonaktifkan).*").exists
                        )
                        # Cek apakah ada input field di layar
                        has_input_box = (
                            d(className="android.widget.EditText").exists or
                            d(resourceId="com.instagram.android:id/layout_comment_thread_edittext").exists or
                            d(resourceId="com.instagram.android:id/comment_composer_text").exists
                        )
                        
                        if comments_limited or not has_input_box:
                            print("      [Farming Reels] Kolom komentar dibatasi, dinonaktifkan, atau tidak ditemukan. Menutup laci komentar...")
                            try:
                                d.keyboard_dismiss()
                                time.sleep(0.5)
                            except:
                                pass
                            d.press("back")
                            time.sleep(2.0)
                            stats["reels_scroll"] += 1
                            print("Menggulir ke video Reel selanjutnya...")
                            d.swipe(0.5, 0.85, 0.5, 0.15, duration=0.15)
                            time.sleep(2.5)
                            continue

                        comment_text = random.choice(comments_pool)
                        kolom_teks = d(className="android.widget.EditText")
                        if kolom_teks.exists:
                            kolom_teks.click()
                            time.sleep(1.0)
                            kolom_teks.set_text(comment_text)
                        else:
                            d.click(width // 2, int(height * 0.92))
                            time.sleep(1.5)
                            d.send_keys(comment_text)
                        time.sleep(2.0)
                        btn_send = d(resourceId="com.instagram.android:id/layout_comment_thread_post_button_icon")
                        if btn_send.exists:
                            btn_send.click()
                            print(f"   [SUKSES] Mengirim komentar Reel: '{comment_text}'")
                            stats["reels_comment"] += 1
                        else:
                            sent_via_bounds = False
                            kolom_teks = d(className="android.widget.EditText")
                            if kolom_teks.exists:
                                try:
                                    bounds = kolom_teks.info.get('bounds')
                                    if bounds:
                                        x_send = bounds['right'] + (width - bounds['right']) / 2
                                        y_send = (bounds['top'] + bounds['bottom']) / 2
                                        d.click(int(x_send), int(y_send))
                                        sent_via_bounds = True
                                except:
                                    pass
                            if not sent_via_bounds:
                                d.click(int(width * 0.89), int(height * 0.92))
                            print(f"   [SUKSES] Mengirim komentar Reel (coords): '{comment_text}'")
                            stats["reels_comment"] += 1
                        # Gunakan multi-strategi penutupan laci komentar yang aman
                        time.sleep(3.5)
                        print("      -> Menutup thread komentar Reels...")
                        try:
                            d.keyboard_dismiss()
                            time.sleep(1.0)
                        except:
                            pass
                            
                        comment_closed = False
                        for back_attempt in range(4):
                            is_comment_thread = is_currently_comment_thread(d)
                            if not is_comment_thread:
                                comment_closed = True
                                break
                                
                            # Strategi 1: Clicks by ID
                            for rid in [
                                "com.instagram.android:id/action_bar_button_back",
                                "com.instagram.android:id/comment_composer_back_button",
                                "com.instagram.android:id/comments_back_button",
                                "com.instagram.android:id/back_button"
                            ]:
                                btn = d(resourceId=rid)
                                if btn.exists:
                                    try:
                                        btn.click()
                                        time.sleep(1.5)
                                        break
                                    except:
                                        pass
                                        
                            # Strategi 2: Clicks by text/description
                            if is_currently_comment_thread(d):
                                for desc in ["Back", "Kembali", "Close", "Tutup"]:
                                    btn = d(descriptionContains=desc)
                                    if not btn.exists:
                                        btn = d(textContains=desc)
                                    if btn.exists:
                                        try:
                                            btn.click()
                                            time.sleep(1.5)
                                            break
                                        except:
                                            pass
                                            
                            # Strategi 3: BACK key
                            if is_currently_comment_thread(d):
                                d.press("back")
                                time.sleep(1.0)
                                
                            # Strategi 4: Swipe down
                            if is_currently_comment_thread(d):
                                d.swipe(0.5, 0.35, 0.5, 0.90, duration=0.25)
                                time.sleep(1.5)
                elif aksi == "repost":
                    print("   -> Mencoba REPOST Reel langsung...")
                    repost_clicked = False
                    for selector in [
                        d(description="Repost"),
                        d(description="Posting ulang"),
                        d(description="Posting Ulang"),
                        d(descriptionContains="Repost"),
                        d(descriptionContains="Posting ulang"),
                        d(resourceIdMatches=".*(?i)repost.*")
                    ]:
                        if selector.exists:
                            try:
                                selector.click()
                                print("      -> Ikon Repost langsung diklik.")
                                repost_clicked = True
                                time.sleep(3.0)
                                break
                            except:
                                pass
                                
                    if repost_clicked:
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
                                
                        # Cek jika ada popup sukses dengan pilihan "Close" / "Tutup" / "Dismiss"
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
                                    
                        print("   [SUKSES] Repost Reel berhasil!")
                        stats["reels_repost"] += 1
                    else:
                        print("      -> Ikon Repost langsung tidak ditemukan. Menonton Reel saja...")
                        stats["reels_scroll"] += 1
                else:
                    print("   -> Menonton Reel saja...")
                    stats["reels_scroll"] += 1
                    
                # Cek limit Reels
                if num_reels_target > 0 and reels_index >= num_reels_target:
                    print(f" [SUCCESS] Target limit Reels tercapai ({reels_index}/{num_reels_target})")
                    break
                    
                time.sleep(random.uniform(3.0, 6.0))
                print("Menggulir ke Reel berikutnya (Swipe Up)...")
                d.swipe(0.5, 0.80, 0.5, 0.20, duration=0.15)
                time.sleep(2.0)
                reels_index += 1
            
        # Alur Akhir: Kembali ke Beranda Instagram (dengan forced stop + restart agar bersih)
        print("\n[+] OPTIMALISASI: Kembali ke Beranda utama Instagram dan menyegarkan (refresh) feed...")
        try:
            print("      -> Menghentikan paksa (kill) aplikasi Instagram...")
            d.app_stop("com.instagram.android")
            time.sleep(2.0)
            
            print("      -> Membuka kembali aplikasi Instagram...")
            d.app_start("com.instagram.android")
            time.sleep(5.0)
            clear_any_popup_fast(d)
            
            # Lakukan klik tombol Beranda sebanyak 2 kali untuk berpindah dan me-refresh feed
            for attempt in range(2):
                print(f"      -> Mengklik tombol Beranda (klik ke-{attempt+1})...")
                home_clicked = False
                
                # 1. Cari berdasarkan Resource ID
                for rid in ["com.instagram.android:id/feed_tab", "com.instagram.android:id/home_tab"]:
                    if d(resourceId=rid).exists:
                        d(resourceId=rid).click()
                        home_clicked = True
                        break
                
                # 2. Cari berdasarkan Deskripsi
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
                
                # Jeda waktu: klik pertama butuh 2.0 detik (pindah tab), klik kedua butuh 4.0 detik (refresh)
                time.sleep(2.0 if attempt == 0 else 4.0)
                
            print("      [SUKSES] Halaman Beranda berhasil di-refresh via tombol Beranda.")
        except Exception as opt_err:
            print(f"      -> Gagal melakukan restart/refresh Beranda: {opt_err}")
            
        print_farming_summary(stats, total_beranda, total_reels)
        log_complete(log_id, message=f"Farming completed. Liked {stats.get('likes', 0)} posts, commented {stats.get('comments', 0)} times.")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n[EXIT] Eksekusi dihentikan oleh user (KeyboardInterrupt).")
        try:
            print_farming_summary(stats, total_beranda, total_reels)
        except:
            pass
        log_complete(log_id, message="Farming manually stopped (KeyboardInterrupt)")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR EXCEPTION] Terjadi kesalahan: {e}")
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
    device_id = sys.argv[1] if len(sys.argv) > 1 else "all"
    posts = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    if len(sys.argv) <= 1 and sys.stdin.isatty():
        try:
            print("\n--- MENJALANKAN BOT FARMING SECARA INTERAKTIF ---")
            ans_dev = input("Masukkan device ID (kosongkan/tekan Enter untuk 'all'): ").strip()
            if ans_dev:
                device_id = ans_dev
            ans_posts = input("Masukkan jumlah post yang di-farm (default 10): ").strip()
            if ans_posts:
                posts = int(ans_posts)
        except (EOFError, KeyboardInterrupt, ValueError):
            pass
            
    devices = resolve_devices(device_id)
    if len(devices) > 1:
        run_parallel_threads(run_farming_bot, devices, total_posts=posts)
    else:
        run_farming_bot(device_pilihan=devices[0], total_posts=posts)
