import sys
import uiautomator2 as u2
import time
import random
import re
import os
from ig_helpers import connect_adb, open_instagram

# Import popup cleaner if available
try:
    from bot_instagram_clear_popups import clear_any_popup_fast, check_and_clear_daily_limit
except Exception as e:
    def clear_any_popup_fast(d):
        return False
    def check_and_clear_daily_limit(d):
        return False
# Import account switcher
try:
    from switch_akun_ig import switch_instagram_account
except ImportError:
    def switch_instagram_account(target_username, device_pilihan="all"): return False

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

# Import activity logger if available
try:
    from activity_logger import log_activity, log_complete, log_error, log_step
except Exception:
    def log_activity(*a, **kw): return ""
    def log_complete(*a, **kw): return False
    def log_error(*a, **kw): return False
    def log_step(*a, **kw): return False

# ========================================================
# KAMUS KATA & KOLEKSI KOMENTAR (Kecerdasan Buatan Bryant)
# ========================================================
KATA_BAGUS = ["bagus", "cantik", "indah", "sukses", "keren", "mantap", "hebat", "menarik", "cakep", "gokil", "top", "wow", "estetik", "seru", "terbaik", "bahagia", "semangat"]
KATA_BURUK = ["jelek", "buruk", "sedih", "payah", "gagal", "sampah", "parah", "capek", "lelah", "pusing", "susah", "sulit", "hancur", "kacau", "benci", "kecewa", "kesal"]

KOMENTAR_BAGUS  = ["Keren banget postingannya! 🔥", "Mantap jiwa, sukses terus! 🙌", "Top markotop! ", "Gokil abis ini mah! 🔥", "Cakep pol! 👏"]
KOMENTAR_BURUK  = ["Semangat kak, pasti ada hikmahnya 💪", "Gapapa bang, besok lebih baik lagi", "Cobaan pasti berlalu, stay strong 🙏", "Semoga lekas membaik"]
KOMENTAR_NETRAL = ["Nice posting! 👍", "Menarik nih!", "Gas terus! 🔥", "Salam kenal kak!", "Kereen!"]

def klasifikasi_deskripsi(teks):
    teks_lower = teks.lower()
    skor = 0
    for kata in KATA_BAGUS:
        if kata in teks_lower: skor += 1
    for kata in KATA_BURUK:
        if kata in teks_lower: skor -= 1
    return skor

