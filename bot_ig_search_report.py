import uiautomator2 as u2
import time
import random

print("Menghubungkan ke HP Android via UiAutomator2...")
d = u2.connect()
print(f"Terhubung ke perangkat: {d.device_info['brand']} {d.device_info['model']}")

username_target = input("Masukkan username yang ingin di-report: ").strip()

def klik_kembali():
    if d(resourceId="com.instagram.android:id/left_action_bar_buttons").exists:
        d(resourceId="com.instagram.android:id/left_action_bar_buttons").click()
        time.sleep(random.uniform(1.0, 2.0))
    elif d(resourceId="com.instagram.android:id/action_bar_button_back").exists:
        d(resourceId="com.instagram.android:id/action_bar_button_back").click()
        time.sleep(random.uniform(1.0, 2.0))
    else:
        d.press("back")
        time.sleep(random.uniform(1.0, 2.0))

print("\n--- TAHAP 1: BUKA INSTAGRAM ---")
d.press("home")
time.sleep(1.5)
d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.2)
time.sleep(2)

if d(text="Instagram").exists:
    d(text="Instagram").click()
else:
    d.swipe(0.8, 0.5, 0.2, 0.5, duration=0.2)
    time.sleep(1)
    d(text="Instagram").click()

print("Menunggu Instagram terbuka...")
time.sleep(random.uniform(5.0, 7.0))

print("\n--- TAHAP 2: CARI USERNAME ---")
print(f"Mencari user: {username_target}")
if d(resourceId="com.instagram.android:id/search_tab").exists:
    d(resourceId="com.instagram.android:id/search_tab").click()
elif d(descriptionContains="Cari").exists:
    d(descriptionContains="Cari").click()
elif d(descriptionContains="Search").exists:
    d(descriptionContains="Search").click()
elif d(descriptionContains="Cari dan Jelajahi").exists:
    d(descriptionContains="Cari dan Jelajahi").click()
elif d(descriptionContains="Search and Explore").exists:
    d(descriptionContains="Search and Explore").click()
elif d(className="android.widget.ImageView", description=True).exists:
    els = d(className="android.widget.ImageView")
    for el in els:
        desc = el.info.get('contentDescription', '') or ''
        if 'cari' in desc.lower() or 'search' in desc.lower():
            el.click()
            break
    else:
        d.click(0.065, 0.060)
else:
    d.click(0.065, 0.060)
time.sleep(random.uniform(2.0, 4.0))

print("Mengklik kolom search...")
if d(resourceId="com.instagram.android:id/action_bar_search_edit_text").exists:
    d(resourceId="com.instagram.android:id/action_bar_search_edit_text").click()
elif d(resourceId="com.instagram.android:id/search_bar").exists:
    d(resourceId="com.instagram.android:id/search_bar").click()
else:
    d.click(0.5, 0.070)
time.sleep(1)

print("Membersihkan kolom search...")
try:
    d(resourceId="com.instagram.android:id/action_bar_search_edit_text").clear_text()
except:
    d.press("del")
time.sleep(0.5)

print(f"Mengetik username: {username_target}")
d.send_keys(username_target)
time.sleep(1)

print("Menunggu hasil pencarian muncul...")
for _ in range(8):
    if d(text=username_target).exists() or d(textContains=username_target).exists():
        break
    d.press("search")
    time.sleep(1)
    if d(text="Search").exists():
        d(text="Search").click()
        time.sleep(1)
        break
    d.press("enter")
    time.sleep(1)

print(f"Mengklik profil @{username_target}...")
if d(text=username_target).exists():
    d(text=username_target).click()
    print("  Klik via text exact match")
elif d(textContains=username_target).exists():
    d(textContains=username_target).click()
    print("  Klik via textContains")
elif d(resourceId="com.instagram.android:id/row_search_user_container").exists():
    d(resourceId="com.instagram.android:id/row_search_user_container").click()
    print("  Klik via row_search_user_container")
else:
    try:
        for el in d(className="android.widget.LinearLayout"):
            try:
                teks_dalam = el.info.get('text', '') or ''
                if not teks_dalam:
                    for child in el.child():
                        t = child.info.get('text', '') or ''
                        if t.strip():
                            teks_dalam += t + ' '
                if username_target.lower() in teks_dalam.lower():
                    el.click()
                    print("  Klik via LinearLayout berisi username")
                    break
            except:
                continue
        else:
            raise Exception
    except:
        if d(resourceId="com.instagram.android:id/search_results_recycler_view").exists():
            items = d(resourceId="com.instagram.android:id/search_results_recycler_view").child()
            if items and len(items) > 0:
                items[0].click()
                print("  Klik item pertama dari recycler view")
        else:
            d.click(0.3, 0.3)
            print("  Fallback: klik koordinat")
time.sleep(random.uniform(3.0, 4.0))

print("\n--- TAHAP 3: BUKA MENU OPSI ---")
print("Mengklik ikon titik 3 (Menu Opsi)...")
if d(descriptionContains="Opsi").exists:
    d(descriptionContains="Opsi").click()
elif d(descriptionContains="Options").exists:
    d(descriptionContains="Options").click()
elif d(resourceId="com.instagram.android:id/profile_header_actions_top_container").exists:
    d(resourceId="com.instagram.android:id/profile_header_actions_top_container").click()
else:
    d.click(0.935, 0.054)
time.sleep(random.uniform(2.0, 4.0))

print("\n--- TAHAP 4: KLIK 'LAPORKAN' ---")
if d(textContains="Laporkan").exists:
    d(textContains="Laporkan").click()
elif d(textContains="Report").exists:
    d(textContains="Report").click()
