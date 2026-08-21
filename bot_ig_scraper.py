import sys
import uiautomator2 as u2
import time
import os
from ig_helpers import connect_adb, open_instagram

def clear_popups_scraper(d):
    try:
        width, height = d.window_size()
    except Exception:
        width, height = 1080, 1920

    # Cek batas harian (Daily Limit)
    try:
        limit_title = d(textMatches="(?i).*(reached your daily limit|batas harian).*")
        more_opt = d(textMatches="(?i).*(more options|opsi lainnya).*")
        if limit_title.exists or more_opt.exists:
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
        
    try:
        current_app = d.app_current()
        pkg = current_app.get('package', '')
        if pkg and pkg != 'com.instagram.android' and pkg != 'com.android.systemui' and pkg != 'com.sec.android.app.launcher' and 'launcher' not in pkg.lower():
            print(f"      -> Mendeteksi jendela sistem/non-Instagram: '{pkg}'. Mengirim BACK...")
            d.press("back")
            time.sleep(1.2)
    except Exception:
        pass
        
    # Cari tombol penutup persis
    for target in ["Lain kali", "Lain Kali", "Not Now", "Not now", "Jangan sekarang", "Jangan Sekarang", "Tutup", "Close"]:
        btn = d(text=target)
        if btn.exists:
            try:
                btn.click()
                time.sleep(1.0)
                return
            except Exception:
                pass
        btn_desc = d(description=target)
        if btn_desc.exists:
            try:
                btn_desc.click()
                time.sleep(1.0)
                return
            except Exception:
                pass

