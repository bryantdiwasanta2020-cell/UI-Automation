import sys
import time
import re
import uiautomator2 as u2
from ig_helpers import connect_adb, open_instagram

def find_element_by_text_or_desc(d, text_val, contains=False, regex=False):
    # Helper to find elements
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

def is_valid_username(txt):
    txt = txt.strip()
    if not txt:
        return False
    # Username Instagram: 1-30 karakter, hanya huruf, angka, titik, dan garis bawah
    if not re.match(r"^[a-zA-Z0-9._]{1,30}$", txt):
        return False
    # Harus mengandung minimal 1 huruf (Instagram tidak mengizinkan username angka saja)
    if not any(c.isalpha() for c in txt):
        return False
    return True

def check_logged_in_accounts(device_id="all"):
    print("=========================================")
    print(" MEMERIKSA JUMLAH AKUN INSTAGRAM DI DEVICE")
    print(f" Perangkat: {device_id}")
    print("=========================================")

    # 1. Hubungkan ke perangkat
    try:
        d = connect_adb(device_id, action="check_accounts", step_label="[1] Menghubungkan ke perangkat Android...")
    except Exception as e:
        print(f"[-] Gagal menghubungkan ke perangkat: {e}")
        sys.exit(1)

    width, height = d.window_size()

    # Pastikan layar menyala & tidak terkunci
    try:
        d.screen_on()
        d.unlock()
        time.sleep(1.0)
    except:
        pass

    # 2. Pastikan Instagram terbuka
    print("[2] Membuka aplikasi Instagram...")
    try:
        if d.app_current().get("package") != "com.instagram.android":
            d.app_start("com.instagram.android")
            time.sleep(4.0)
    except Exception as e:
        print(f"[-] Gagal membuka Instagram: {e}")
        sys.exit(1)

    # Ambil layout hirarki halaman XML untuk deteksi login status
    try:
        xml_src = d.dump_hierarchy()
    except Exception as e:
        print(f"[-] Gagal membaca layout layar: {e}")
        sys.exit(1)

    xml_lower = xml_src.lower()

    # Identifikasi keadaan layar (Login vs Logout)
    is_logged_in = "feed_tab" in xml_lower or "profile_tab" in xml_lower
    accounts_found = []

    # Daftar keyword bawaan Instagram yang harus diabaikan
    ignore_keywords = [
        "tambahkan akun", "tambah akun", "add account", "log in", "masuk", "buat", "create", "threads",
        "existing", "sudah ada", "akun lama", "akun lain", "another account",
        "log into", "log out", "keluar", "security", "keamanan", "pilih", "choose",
        "lanjutkan", "continue", "profile", "profil", "tentang", "about",
        "pengaturan", "settings", "bantuan", "help", "posts", "post", "follower", 
        "followers", "following", "follow", "edit profile", "edit", "message", 
        "contact", "insights", "share", "grid", "tagged", "reels", "home", "share profile",
        "search", "explore", "activity", "recent", "dismiss", "add instagram account", "add banner",
        "go to meta account settings", "meta logo", "cancel", "batal", "sign up", "daftar", "back", "back to home", "back to top",
    ]

    if is_logged_in:
        print("[3] Terdeteksi status: LOGGED_IN (Sedang login)")
        
        # Buka tab profil terlebih dahulu agar aman
        print("   -> Membuka halaman profil...")
        profile_tab = d(resourceId="com.instagram.android:id/profile_tab")
        if profile_tab.exists:
            profile_tab.click()
        else:
            d.click(int(width * 0.9), int(height * 0.93))
        time.sleep(3.0)
        
        print("[4] Membuka Account Switcher...")
        # Lakukan long click pada tab profil untuk membuka switcher secara konsisten
        profile_tab = d(resourceId="com.instagram.android:id/profile_tab")
        if profile_tab.exists:
            profile_tab.long_click()
        else:
            d.click(int(width * 0.9), int(height * 0.93))
            time.sleep(0.5)
            d.long_click(int(width * 0.9), int(height * 0.93), duration=1.0)
        time.sleep(3.5)

        # Dump layout hierarchy saat switcher terbuka
        try:
            xml_src = d.dump_hierarchy()
        except Exception as e:
            print(f"[-] Gagal membaca layout switcher: {e}")
            d.press("back")
            sys.exit(1)

        # Cari semua elemen teks dalam switcher secara dinamis dari semua jenis class (TextView, View, Button, dll.)
        from xml.etree import ElementTree as ET
        try:
            root = ET.fromstring(xml_src.encode('utf-8'))
            all_nodes = root.findall(".//node")
            
            for node in all_nodes:
                txt = node.attrib.get("text", "").strip()
                if not txt:
                    # Ambil dari content-desc jika text kosong (Instagram view sering menggunakan desc)
                    txt = node.attrib.get("content-desc", "").strip()
                if not txt:
                    continue
                
                txt_lower = txt.lower()
                # Saring keyword menu bawaan
                if any(kw in txt_lower for kw in ignore_keywords):
                    continue
                
                if is_valid_username(txt):
                    if txt not in accounts_found:
                        accounts_found.append(txt)
        except Exception as parser_err:
            print(f"[-] Warning parsing XML: {parser_err}")

        # Tutup switcher secara aman dengan menekan BACK
        print("[5] Menutup Account Switcher...")
        d.press("back")
        time.sleep(1.5)

    else:
        # Layar logged out / Saved accounts
        print("[3] Terdeteksi status: LOGGED_OUT (Belum login / Layar pemilihan akun)")
        
        # Cari semua elemen teks dalam layar saved accounts secara dinamis
        from xml.etree import ElementTree as ET
        try:
            root = ET.fromstring(xml_src.encode('utf-8'))
            all_nodes = root.findall(".//node")
            
            for node in all_nodes:
                txt = node.attrib.get("text", "").strip()
                if not txt:
                    txt = node.attrib.get("content-desc", "").strip()
                if not txt:
                    continue
                
                txt_lower = txt.lower()
                if any(kw in txt_lower for kw in ignore_keywords):
                    continue
                if is_valid_username(txt):
                    if txt not in accounts_found:
                        accounts_found.append(txt)
        except Exception as parser_err:
            print(f"[-] Warning parsing XML: {parser_err}")

    # Cetak hasil
    print("\n-----------------------------------------")
    print("Hasil Pemindaian Akun Instagram:")
    print(f"Jumlah Akun Terdeteksi: {len(accounts_found)} Akun")
    if accounts_found:
        print("Daftar Akun:")
        for idx, acc in enumerate(accounts_found, 1):
            print(f" {idx}. {acc}")
    else:
        print(" (Tidak ada akun tersimpan atau terdeteksi di layar)")
    print("-----------------------------------------")
    print("[SELESAI] Pemeriksaan akun selesai secara aman.\n")

if __name__ == "__main__":
    device_id = "all"
    if len(sys.argv) > 1:
        device_id = sys.argv[1]
    
    check_logged_in_accounts(device_id)