def generate_komentar_otomatis(teks_deskripsi, komentar_custom=""):
    if komentar_custom and komentar_custom.strip() != "":
        if komentar_custom.endswith(".txt") and os.path.exists(komentar_custom):
            try:
                with open(komentar_custom, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    print(f"Menggunakan seluruh isi komentar dari file txt '{komentar_custom}'")
                    return content
                else:
                    print(f"File txt '{komentar_custom}' kosong. Menggunakan komentar otomatis.")
            except Exception as e:
                print(f"Gagal membaca file komentar txt '{komentar_custom}': {e}")
        else:
            print(f"Menggunakan komentar manual dari web: '{komentar_custom}'")
            return komentar_custom
    if not teks_deskripsi:
        return random.choice(KOMENTAR_NETRAL)
    skor = klasifikasi_deskripsi(teks_deskripsi)
    if skor > 0:
        return random.choice(KOMENTAR_BAGUS)
    elif skor < 0:
        return random.choice(KOMENTAR_BURUK)
    else:
        return random.choice(KOMENTAR_NETRAL)

# ========================================================
# HELPER: CEK APAKAH SEDANG DI THREAD KOMENTAR
# ========================================================
def is_currently_comment_thread(d):
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
        or d(resourceId="com.instagram.android:id/row_comment_like_button").exists \
        or d(resourceId="com.instagram.android:id/comment_like_button").exists \
        or d(resourceId="com.instagram.android:id/comment_reply_button").exists \
        or d(resourceId="com.instagram.android:id/comment_composer_gif_button").exists \
        or d(textMatches="(?i)^(Comments|Komentar|Replies|Balasan)$").exists

# ========================================================
# HELPER: SWAP AKUN
# ========================================================
def _swap_akun(d, my_account, width, height):
    if not my_account or my_account.strip() == "":
        return True
    print(f"[PRE-RUN] Mengganti akun ke: '{my_account}'...")
    x_profile = int(width * 0.904)
    y_profile = int(height * 0.914)
    d.click(x_profile, y_profile)
    time.sleep(3.0)
    clear_any_popup_fast(d)
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
    clean_acc = my_account.replace("@", "").strip()
    btn_acc = d(text=clean_acc)
    if not btn_acc.exists:
        btn_acc = d(textContains=clean_acc)
    if btn_acc.exists:
        print(f"      -> Akun '{clean_acc}' ditemukan. Mengklik untuk beralih...")
        btn_acc.click()
        time.sleep(6.0)
        clear_any_popup_fast(d)
        print(f"[PRE-RUN] Sukses beralih ke akun '{clean_acc}'.")
        return True
    else:
        print(f"[PRE-RUN] Akun '{clean_acc}' tidak ditemukan di menu ganti akun!")
        d.press("back")
        time.sleep(1.5)
        return False

# ========================================================
# HELPER: KIRIM KOMENTAR KE KOLOM INPUT
# ========================================================
def _kirim_komentar(d, isi_komentar, width, height, use_send_keys=False):
    kolom_teks = d(resourceId="com.instagram.android:id/layout_comment_thread_edittext")
    if not kolom_teks.exists:
        kolom_teks = d(className="android.widget.EditText")
    if kolom_teks.exists:
        kolom_teks.click()
        time.sleep(1)
        try:
            kolom_teks.clear_text()
            time.sleep(0.5)
        except Exception as e:
            print(f"      -> Gagal membersihkan kolom komentar: {e}")
        if use_send_keys:
            for _ in range(50):
                d.keyevent("67")
            time.sleep(0.3)
            d.send_keys(isi_komentar)
        else:
            kolom_teks.set_text(isi_komentar)
        return True
    else:
        d.click(width // 2, int(height * 0.92))
        time.sleep(1)
        d.send_keys(isi_komentar)
        return True

def _tekan_kirim(d, kolom_teks, width, height):
    # 0. Jaring pengaman khusus FastInputIME (AdbKeyboard) atau tombol Send di keyboard
    for send_lbl in ["Send", "Kirim", "Post", "Posting"]:
        sel_send = d(text=send_lbl)
        if sel_send.exists:
            for idx in range(sel_send.count):
                try:
                    b = sel_send[idx].info.get("bounds")
                    if b and b["top"] > height * 0.8:
                        sel_send[idx].click()
                        print(f"      -> Berhasil klik tombol '{send_lbl}' pada keyboard/laci bawah.")
                        time.sleep(1.5)
                        try: d.keyboard_dismiss()
                        except: pass
                        return
                except:
                    pass

    btn_kirim = None
    # 1. Cari berdasarkan Resource ID
    for rid in [
        "com.instagram.android:id/layout_comment_thread_post_button_icon",
        "com.instagram.android:id/layout_comment_thread_post_button_click_area",
        "com.instagram.android:id/layout_comment_thread_post_button",
        "com.instagram.android:id/comment_post_button",
        "com.instagram.android:id/comment_composer_send_button",
        "com.instagram.android:id/send_button"
    ]:
        if d(resourceId=rid).exists:
            btn_kirim = d(resourceId=rid)
            break
            
    # 2. Cari berdasarkan deskripsi / teks
    if not btn_kirim:
        for match_sel in [
            d(descriptionMatches="(?i)(Kirim|Post|Posting|Send|Send Icon|Kirim Icon)"), 
            d(textMatches="(?i)(Kirim|Post|Posting|Send)")
        ]:
            if match_sel.exists:
                btn_kirim = match_sel
                break
                
    if btn_kirim:
        btn_kirim.click()
        return

    # 3. Cari kolom edit text yang aktif untuk menghitung koordinat dinamis
    kolom_aktif = d(focused=True)
    if not kolom_aktif.exists:
        kolom_aktif = d(className="android.widget.EditText")
    if not kolom_aktif.exists:
        kolom_aktif = d(resourceIdMatches=".*(?i)(edittext|comment_thread_edittext|edit_text|input).*")
    if not kolom_aktif.exists:
        kolom_aktif = kolom_teks
        
    if kolom_aktif and kolom_aktif.exists:
        bounds = kolom_aktif.info.get("bounds")
        if bounds:
            x_send = int(bounds["right"] + (width - bounds["right"]) / 2)
            y_send = int((bounds["top"] + bounds["bottom"]) / 2)
            print(f"      -> Mengklik tombol kirim dinamis: X={x_send}, Y={y_send}")
            d.click(x_send, y_send)
            return

    # 4. Fallback koordinat jika uiautomator2 tidak mendeteksi elemen
    keyboard_active = False
    try:
        res = d.shell("dumpsys input_method").output
        if "mInputShown=true" in res:
            keyboard_active = True
    except:
        pass

    if keyboard_active:
        y_fallback = int(height * 0.58)
        print(f"      -> Keyboard terdeteksi aktif. Mengklik tombol kirim via fallback atas: X={int(width * 0.89)}, Y={y_fallback}")
    else:
        y_fallback = int(height * 0.95)
        print(f"      -> Keyboard tidak aktif. Mengklik tombol kirim via fallback bawah: X={int(width * 0.89)}, Y={y_fallback}")
        
    d.click(int(width * 0.89), y_fallback)

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


# ========================================================
# FUNGSI 1: COMMENT TARGET (komentar ke profil/post spesifik)
# ========================================================
def comment_target(target_user, komentar_custom="", device_pilihan="all", my_account=""):
    log_id = log_activity(
        action="comment_target", username=target_user,
        message=komentar_custom or "(otomatis)", status="on_progress",
        mode="manual", device_id=device_pilihan,
        extra={"target": target_user, "my_account": my_account}
    )
    try:
        print("=========================================")
        print(f" JALANKAN BOT COMMENT TARGET: @{target_user}")
        if my_account:
            print(f" Menggunakan Akun Saya: {my_account}")
        print("=========================================")

        d = connect_adb(device_pilihan, action="comment", step_label="[1] Menghubungkan ke perangkat Android...")
        width, height = d.window_size()

        open_instagram(d, device_pilihan, action="comment", delay=6, step_label="[2] Membuka aplikasi Instagram...")
        clear_any_popup_fast(d)

        # === PROSES SWAP AKUN DI AWAL (JIKA PARAMETER DIBERIKAN) ===
        if my_account and my_account.strip() != "":
            print(f"[PRE-RUN] Mengganti akun ke: '{my_account}'...")
            success = switch_instagram_account(my_account, device_pilihan)
            if not success:
                print("akun tidak ditemukan")
                print("=========================================\n")
                log_error(log_id, f"Akun '{my_account}' tidak ditemukan atau gagal beralih.")
                return

        is_direct_url = target_user.startswith("http://") or target_user.startswith("https://") or "instagram.com" in target_user

        if is_direct_url:
            print(f"[3] Membuka URL postingan secara langsung menggunakan Intent...")
            log_step("open_url", status="complete", device_id=device_pilihan, action="comment")
            d.shell(f"am start -a android.intent.action.VIEW -d \"{target_user}\" com.instagram.android")
            time.sleep(6)
            clear_any_popup_fast(d)
        else:
            print(f"[3] Mencari profil target: @{target_user}...")
            log_step("search_target", status="complete", device_id=device_pilihan, action="comment")
            icon_search_bawah = d(resourceId="com.instagram.android:id/search_tab")
            if icon_search_bawah.exists:
                print("      -> Mengeklik ikon Search bawah via Resource ID resmi...")
                icon_search_bawah.click()
            else:
                if d(descriptionContains="Cari").exists:
                    d(descriptionContains="Cari").click()
                elif d(descriptionContains="Search").exists:
                    d(descriptionContains="Search").click()
                else:
                    d.click(int(width * 0.69), int(height * 0.918))
            time.sleep(4)

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
            time.sleep(2)

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

            print(" [4] Menekan tombol Enter pada keyboard...")
            d.press("enter")
            time.sleep(4)

            print(" [5] Membuka profil teratas dari hasil pencarian...")
            akun_target_text = d(text=target_user, className="android.widget.TextView")
            akun_target_contains = d(textContains=target_user, className="android.widget.TextView")
            user_container_1 = d(resourceId="com.instagram.android:id/row_search_user_info_container")
            user_container_2 = d(resourceId="com.instagram.android:id/row_search_user_container")

            if akun_target_text.exists:
                akun_target_text.click()
            elif akun_target_contains.exists:
                akun_target_contains.click()
            elif user_container_1.exists:
                user_container_1.click()
            elif user_container_2.exists:
                user_container_2.click()
            else:
                d.click(int(width * 0.4), int(height * 0.24))
            time.sleep(5)

            print(" [6] Membuka postingan teratas milik target...")
            post_clicked = False
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
                d.click(int(width * 0.168), int(height * 0.55))
                time.sleep(2)
                d.click(int(width * 0.168), int(height * 0.741))
                post_clicked = True
            time.sleep(4)

            # Verifikasi apakah halaman detail postingan berhasil dibuka
            print("      -> Memverifikasi apakah halaman detail postingan berhasil dibuka...")
            for check_open in range(3):
                is_profile = d(resourceId="com.instagram.android:id/row_profile_header").exists \
                    or d(text="Postingan").exists \
                    or d(text="Posts").exists
                
                has_post_indicators = d(resourceIdMatches=".*(?i)(button_like|like_button|button_comment|comment_button|row_feed_button).*").exists
                
                if not is_profile and has_post_indicators:
                    print("      -> Sukses masuk ke halaman detail postingan!")
                    break
                else:
                    print(f"      -> Percobaan {check_open + 1}: Halaman detail belum terbuka. Mengklik ulang postingan pertama...")
                    d.click(int(width * 0.168), int(height * 0.55))
                    time.sleep(3.5)

        caption_terdeteksi = ""
        selector_caption = d(resourceId="com.instagram.android:id/row_feed_textview")
        if selector_caption.exists:
            caption_terdeteksi = selector_caption.get_text()
            print(f" Caption terdeteksi: '{caption_terdeteksi[:50]}...'")

        isi_komentar = generate_komentar_otomatis(caption_terdeteksi, komentar_custom)

        print("[7] Mengeklik ikon komentar...")
        log_step("click_comment_icon", status="complete", device_id=device_pilihan, action="comment")
        btn_comment = d(descriptionMatches="(?i)(Komentar|Comment|Comment Icon)")
        if btn_comment.exists:
            btn_comment.click()
        else:
            d.click(int(width * 0.25), int(height * 0.65))
        time.sleep(3)

        print(f" [8] Memasukkan teks komentar: '{isi_komentar}'...")
        log_step("type_comment", status="complete", device_id=device_pilihan, action="comment")
        kolom_teks = d(className="android.widget.EditText")
        _kirim_komentar(d, isi_komentar, width, height)
        time.sleep(2)

        print(" [9] Mengirimkan komentar...")
        log_step("send_comment", status="complete", device_id=device_pilihan, action="comment")
        _tekan_kirim(d, kolom_teks, width, height)
        time.sleep(4)

        print(" [10] Kembali ke Beranda & Refresh...")
        log_step("return_home", status="complete", device_id=device_pilihan, action="comment")
        _kembali_ke_beranda(d, width, height)
        time.sleep(3)

        print(" [SUCCESS] Bot Comment Target berhasil dieksekusi!\n")
        log_complete(log_id, message=isi_komentar, extra_update={"komentar_terkirim": isi_komentar})

    except Exception as e:
        print(f" Terjadi kesalahan pada bot comment target: {e}")
        log_error(log_id, str(e))


# ========================================================
# FUNGSI 2: COMMENT BY KEYWORD (komentar berdasarkan hashtag/keyword)
# ========================================================
def comment_by_keyword(keyword, limit=5, komentar_custom="", device_pilihan="all", my_account=""):
    log_id = log_activity(
        action="comment_keyword", username=keyword,
        message=komentar_custom or "(otomatis)", status="on_progress",
        mode="manual", device_id=device_pilihan,
        extra={"keyword": keyword, "limit": limit, "my_account": my_account}
    )
    try:
        print("=========================================")
        print(f" JALANKAN BOT COMMENT BY KEYWORD: '{keyword}'")
        print(f" Target Comment: {limit} postingan")
        print(f" Komentar Kustom: {komentar_custom if komentar_custom else 'Otomatis/Sentimen'}")
        if my_account:
            print(f" Menggunakan Akun Saya: {my_account}")
        print("=========================================")

        d = connect_adb(device_pilihan, action="comment", step_label="[1/5] Menghubungkan ke perangkat Android via ADB...")
        width, height = d.window_size()
        print(f"Terhubung: {d.device_info.get('brand','?')} {d.device_info.get('model','Device')} ({width}x{height})")

        open_instagram(d, device_pilihan, action="comment", delay=6, step_label="[2/5] Membuka aplikasi Instagram...")
        clear_any_popup_fast(d)

        # === PROSES SWAP AKUN DI AWAL (JIKA PARAMETER DIBERIKAN) ===
        if my_account and my_account.strip() != "":
            print(f"[PRE-RUN] Mengganti akun ke: '{my_account}'...")
            success = switch_instagram_account(my_account, device_pilihan)
            if not success:
                print(f"[-] ERROR: Gagal beralih ke akun '{my_account}' pada perangkat '{device_pilihan}'. Menghentikan bot.")
                return
            time.sleep(3.0)

        print("[2.5] Memeriksa thread komentar terbuka dari sesi sebelumnya...")
        for check_idx in range(3):
            clear_any_popup_fast(d)
            if is_currently_comment_thread(d):
                print(f"      -> Thread komentar terbuka (percobaan tutup {check_idx+1}). Menutup...")
                d.press("back")
                time.sleep(1.0)
                if is_currently_comment_thread(d):
                    for rid in ["com.instagram.android:id/action_bar_button_back", "com.instagram.android:id/comment_composer_back_button", "com.instagram.android:id/comments_back_button"]:
                        if d(resourceId=rid).exists:
                            try: d(resourceId=rid).click(); time.sleep(1.0); break
                            except: pass
                if is_currently_comment_thread(d):
                    d.swipe(0.5, 0.30, 0.5, 0.90, duration=0.25); time.sleep(1.5)
            else:
                break

        print("[3/5] Navigasi ke halaman Pencarian (Search Page)...")
        log_step("navigate_search", status="complete", device_id=device_pilihan, action="comment")
        search_opened = False
        for step in range(8):
            clear_any_popup_fast(d)
            try:
                if d.app_current().get("package") != "com.instagram.android":
                    d.app_start("com.instagram.android"); time.sleep(4.0); continue
            except: pass
            if step == 3:
                try:
                    d.app_stop("com.instagram.android"); time.sleep(2.0)
                    d.app_start("com.instagram.android"); time.sleep(6.0)
                except Exception as e: print(f"      -> Gagal restart: {e}")
                continue
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
                        search_tab = d(descriptionMatches=f"(?i)^({desc}|tab {desc}|{desc} tab)$"); break
            if search_tab:
                try: search_tab.click(); time.sleep(3.0); continue
                except: pass
            has_nav = any(d(resourceId=r).exists for r in ["com.instagram.android:id/feed_tab","com.instagram.android:id/home_tab","com.instagram.android:id/profile_tab","com.instagram.android:id/clips_tab","com.instagram.android:id/reels_tab"])
            if has_nav:
                d.click(int(width * 0.30), int(height * 0.96)); time.sleep(3.0); continue
            print(f"      -> Sedang di sub-halaman (Langkah {step+1}). Mengirim BACK...")
            d.press("back"); time.sleep(2.0)
        if not search_opened:
            d.click(int(width * 0.30), int(height * 0.96)); time.sleep(4.0)

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
        time.sleep(2)

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
                target_input.click(); time.sleep(1.0); target_input.clear_text(); time.sleep(0.5); target_input.set_text(search_text)
            else:
                d.send_keys(search_text)
        except Exception as e:
            print(f"      -> Gagal mengetik kata kunci: {e}")
            try: d.send_keys(search_text)
            except: pass
        time.sleep(3)

        print("      Menekan tombol Enter pada keyboard...")
        d.press("enter"); time.sleep(4)

        if is_account_search:
            print("      Mencari tab 'Accounts'/'Akun'...")
            clear_any_popup_fast(d)
            accounts_tab = None
            for lab in ["Accounts", "Akun", "Profil", "Profiles", "AKUN", "ACCOUNTS"]:
                if d(text=lab).exists:
                    accounts_tab = d(text=lab); break
                elif d(textContains=lab).exists:
                    el = d(textContains=lab)
                    if el.info.get("bounds", {}).get("top", 0) < int(height * 0.20):
                        accounts_tab = el; break
            if accounts_tab:
                accounts_tab.click(); time.sleep(3)
            else:
                d.click(int(width * 0.30), int(height * 0.13)); time.sleep(2)

            profile_item = None
            for rid in ["com.instagram.android:id/row_search_user_info_container","com.instagram.android:id/row_search_user_container","com.instagram.android:id/row_search_user_username","com.instagram.android:id/title"]:
                if d(resourceId=rid).exists: profile_item = d(resourceId=rid); break
            if not profile_item or not profile_item.exists:
                profile_item = d(textMatches=f"(?i).*{re.escape(search_text)}.*")
            profile_clicked = False
            if profile_item and profile_item.exists:
                try: profile_item.click(); profile_clicked = True
                except: pass
            if not profile_clicked:
                d.click(int(width * 0.5), int(height * 0.25))
        else:
            # Mode Pencarian Kata Kunci (Keyword): Langsung di halaman utama pencarian (For You / Top / Popular)
            # Menggulir sedikit ke bawah agar postingan/grid terlihat jika tertutup hasil akun
            print("      -> Menggulir sedikit ke bawah agar postingan/grid hasil pencarian terlihat...")
            d.swipe(int(width * 0.5), int(height * 0.7), int(width * 0.5), int(height * 0.45), duration=0.2)
            time.sleep(2.0)

        time.sleep(3); clear_any_popup_fast(d)

        print("[4/5] Membuka postingan pertama di grid...")
        log_step("open_first_post", status="complete", device_id=device_pilihan, action="comment")
        post_clicked = False
        for rid in ["com.instagram.android:id/media_set_row_image","com.instagram.android:id/grid_item_image","com.instagram.android:id/image_button"]:
            btn = d(resourceId=rid)
            if btn.exists:
                try: btn.click(); post_clicked = True; break
                except: pass
        if not post_clicked:
            try:
                candidate_posts = []
                for el in d(clickable=True):
                    try:
                        info = el.info
                        bounds = info.get('bounds', {})
                        if bounds:
                            left = bounds.get('left', 0)
                            top = bounds.get('top', 0)
                            right = bounds.get('right', 0)
                            bottom = bounds.get('bottom', 0)
                            
                            x_c = (left + right) // 2
                            y_c = (top + bottom) // 2
                            el_w = right - left
                            el_h = bottom - top
                            
                            if (0 < x_c < int(width * 0.35) and 
                                int(height * 0.15) < y_c < int(height * 0.85) and 
                                int(width * 0.20) < el_w < int(width * 0.45) and
                                el_h > 100):
                                candidate_posts.append((y_c, el, x_c, y_c))
                    except:
                        pass
                if candidate_posts:
                    candidate_posts.sort(key=lambda x: x[0])
                    print(f"      -> Menemukan {len(candidate_posts)} postingan grid. Mengklik postingan pertama...")
                    candidate_posts[0][1].click()
                    post_clicked = True
            except Exception as e:
                print(f"      -> Gagal mencari postingan di grid: {e}")
        if not post_clicked:
            d.click(int(width * 0.168), int(height * 0.55))
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
                    d.click(int(width * 0.168), int(height * 0.55))
                time.sleep(3.5)

        clear_any_popup_fast(d)

        print("[5/5] Mulai proses Loop Komentar & Scroll...")
        log_step("comment_posts", status="on_progress", device_id=device_pilihan, action="comment")
        komentar_sukses = 0

        for idx in range(limit):
            print(f"\n--- Postingan Ke-{idx + 1} dari {limit} ---")
            clear_any_popup_fast(d)

            try:
                if d.app_current().get("package") != "com.instagram.android":
                    d.app_start("com.instagram.android"); time.sleep(4.0)
            except: pass

            try:
                is_grid_page = d(textMatches="(?i)^(Teratas|Top|Terbaru|Recent)$").exists or d(resourceId="com.instagram.android:id/row_hashtag_header_container").exists
                
                # Hanya anggap halaman grid profil jika ada teks "Posts"/"Postingan" tetapi TIDAK ada tombol interaksi postingan (Like/Comment)
                has_post_interaction = d(resourceIdMatches=".*(?i)(like_button|button_like|comment_button|button_comment|row_feed_button_like|row_feed_button_comment).*").exists or d(descriptionMatches="(?i)(like|suka|comment|komentar).*").exists
                is_profile_grid = (d(resourceId="com.instagram.android:id/row_profile_header").exists or d(text="Postingan").exists or d(text="Posts").exists) and not has_post_interaction
                
                if is_grid_page or is_profile_grid:
                    print("      [Safety] Terlempar ke halaman grid! Masuk kembali ke detail post...")
                    post_btn = None
                    for rid in ["com.instagram.android:id/image_button","com.instagram.android:id/media_set_row_image","com.instagram.android:id/grid_item_image"]:
                        if d(resourceId=rid).exists: post_btn = d(resourceId=rid); break
                    if post_btn: post_btn.click()
                    else: d.click(int(width * 0.17), int(height * 0.55))
                    time.sleep(3.5)
            except Exception as se: print(f"      [Safety] Error: {se}")

            caption_terdeteksi = ""
            selector_caption = d(resourceId="com.instagram.android:id/row_feed_textview")
            if selector_caption.exists:
                caption_terdeteksi = selector_caption.get_text()
                print(f"      Caption: '{caption_terdeteksi[:40]}...'")

            isi_komentar = generate_komentar_otomatis(caption_terdeteksi, komentar_custom)

            comment_icon_clicked = False

            # 1. PRIORITAS UTAMA: Cari berdasarkan Deskripsi (Sangat Akurat & Unik pada icon)
            selector = d(descriptionMatches="(?i)(Komentar|Comment|Comment Icon|Comment button|Komentar button)")
            if selector.exists:
                for idx_elem in range(selector.count):
                    try:
                        elem = selector[idx_elem]
                        bounds = elem.info.get("bounds")
                        if bounds:
                            y_center = (bounds["top"] + bounds["bottom"]) // 2
                            x_center = (bounds["left"] + bounds["right"]) // 2
                            # Hanya klik yang terlihat di area aktif layar
                            if height * 0.15 < y_center < height * 0.88:
                                d.click(x_center, y_center)
                                comment_icon_clicked = True
                                print(f"      -> Klik ikon komentar via description: (instance={idx_elem})")
                                break
                    except:
                        pass
                if comment_icon_clicked:
                    pass

            # 2. PRIORITAS KEDUA: Cari berdasarkan Resource ID
            if not comment_icon_clicked:
                for rid in ["com.instagram.android:id/row_feed_button_comment", "com.instagram.android:id/comment_button", "com.instagram.android:id/comment_icon"]:
                    selector = d(resourceId=rid)
                    if selector.exists:
                        for idx_elem in range(selector.count):
                            try:
                                elem = selector[idx_elem]
                                bounds = elem.info.get("bounds")
                                if bounds:
                                    y_center = (bounds["top"] + bounds["bottom"]) // 2
                                    x_center = (bounds["left"] + bounds["right"]) // 2
                                    if height * 0.15 < y_center < height * 0.88:
                                        d.click(x_center, y_center)
                                        comment_icon_clicked = True
                                        print(f"      -> Klik ikon komentar via ID: {rid} (instance={idx_elem})")
                                        break
                            except:
                                pass
                        if comment_icon_clicked:
                            break

            if not comment_icon_clicked:
                for tv in ["Add comment...", "Add comment…", "Tambahkan komentar...", "Tambahkan komentar…", "Komentar..."]:
                    selector = d(text=tv)
                    if selector.exists:
                        for idx_elem in range(selector.count):
                            try:
                                elem = selector[idx_elem]
                                bounds = elem.info.get("bounds")
                                if bounds:
                                    y_center = (bounds["top"] + bounds["bottom"]) // 2
                                    x_center = (bounds["left"] + bounds["right"]) // 2
                                    if height * 0.15 < y_center < height * 0.95:
                                        d.click(x_center, y_center)
                                        comment_icon_clicked = True
                                        print(f"      -> Klik bar komentar via text: '{tv}' (instance={idx_elem})")
                                        break
                            except:
                                pass
                        if comment_icon_clicked:
                            break

            if not comment_icon_clicked:
                # Fallback Dinamis: Dapatkan koordinat Y dari Like button yang terlihat
                like_y = None
                for like_id in ["com.instagram.android:id/row_feed_button_like", "com.instagram.android:id/like_button"]:
                    sel_like = d(resourceId=like_id)
                    if sel_like.exists:
                        for idx_l in range(sel_like.count):
                            try:
                                b_like = sel_like[idx_l].info.get("bounds")
                                if b_like:
                                    y_l = (b_like["top"] + b_like["bottom"]) // 2
                                    if height * 0.15 < y_l < height * 0.90:
                                        like_y = y_l
                                        break
                            except:
                                pass
                        if like_y:
                            break

                if like_y:
                    print(f"      -> Koordinat baris interaksi ditemukan di Y={like_y}. Klik X=20%...")
                    d.click(int(width * 0.20), like_y)
                    comment_icon_clicked = True
                else:
                    print("      -> Klik koordinat fallback absolut...")
                    d.click(int(width * 0.20), int(height * 0.72))
                    comment_icon_clicked = True

            time.sleep(3.0); clear_any_popup_fast(d)

            comment_typed = False
            kolom_teks = None
            # 1. Cari berdasarkan Resource ID input komentar yang umum
            for rid in [
                "com.instagram.android:id/layout_comment_thread_edittext",
                "com.instagram.android:id/comment_composer_text",
                "com.instagram.android:id/comment_composer_edittext",
                "com.instagram.android:id/layout_comment_thread_edittext_container"
            ]:
                sel = d(resourceId=rid)
                if sel.exists:
                    kolom_teks = sel
                    break

            # 2. Cari berdasarkan textContains / descriptionContains (untuk placeholder dinamis seperti "Tambahkan komentar sebagai...")
            if not kolom_teks or not kolom_teks.exists:
                for kw in ["tambahkan komentar", "add a comment", "add comment", "komentar sebagai", "comment as", "komentar", "comment"]:
                    sel = d(textMatches=f"(?i).*{re.escape(kw)}.*")
                    if not sel.exists:
                        sel = d(descriptionMatches=f"(?i).*{re.escape(kw)}.*")
                    if sel.exists:
                        for idx_e in range(sel.count):
                            try:
                                bounds = sel[idx_e].info.get("bounds")
                                if bounds and bounds["top"] > height * 0.7:
                                    kolom_teks = sel[idx_e]
                                    break
                            except:
                                pass
                    if kolom_teks and kolom_teks.exists:
                        break

            # 3. Fallback: Cari EditText tipe input apa saja di layar
            if not kolom_teks or not kolom_teks.exists:
                sel = d(className="android.widget.EditText")
                if sel.exists:
                    kolom_teks = sel

            if kolom_teks and kolom_teks.exists:
                try:
                    kolom_teks.click(); time.sleep(1.5); clear_any_popup_fast(d)
                    kolom_aktif = d(className="android.widget.EditText")
                    if not kolom_aktif.exists: kolom_aktif = d(resourceId="com.instagram.android:id/layout_comment_thread_edittext")
                    if not kolom_aktif.exists: kolom_aktif = kolom_teks
                    kolom_aktif.click(); time.sleep(1.0)
                    for _ in range(50): d.keyevent("67")
                    time.sleep(0.5)
                    d.send_keys(isi_komentar)
                    print(f"      -> Komentar diisi: '{isi_komentar}'")
                    comment_typed = True
                except Exception as te: print(f"      -> Gagal mengetik komentar: {te}")

            if not comment_typed:
                print("      [WARNING] Kolom komentar gagal dibuka. Melewati postingan ini...")
                if is_currently_comment_thread(d):
                    d.press("back"); time.sleep(1.5)
                if idx < limit - 1:
                    d.swipe(0.5, 0.75, 0.5, 0.20, duration=0.25); time.sleep(3.5)
                continue

            time.sleep(2)
            _tekan_kirim(d, kolom_teks, width, height)
            time.sleep(3.5)
            komentar_sukses += 1

            print("      -> Menutup thread komentar...")
            try: d.keyboard_dismiss(); time.sleep(1.0)
            except: pass
            comment_closed = False
            for back_attempt in range(4):
                if not is_currently_comment_thread(d):
                    print("      -> Sukses kembali ke detail postingan.")
                    comment_closed = True; break
                print(f"      -> Masih di komentar (percobaan {back_attempt+1}). Menutup...")
                for rid in ["com.instagram.android:id/action_bar_button_back","com.instagram.android:id/comment_composer_back_button","com.instagram.android:id/comments_back_button","com.instagram.android:id/back_button"]:
                    btn = d(resourceId=rid)
                    if btn.exists:
                        try: btn.click(); time.sleep(1.5); break
                        except: pass
                if is_currently_comment_thread(d):
                    for desc in ["Back","Kembali","Close","Tutup"]:
                        btn = d(descriptionContains=desc)
                        if not btn.exists: btn = d(textContains=desc)
                        if btn.exists:
                            try: btn.click(); time.sleep(1.5); break
                            except: pass
                if is_currently_comment_thread(d):
                    d.press("back"); time.sleep(1.0)
                if is_currently_comment_thread(d):
                    d.swipe(0.5, 0.35, 0.5, 0.90, duration=0.25); time.sleep(1.5)
            clear_any_popup_fast(d)

            if idx < limit - 1:
                print("      -> Men-scroll ke postingan berikutnya...")
                d.swipe(0.5, 0.75, 0.5, 0.20, duration=0.25); time.sleep(3.5)

        print("\n[+] LOOP SELESAI. Kembali ke Beranda...")
        _kembali_ke_beranda(d, width, height)
        time.sleep(2)

        try:
            d.app_stop("com.instagram.android"); time.sleep(2.0)
            d.shell("am force-stop com.instagram.android"); time.sleep(2.0)
            d.app_start("com.instagram.android"); time.sleep(5.0)
            clear_any_popup_fast(d)
        except Exception as opt_err:
            print(f"      -> Gagal melakukan optimalisasi cache: {opt_err}")

        print("=========================================")
        print(f" BOT COMMENT BY KEYWORD SELESAI")
        print(f" Total Komentar Sukses: {komentar_sukses}")
        print("=========================================\n")
        print("___BOT_RESULT_SUCCESS___")
        log_complete(log_id, extra_update={"komentar_sukses": komentar_sukses, "keyword": keyword})
        sys.exit(0)

    except Exception as e:
        print(f"[-] ERROR BOT COMMENT BY KEYWORD: {e}")
        print(f"___BOT_RESULT_ERROR___{str(e)}")
        log_error(log_id, str(e))
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
        print("  1. Comment Target URL:  python3 bot_ig_comment.py <url> <komentar> [device_id] [my_account] target_url")
        print("  2. Comment Normal:      python3 bot_ig_comment.py <keyword> [limit] <komentar> [device_id] [my_account] normal")
        sys.exit(1)

    # Deteksi Mode Trailing (Paling Belakang)
    last_arg = sys.argv[-1].lower() if len(sys.argv) > 1 else ""
    first_arg = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    
    # 1. Mode Trailing
    if last_arg == "target_url":
        url = sys.argv[1] if len(sys.argv) > 2 else ""
        komentar_custom = sys.argv[2] if len(sys.argv) > 3 and sys.argv[2].lower() != "target_url" else ""
        device_pilihan = sys.argv[3] if len(sys.argv) > 4 and sys.argv[3].lower() != "target_url" else "all"
        my_account = sys.argv[4] if len(sys.argv) > 5 and sys.argv[4].lower() != "target_url" else ""
        
        if not url:
            print("ERROR: URL target wajib disertakan!")
            sys.exit(1)
            
        devices = resolve_devices(device_pilihan)
        if len(devices) > 1:
            run_parallel_threads(comment_target, devices, target_user=url, komentar_custom=komentar_custom, my_account=my_account)
        else:
            comment_target(url, komentar_custom, device_pilihan=devices[0], my_account=my_account)

    elif last_arg == "normal":
        keyword = sys.argv[1] if len(sys.argv) > 2 else ""
        limit_str = sys.argv[2] if len(sys.argv) > 3 and sys.argv[2].lower() != "normal" else "5"
        komentar_custom = sys.argv[3] if len(sys.argv) > 4 and sys.argv[3].lower() != "normal" else ""
        device_id = sys.argv[4] if len(sys.argv) > 5 and sys.argv[4].lower() != "normal" else "all"
        my_account = sys.argv[5] if len(sys.argv) > 6 and sys.argv[5].lower() != "normal" else ""
        
        if not keyword:
            print("ERROR: Kata kunci pencarian wajib disertakan!")
            sys.exit(1)
            
        try:
            limit = int(limit_str)
        except ValueError:
            # Jika limit dilewati: e.g. python3 bot_ig_comment.py "kucing" "Mantap!" R9RY801LRPW normal
            komentar_custom = limit_str
            device_id = sys.argv[3] if len(sys.argv) > 4 and sys.argv[3].lower() != "normal" else "all"
            my_account = sys.argv[4] if len(sys.argv) > 5 and sys.argv[4].lower() != "normal" else ""
            limit = 5
            
        devices = resolve_devices(device_id)
        if len(devices) > 1:
            run_parallel_threads(comment_by_keyword, devices, keyword=keyword, limit=limit, komentar_custom=komentar_custom, my_account=my_account)
        else:
            comment_by_keyword(keyword, limit, komentar_custom, device_pilihan=devices[0], my_account=my_account)

    # 2. Mode Eksplisit (Awalan / di Depan) - kompatibilitas
    elif first_arg in ("target_url", "url", "username", "target", "comment_target"):
        target_user = sys.argv[2] if len(sys.argv) > 2 else ""
        komentar_custom = sys.argv[3] if len(sys.argv) > 3 else ""
        device_pilihan = sys.argv[4] if len(sys.argv) > 4 else "all"
        my_account = sys.argv[5] if len(sys.argv) > 5 else ""
        if not target_user:
            target_user = input("Masukkan username/URL target (default 'cristiano'): ").strip() or "cristiano"
        
        devices = resolve_devices(device_pilihan)
        if len(devices) > 1:
            run_parallel_threads(comment_target, devices, target_user=target_user, komentar_custom=komentar_custom, my_account=my_account)
        else:
            comment_target(target_user, komentar_custom, device_pilihan=devices[0], my_account=my_account)

    elif first_arg in ("keyword", "comment_keyword", "normal"):
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        limit = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 5
        komentar_custom = sys.argv[4] if len(sys.argv) > 4 else ""
        device_id = sys.argv[5] if len(sys.argv) > 5 else "all"
        my_account = sys.argv[6] if len(sys.argv) > 6 else ""
        if not keyword:
            keyword = input("Masukkan keyword/hashtag (default 'photography'): ").strip() or "photography"
        
        devices = resolve_devices(device_id)
        if len(devices) > 1:
            run_parallel_threads(comment_by_keyword, devices, keyword=keyword, limit=limit, komentar_custom=komentar_custom, my_account=my_account)
        else:
            comment_by_keyword(keyword, limit, komentar_custom, device_pilihan=devices[0], my_account=my_account)

    else:
        # ==== AUTO-DETECT (Kompatibilitas Mundur) ====
        first_arg = sys.argv[1] if len(sys.argv) > 1 else ""
        if first_arg.startswith("#") or (len(sys.argv) > 2 and sys.argv[2].isdigit()):
            keyword = first_arg
            limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 5
            komentar_custom = sys.argv[3] if len(sys.argv) > 3 else ""
            device_id = sys.argv[4] if len(sys.argv) > 4 else "all"
            my_account = sys.argv[5] if len(sys.argv) > 5 else ""
            if not keyword:
                keyword = input("Masukkan keyword/hashtag (default 'photography'): ").strip() or "photography"
            
            devices = resolve_devices(device_id)
            if len(devices) > 1:
                run_parallel_threads(comment_by_keyword, devices, keyword=keyword, limit=limit, komentar_custom=komentar_custom, my_account=my_account)
            else:
                comment_by_keyword(keyword, limit, komentar_custom, device_pilihan=devices[0], my_account=my_account)
        else:
            target_user = first_arg
            komentar_custom = sys.argv[2] if len(sys.argv) > 2 else ""
            device_pilihan = sys.argv[3] if len(sys.argv) > 3 else "all"
            my_account = sys.argv[4] if len(sys.argv) > 4 else ""
            if not target_user:
                target_user = input("Masukkan username/URL target (default 'cristiano'): ").strip() or "cristiano"
            
            devices = resolve_devices(device_pilihan)
            if len(devices) > 1:
                run_parallel_threads(comment_target, devices, target_user=target_user, komentar_custom=komentar_custom, my_account=my_account)
            else:
                comment_target(target_user, komentar_custom, device_pilihan=devices[0], my_account=my_account)