def bot_scrape(target_competitor, scrape_type="followers", limit=50, device_pilihan="all"):
    try:
        print("=========================================")
        print(" JALANKAN BOT SCRAPER INSTAGRAM")
        print(f" Target Kompetitor : @{target_competitor}")
        print(f" Tipe Scraping     : {scrape_type.upper()}")
        print(f" Batas Maksimal    : {limit} username")
        print(f" Perangkat         : {device_pilihan}")
        print("=========================================")

        d = connect_adb(device_pilihan, action=None, step_label="[1] Menghubungkan ke perangkat Android...")
        width, height = d.window_size()
        print(f"Terhubung ke perangkat: {d.device_info.get('brand', 'Unknown')} {d.device_info.get('model', 'Device')}")

        open_instagram(d, device_pilihan, action=None, delay=4, step_label="[2] Membuka aplikasi Instagram...")
        clear_popups_scraper(d)

        is_link = "instagram.com" in target_competitor or target_competitor.startswith("http")
        
        if is_link:
            if scrape_type.lower() == "followers":
                print("ERROR: Tipe scraping followers tidak mendukung link postingan langsung!")
                sys.exit(1)
                
            print(f"[3] Membuka link postingan secara langsung: {target_competitor}...")
            d.shell(["am", "start", "-a", "android.intent.action.VIEW", "-d", target_competitor, "com.instagram.android"])
            time.sleep(6)
            clear_popups_scraper(d)
        else:
            print(f"[3] Mencari profil kompetitor: @{target_competitor}...")
            search_tab = None
            if d(resourceId="com.instagram.android:id/search_tab").exists:
                search_tab = d(resourceId="com.instagram.android:id/search_tab")
            else:
                sel = d(descriptionMatches="(?i).*(search|cari|explore|jelajahi).*", packageName="com.instagram.android")
                if sel.exists:
                    search_tab = sel
                    
            if search_tab:
                try:
                    search_tab.click()
                    print("      -> Mengklik tab Pencarian via selector...")
                    time.sleep(2.5)
                except:
                    pass
            else:
                print("      -> Mengklik tab Pencarian via koordinat fallback...")
                d.click(int(width * 0.30), int(height * 0.93))
                time.sleep(1.5)
                d.click(int(width * 0.30), int(height * 0.914))
                time.sleep(2.0)

            print("      Mengklik kolom pencarian...")
            if d(resourceId="com.instagram.android:id/action_bar_search_edit_text").exists:
                d(resourceId="com.instagram.android:id/action_bar_search_edit_text").click()
            elif d(resourceId="com.instagram.android:id/search_bar").exists:
                d(resourceId="com.instagram.android:id/search_bar").click()
            elif d(className="android.widget.EditText").exists:
                d(className="android.widget.EditText").click()
            else:
                d.click(int(width * 0.5), int(height * 0.06))
            time.sleep(1.5)

            print(f"      Mengetik nama kompetitor: {target_competitor}")
            try:
                if d(resourceId="com.instagram.android:id/action_bar_search_edit_text").exists:
                    d(resourceId="com.instagram.android:id/action_bar_search_edit_text").clear_text()
                elif d(className="android.widget.EditText").exists:
                    d(className="android.widget.EditText").clear_text()
            except:
                pass
            d.send_keys(target_competitor)
            time.sleep(3)

            d.press("enter")
            time.sleep(3)

            print("      Memilih profil kompetitor...")
            row_username = d(resourceId="com.instagram.android:id/row_search_user_username", text=target_competitor)
            row_username_contains = d(resourceId="com.instagram.android:id/row_search_user_username", textContains=target_competitor)
            akun_target_text = d(text=target_competitor, className="android.widget.TextView")
            container_1 = d(resourceId="com.instagram.android:id/row_search_user_info_container")
            container_2 = d(resourceId="com.instagram.android:id/row_search_user_container")
            
            clicked_target = False
            for selector in [row_username, row_username_contains, akun_target_text, container_1, container_2]:
                if selector.exists:
                    try:
                        selector.click()
                        clicked_target = True
                        break
                    except Exception as e:
                        print(f"      -> Info: Gagal klik selector ({e})")
                        
            if not clicked_target:
                print("      -> Klik default koordinat pencarian teratas...")
                d.click(int(width * 0.5), int(height * 0.24))
            time.sleep(5)
            clear_popups_scraper(d)

        output_file = "scraped_targets.txt"
        existing_targets = set()
        if os.path.exists(output_file):
            try:
                with open(output_file, "r") as f:
                    for line in f:
                        line_str = line.strip()
                        if line_str:
                            usr = line_str.split('|')[0].strip()
                            existing_targets.add(usr)
            except Exception as read_err:
                print(f"Peringatan: Gagal membaca file target lama: {read_err}")

        scraped_users = {}  # key: username, value: display_name/fullname

        if scrape_type.lower() == "followers":
            print("[4] Membuka daftar Followers/Pengikut...")
            followers_btn = None
            
            # Cari tombol followers di layar
            for txt_val in ["pengikut", "followers", "Followers", "Pengikut"]:
                elem = d(textContains=txt_val)
                if elem.exists:
                    followers_btn = elem
                    break
                    
            if not followers_btn:
                # Coba resource id yang umum
                for rid in ["com.instagram.android:id/row_profile_header_followers_container", "com.instagram.android:id/row_profile_header_followers_layout"]:
                    if d(resourceId=rid).exists:
                        followers_btn = d(resourceId=rid)
                        break
                        
            if followers_btn:
                followers_btn.click()
                print("      -> Mengklik tombol pengikut")
            else:
                print("      -> Tombol pengikut tidak terdeteksi via teks, menggunakan koordinat fallback (0.62, 0.12)...")
                d.click(int(width * 0.62), int(height * 0.12))
            time.sleep(5)

            print("[5] Memulai ekstraksi data Followers...")
            stuck_count = 0
            
            while len(scraped_users) < limit:
                found_new_this_turn = False
                
                # Coba cara 1: Gunakan resource ID khusus untuk nama profil (subtitle / full name) jika ada
                selectors_username = d(resourceIdMatches=".*(?i)(follow_list_username|user_name|username).*")
                selectors_subtitle = d(resourceIdMatches=".*(?i)(follow_list_subtitle|follow_list_name).*")
                
                if selectors_username.exists and selectors_username.count > 0:
                    for idx in range(selectors_username.count):
                        try:
                            usr = selectors_username[idx].info.get('text', '').strip()
                            if usr and ' ' not in usr and len(usr) >= 3 and len(usr) <= 30:
                                exclusions = ["pengikut", "followers", "mengikuti", "following", "saran", "suggested", "hapus", "remove", "batal", "cancel", "tutup", "close", "instagram", "threads"]
                                if any(ex in usr.lower() for ex in exclusions):
                                    continue
                                
                                if usr in scraped_users or usr in existing_targets:
                                    continue
                                    
                                # Ambil subtitle (nama lengkap) jika ada pada indeks yang sama
                                display_name = usr
                                if selectors_subtitle.exists and idx < selectors_subtitle.count:
                                    sub_txt = selectors_subtitle[idx].info.get('text', '').strip()
                                    # Pastikan sub_txt bukan info hubungan
                                    if sub_txt and not any(info_word in sub_txt.lower() for info_word in ["diikuti oleh", "followed by", "mutual", "pengikut sama"]):
                                        display_name = sub_txt
                                
                                scraped_users[usr] = display_name
                                found_new_this_turn = True
                        except:
                            pass
                
                # Fallback: pindaian TextView
                if not found_new_this_turn:
                    for txt_elem in d(className="android.widget.TextView"):
                        try:
                            txt = txt_elem.info.get('text', '').strip()
                            if txt and ' ' not in txt and len(txt) >= 3 and len(txt) <= 30:
                                exclusions = ["pengikut", "followers", "mengikuti", "following", "saran", "suggested", "hapus", "remove", "batal", "cancel", "tutup", "close", "instagram", "threads", "cari", "search", "beranda", "home"]
                                if not any(ex in txt.lower() for ex in exclusions):
                                    if txt not in scraped_users and txt not in existing_targets:
                                        scraped_users[txt] = txt
                                        found_new_this_turn = True
                        except:
                            pass
                
                if found_new_this_turn:
                    print(f"      -> Berhasil mengekstrak pengikut baru. Total: {len(scraped_users)}/{limit}")
                    stuck_count = 0
                else:
                    stuck_count += 1

                if len(scraped_users) >= limit:
                    break

                if stuck_count >= 5:
                    print("      -> Deteksi akhir daftar / list stuck. Mengakhiri scraping.")
                    break

                # Scroll ke bawah untuk memuat data baru (flick scroll)
                d.swipe(0.5, 0.75, 0.5, 0.25, duration=0.15)
                time.sleep(1.5)

        elif scrape_type.lower() == "comments":
            if is_link:
                print("[4] Link postingan dideteksi, langsung memproses thread komentar...")
            else:
                print("[4] Membuka postingan pertama kompetitor...")
                post_clicked = False
                
                # Coba klik media grid pertama
                for rid in ["com.instagram.android:id/image_button", "com.instagram.android:id/media_picker_grid_view"]:
                    elem = d(resourceId=rid)
                    if elem.exists:
                        elem.click()
                        post_clicked = True
                        break
                        
                if not post_clicked:
                    # Koordinat fallback postingan pertama di kisi grid profil (kiri atas grid)
                    print("      -> Postingan tidak terdeteksi via id, menggunakan koordinat grid kiri atas (0.16, 0.52)...")
                    d.click(int(width * 0.16), int(height * 0.52))
                    post_clicked = True
                time.sleep(4)

            print("[5] Membukanya thread komentar...")
            comment_btn_clicked = False
            
            # Klik tombol komentar di postingan
            comment_selectors = [
                d(resourceIdMatches=".*(?i)(button_comment|comment_button).*"),
                d(descriptionContains="Komentar"),
                d(descriptionContains="Comment")
            ]
            for sel in comment_selectors:
                if sel.exists:
                    sel.click()
                    comment_btn_clicked = True
                    break
                    
            if not comment_btn_clicked:
                # Coba klik teks "Lihat semua komentar"
                for view_all in ["Lihat semua komentar", "View all comments", "Lihat komentar", "View comments"]:
                    elem = d(textContains=view_all)
                    if elem.exists:
                        elem.click()
                        comment_btn_clicked = True
                        break
                        
            if not comment_btn_clicked:
                # Klik koordinat tombol komentar pada feed standard (x=22%)
                d.click(int(width * 0.22), int(height * 0.65))
                comment_btn_clicked = True
            time.sleep(6.0)

            print("[6] Memulai ekstraksi data Komentator...")
            stuck_count = 0
            
            while len(scraped_users) < limit:
                found_new_this_turn = False
                found_usernames = set()
                
                # Coba cara 1: Ambil lewat resource ID komentator
                selectors = d(resourceIdMatches=".*(?i)(row_comment_author_id|comment_author).*")
                if selectors.exists and selectors.count > 0:
                    for idx in range(selectors.count):
                        try:
                            username = selectors[idx].info.get('text', '').strip()
                            if username and ' ' not in username and len(username) >= 3 and len(username) <= 30:
                                exclusions = ["balas", "reply", "suka", "like", "komentar", "comment", "tanggapan", "lihat", "view", "menit", "hour", "day", "hari", "jam", "minggu", "week"]
                                if not any(ex in username.lower() for ex in exclusions):
                                    found_usernames.add(username)
                        except:
                            pass
                
                # Coba cara 2: Fallback pindaian TextView
                for txt_elem in d(className="android.widget.TextView"):
                    try:
                        username = txt_elem.info.get('text', '').strip()
                        if username and ' ' not in username and len(username) >= 3 and len(username) <= 30:
                            exclusions = ["balas", "reply", "suka", "like", "komentar", "comment", "tanggapan", "lihat", "view", "menit", "hour", "day", "hari", "jam", "minggu", "week", "cari", "search", "beranda", "home"]
                            if not any(ex in username.lower() for ex in exclusions):
                                found_usernames.add(username)
                    except:
                        pass
                
                # Tambahkan ke database hasil
                for username in found_usernames:
                    if username not in scraped_users and username not in existing_targets:
                        scraped_users[username] = username  # Simpan username sebagai fullname
                        found_new_this_turn = True
                
                if found_new_this_turn:
                    print(f"      -> Berhasil mengekstrak komentator baru. Total: {len(scraped_users)}/{limit}")
                    stuck_count = 0
                else:
                    stuck_count += 1
                    
                if len(scraped_users) >= limit:
                    break
                    
                if stuck_count >= 5:
                    print("      -> Akhir thread komentar terdeteksi atau stuck. Selesai.")
                    break
                    
                # Scroll ke bawah di kolom komentar
                d.swipe(0.5, 0.75, 0.5, 0.25, duration=0.15)
                time.sleep(1.5)

        # Kembali ke beranda setelah selesai scraping (dengan forced stop + restart agar bersih)
        print("[*] Mengembalikan tampilan Instagram ke Beranda...")
        try:
            print("      -> Menghentikan paksa (kill) aplikasi Instagram...")
            d.app_stop("com.instagram.android")
            time.sleep(2.0)
            
            print("      -> Membuka kembali aplikasi Instagram...")
            d.app_start("com.instagram.android")
            time.sleep(5.0)
            clear_popups_scraper(d)
            
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
            print("      -> Kembali ke Beranda & refresh berhasil.")
        except Exception as home_err:
            print(f"Peringatan: Gagal kembali ke Beranda: {home_err}")

        # Tambahkan target baru
        final_list_to_add = []
        for usr, fullname in scraped_users.items():
            if usr not in existing_targets:
                final_list_to_add.append(f"{usr} | {fullname}")
        
        if final_list_to_add:
            try:
                with open(output_file, "a") as f:
                    for line_to_write in final_list_to_add:
                        f.write(f"{line_to_write}\n")
                print(f"\n[SUKSES] Menyimpan {len(final_list_to_add)} username baru ke '{output_file}'.")
            except Exception as write_err:
                print(f"ERROR: Gagal menulis data ke file: {write_err}")
        else:
            print("\n[INFO] Semua username hasil scraping sudah ada di database targets (tidak ada duplikat baru).")

        print("=========================================")
        print(f" SCRAPING SELESAI: Berhasil mengekstrak {len(scraped_users)} total username.")
        print(f" Silakan cek file '{output_file}' untuk daftar target lengkap.")
        print("=========================================\n")
        sys.exit(0)

    except Exception as e:
        print(f"[ERROR EXCEPTION] Terjadi kesalahan saat scraping: {e}")
        sys.exit(1)

if __name__ == "__main__":
    competitor = sys.argv[1] if len(sys.argv) > 1 else ""
    stype = sys.argv[2] if len(sys.argv) > 2 else "followers"
    limit_val = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    device_id = sys.argv[4] if len(sys.argv) > 4 else "all"
    
    if not competitor:
        print("ERROR: Argumen target kompetitor tidak boleh kosong!")
        print("Penggunaan: python bot_ig_scraper.py <username_kompetitor> <followers/comments> <limit> <device_id>")
        sys.exit(1)
        
    bot_scrape(competitor, stype, limit_val, device_id)
