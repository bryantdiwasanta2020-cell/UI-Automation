import sys
import uiautomator2 as u2
import time
import json
import re
from ig_helpers import connect_adb

def scrape_profile_stats(d, pkg):
    posts = "0"
    followers = "0"
    
    try:
        # 1. Coba lewat Resource ID resmi (paling cepat & akurat)
        for p_id in [f"{pkg}:id/row_profile_header_textview_post_count", f"{pkg}:id/row_profile_header_post_count"]:
            el = d(resourceId=p_id)
            if el.exists:
                posts = el.get_text().strip()
                break
                
        for f_id in [f"{pkg}:id/row_profile_header_textview_followers_count", f"{pkg}:id/row_profile_header_followers_count"]:
            el = d(resourceId=f_id)
            if el.exists:
                followers = el.get_text().strip()
                break
                
        # 2. Fallback: Cari lewat flow teks di layar (sangat robust)
        if posts == "0" or followers == "0":
            all_texts = []
            for el in d(classNameMatches=".*(TextView|Button).*"):
                if el.exists:
                    try:
                        txt = el.get_text()
                        if txt:
                            val = txt.strip()
                            if val and val not in all_texts:
                                all_texts.append(val)
                    except:
                        pass
                        
            for idx, text in enumerate(all_texts):
                text_lower = text.lower()
                if text_lower in ["postingan", "posts", "post"]:
                    for offset in [-1, 1]:
                        if 0 <= idx + offset < len(all_texts):
                            candidate = all_texts[idx + offset]
                            if re.match(r'^[\d.,]+[kmKM]?$', candidate):
                                posts = candidate
                                break
                elif text_lower in ["pengikut", "followers", "follower"]:
                    for offset in [-1, 1]:
                        if 0 <= idx + offset < len(all_texts):
                            candidate = all_texts[idx + offset]
                            if re.match(r'^[\d.,]+[kmKM]?$', candidate):
                                followers = candidate
                                break
                                
        # 3. Bersihkan format angka agar rapi
        posts = re.sub(r'[^\d.,kKmM]', '', posts)
        followers = re.sub(r'[^\d.,kKmM]', '', followers)
        
        if not posts or posts == "0": posts = "0"
        if not followers or followers == "0": followers = "0"
        
    except Exception as e:
        print(f"      -> Gagal scrape profil stats: {e}")
        
    return posts, followers