elif d(descriptionContains="Laporkan").exists:
    d(descriptionContains="Laporkan").click()
elif d(descriptionContains="Report").exists:
    d(descriptionContains="Report").click()
else:
    ditemukan = False
    for cls in ["android.widget.TextView", "android.widget.Button"]:
        for el in d(className=cls):
            try:
                txt = el.info.get('text', '') or el.info.get('contentDescription', '')
                if 'lapor' in txt.lower() or 'report' in txt.lower():
                    print(f"  Ditemukan via className '{cls}': '{txt}'")
                    el.click()
                    ditemukan = True
                    break
            except:
                pass
        if ditemukan:
            break
    if not ditemukan:
        d.click(0.5, 0.6)
time.sleep(random.uniform(3.0, 5.0))

print("\n--- TAHAP 5: NAVIGASI REPORT (PILIH ALASAN & DETAIL) ---")
time.sleep(random.uniform(3.0, 5.0))

def teks_di_layar():
    hasil = []
    try:
        for el in d(className="android.widget.TextView"):
            txt = el.info.get('text', '') or ''
            if txt.strip():
                hasil.append(txt.strip())
    except:
        pass
    return hasil

def opsi_dapat_diklik():
    try:
        y_layar = d.window_size()[1]
        opsi_list = []
        for el in d(className="android.widget.TextView"):
            b = el.info.get('bounds')
            if b:
                y = (b['top'] + b['bottom']) // 2
                if y > y_layar * 0.15 and y < y_layar * 0.85:
                    teks = el.info.get('text', '') or ''
                    if teks.strip():
                        opsi_list.append((el, teks.strip(), y))
        return opsi_list
    except:
        return []

def klik_konfirmasi():
    for kw in ["Ya, laporkan", "Kirim laporan", "Kirim", "Send", "Submit",
                "Berikutnya", "Lanjutkan", "Next", "Continue", "Paham",
                "OK", "Baik", "Oke", "Selesai", "Done", "Tutup", "Close"]:
        for selector in [
            (d(textContains=kw), "text"),
            (d(descriptionContains=kw), "desc"),
        ]:
            if selector[0].exists:
                print(f"  [KONFIRMASI] Klik: '{kw}' via {selector[1]}")
                selector[0].click()
                return True
    return False

semua_teks = teks_di_layar()
print(f"  [DEBUG] Teks di layar: {semua_teks}")
opsi_sudah_diklik = set()
teks_sebelumnya = set(semua_teks)
langkah_kosong = 0

for _ in range(30):
    time.sleep(random.uniform(2.0, 4.0))
    semua_teks = teks_di_layar()
    teks_sekarang = set(semua_teks)
    print(f"  [DEBUG] Teks di layar: {semua_teks}")

    if klik_konfirmasi():
        langkah_kosong = 0
        continue

    if teks_sekarang and teks_sekarang != teks_sebelumnya:
        print("  [LAYAR] Konten berubah, reset daftar opsi yang sudah diklik")
        opsi_sudah_diklik.clear()
        teks_sebelumnya = teks_sekarang

    try:
        y_layar = d.window_size()[1]
        gambar_di_tengah = []
        for el in d(className="android.widget.ImageView"):
            b = el.info.get('bounds')
            if b:
                y = (b['top'] + b['bottom']) // 2
                w = b['right'] - b['left']
                if y > y_layar * 0.25 and y < y_layar * 0.75 and w < y_layar * 0.4:
                    gambar_di_tengah.append(el)
        if len(gambar_di_tengah) >= 3:
            acak = random.choice(gambar_di_tengah)
            print(f"  [GRID] Klik postingan (1/{len(gambar_di_tengah)})")
            acak.click()
            langkah_kosong = 0
            continue
    except:
        pass

    opsi = opsi_dapat_diklik()
    opsi_filter = []
    for el, teks, y in opsi:
        if teks in opsi_sudah_diklik:
            continue
        if any(kw in teks.lower() for kw in ["batal", "cancel", "kembali", "back"]):
            continue
        if len(teks) <= 2:
            continue
        opsi_filter.append((el, teks, y))

    if opsi_filter:
        opsi_filter.sort(key=lambda x: x[2])
        print(f"  [OPSI] Ditemukan {len(opsi_filter)} opsi:")
        for _, teks, y in opsi_filter:
            print(f"         - '{teks}' (y={y})")

        el, teks, y = opsi_filter[0]
        print(f"  [PIlih] Klik: '{teks}'")
        el.click()
        opsi_sudah_diklik.add(teks)
        langkah_kosong = 0
    else:
        langkah_kosong += 1
        print("  [OPSI] Tidak ada opsi baru yang bisa diklik")

    print(f"  Langkah kosong: {langkah_kosong}/5")
    if langkah_kosong >= 5:
        print("  Fallback klik tengah layar...")
        d.click(0.5, 0.5)
        time.sleep(random.uniform(1.5, 3.0))
        if langkah_kosong >= 7:
            break

print("  [OK] Navigasi report selesai")

print("\n--- TAHAP 6: KEMBALI KE BERANDA ---")
for _ in range(3):
    klik_kembali()
    time.sleep(1)

if d(resourceId="com.instagram.android:id/home_tab").exists:
    d(resourceId="com.instagram.android:id/home_tab").click()
elif d(descriptionContains="Beranda").exists:
    d(descriptionContains="Beranda").click()
elif d(descriptionContains="Home").exists:
    d(descriptionContains="Home").click()
else:
    d.click(0.5, 0.922)
time.sleep(3)

print("\n========================================================")
print(f"PROSES REPORT SELESAI! User @{username_target} telah di-report.")
print("   Laporan telah dikirim ke Instagram.")
print("========================================================")