def scan_accounts(device_id="all"):
    try:
        print("=========================================")
        print(f" RUN SCAN INSTAGRAM ACCOUNTS FOR: {device_id}")
        print("=========================================")
        
        print("[1] Menghubungkan ke perangkat Android...")
        d = connect_adb(device_id)
            
        width, height = d.window_size()
        
        # Daftar package aplikasi sosmed yang akan dipindai
        target_packages = {
            "com.instagram.android": "Instagram"
        }
        
        scraped_results = []
        
        for pkg, app_name in target_packages.items():
            # Cek apakah aplikasi terinstall di perangkat
            try:
                d.app_info(pkg)
                print(f"      -> Mendeteksi aplikasi terinstall: {app_name} ({pkg})")
            except:
                print(f"      -> Aplikasi tidak ditemukan: {app_name} ({pkg})")
                continue
                
            print(f"[2] Membuka aplikasi {app_name}...")
            d.app_start(pkg)
            time.sleep(6)
            
            # 1. Pastikan di tab Profil (klik kanan bawah)
            print(f"      -> Membuka Halaman Profil {app_name}...")
            profile_tab = None
            for selector in [
                d(resourceId=f"{pkg}:id/profile_tab"),
                d(resourceId=f"{pkg}:id/profile_tab_icon"),
                d(descriptionContains="Profil"),
                d(descriptionContains="Profile"),
                d(descriptionContains="Profil Anda"),
                d(descriptionContains="Your Profile")
            ]:
                if selector.exists:
                    profile_tab = selector
                    break
                    
            if profile_tab:
                profile_tab.click()
            else:
                # Fallback koordinat kanan bawah (Dinaikkan dari 0.96 ke 0.93 agar di atas tombol navigasi sistem)
                d.click(int(width * 0.90), int(height * 0.93))
            time.sleep(4)
            
            # 2. Dapatkan username aktif saat ini (top-left)
            active_user = None
            selectors_active = [
                d(resourceId=f"{pkg}:id/title_text"),
                d(resourceId=f"{pkg}:id/action_bar_title"),
                d(resourceId=f"{pkg}:id/row_profile_header_username")
            ]
            for sel in selectors_active:
                if sel.exists:
                    active_user = sel.get_text().strip()
                    if active_user:
                        break
            
            if active_user:
                if active_user.startswith('@'):
                    active_user = active_user[1:]
                print(f"      -> Akun aktif di {app_name}: @{active_user}")
                
            # Scrape stats untuk akun aktif pertama kali
            active_posts, active_followers = scrape_profile_stats(d, pkg)
            print(f"      -> Stats akun aktif (@{active_user}): posts={active_posts}, followers={active_followers}")
            
            scraped_accounts = {}
            if active_user:
                scraped_accounts[active_user] = {
                    "posts": active_posts,
                    "followers": active_followers
                }
                
            # 3. Buka Account Switcher Bottom Sheet
            print(f"      -> Membuka daftar switcher akun {app_name} dengan mengklik header...")
            opened = False
            for sel in selectors_active:
                if sel.exists:
                    print("         -> Mengklik header username...")
                    sel.click()
                    opened = True
                    break
            
            if not opened:
                print("         -> Mengklik koordinat area header username (fallback)...")
                d.click(int(width * 0.25), int(height * 0.07))
                opened = True
                
            # Tunggu 4 detik agar bottom sheet/switcher selesai meluncur ke atas
            time.sleep(4)

            # Fungsi pembantu untuk memvalidasi apakah sebuah kata adalah username Instagram riil
            def is_valid_username(word):
                word_lower = word.lower()
                
                # 1. Harus memenuhi kriteria format username (3-30 karakter: huruf, angka, titik, underscore)
                if not re.match(r'^[a-zA-Z0-9._]{3,30}$', word):
                    return False
                    
                # 2. Tidak boleh hanya berisi angka saja (misal: statistik angka "420" atau tahun "2026")
                if re.match(r'^\d+$', word):
                    return False
                    
                # 3. Mengabaikan format angka statistik seperti "3.1K", "10M", "5.5k"
                if re.match(r'^\d+(\.\d+)?[kmKM]$', word):
                    return False
                    
                # 4. Daftar kata-kata UI umum yang harus diabaikan (Blocklist Lengkap)
                blocklist = {
                    # Bahasa Inggris (UI Instagram)
                    "login", "logout", "signin", "signout", "cancel", "done", "edit", "search", 
                    "reels", "posts", "followers", "following", "profile", "home", "explore",
                    "activity", "messages", "settings", "about", "help", "language", "theme", 
                    "privacy", "security", "account", "accounts", "drafts", "saved", "close", "friends", 
                    "instagram", "threads", "highlights", "grid", "tag", "tagged", "mentions", 
                    "post", "like", "comment", "share", "video", "photo", "view", "views", 
                    "add", "create", "new", "switch", "choose", "select", "next", "back", 
                    "ok", "save", "delete", "remove", "archive", "notification", "notifications", 
                    "chat", "chats", "live", "igtv", "shop", "shopping", "store", "insights", 
                    "dashboard", "tools", "dismiss", "meta", "your", "center", "facebook",
                    
                    # Bahasa Indonesia (UI Instagram)
                    "batal", "selesai", "cari", "profil", "pesan", "notifikasi", "ditandai", 
                    "jelajahi", "notif", "suka", "komentar", "bagikan", "repost", "tambahkan", 
                    "tambah", "masuk", "daftar", "register", "buat", "baru", "sekarang", 
                    "aktif", "active", "kembali", "beranda", "postingan", "pengikut", "diikuti", 
                    "pengaturan", "arsip", "disimpan", "bantuan", "keluar", "laporkan", "salin", 
                    "tautan", "kirim", "berbagi", "menyukai", "mengomentari", "mengikuti",
                    "tutup", "buka", "logo", "foto", "gambar", "video", "audio", "klik", 
                    "konten", "aplikasi", "unduh", "ikuti", "lewatkan", "lewati"
                }
                
                if word_lower in blocklist:
                    return False
                    
                return True

            # 4. Scrape semua username di bottom sheet yang terbuka
            usernames = set()
            if active_user:
                usernames.add(active_user)
                
            # Ambil elemen HANYA dari dalam kontainer bottom sheet yang diberikan user
            print("      -> Membaca elemen dari kontainer bottom sheet presisi...")
            try:
                # 1. Coba cari di dalam kontainer FrameLayout bottom sheet presisi sesuai data dari perangkat user
                all_views = d.xpath('//*[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout//*[@text or @content-desc]').all()
                
                # 2. Fallback: Cari di dalam container bottom_sheet umum jika kontainer di atas tidak ditemukan
                if not all_views:
                    all_views = d.xpath('//*[contains(@resource-id, "bottom_sheet") or contains(@resource-id, "dialog")]//*[@text or @content-desc]').all()
                    
                # 3. Fallback Ekstrim: Jika tidak ada container, baru baca seluruh layar
                if not all_views:
                    all_views = d.xpath('//*[@text or @content-desc]').all()
                for el in all_views:
                    # Filter: Lewati jika element bagian dari bar navigasi / tab bar / status bar
                    res_id = (el.attrib.get('resource-id') or '').lower()
                    if any(x in res_id for x in ["tab", "navigation", "bar", "status_bar"]):
                        continue
                        
                    txt = (el.attrib.get('text') or '').strip()
                    desc = (el.attrib.get('content-desc') or '').strip()
                    
                    # Periksa keduanya (text dan description)
                    for val in [txt, desc]:
                        if not val:
                            continue
                        
                        # 1. Ambil kata pertama (untuk mengabaikan status/angka di belakang username)
                        words = val.split()
                        if not words:
                            continue
                        first_word = words[0]
                        
                        # 2. Bersihkan karakter '@' di awal
                        if first_word.startswith('@'):
                            first_word = first_word[1:]
                            
                        # 3. Validasi & Filter secara otomatis
                        if is_valid_username(first_word):
                            print(f"         [DETECTED] Menemukan username: '{first_word}' (sumber: '{val}')")
                            usernames.add(first_word)
            except Exception as e:
                print(f"      -> Gagal membaca XPath: {e}")
                
            # 5. Menutup account switcher tanpa berpindah akun agar akun aktif di HP tidak berubah
            print("      -> Menutup account switcher tanpa berpindah akun...")
            d.press("back")
            time.sleep(1.5)
                            
            for u in usernames:
                formatted_u = f"@{u}" if not u.startswith("@") else u
                stats = scraped_accounts.get(u, {"posts": "0", "followers": "0"})
                scraped_results.append({
                    "app": app_name,
                    "username": formatted_u,
                    "posts": stats["posts"],
                    "followers": stats["followers"]
                })
                
            print(f"      -> Akun berhasil dipindai pada {app_name}: {list(usernames)}")
            
            # Tutup aplikasi
            d.app_stop(pkg)
            time.sleep(1)
            
        print(f"[3] Pemindaian seluruh aplikasi selesai. Hasil: {scraped_results}")
        print(f"__SCAN_RESULT__:{json.dumps(scraped_results)}")
        return scraped_results
        
    except Exception as e:
        print(f"ERROR SCANNING: {e}")
        print("__SCAN_RESULT__:[]")
        return []

if __name__ == "__main__":
    device_id = sys.argv[1] if len(sys.argv) > 1 else "all"
    scan_accounts(device_id)
