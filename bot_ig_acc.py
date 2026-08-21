import uiautomator2 as u2
import time
import random
from ig_helpers import connect_adb

def konfirmasi_permintaan_follow():
    try:
        # 1. Koneksi ke perangkat Android
        d = connect_adb()
        print(f"Terhubung ke perangkat: {d.device_info['brand']} {d.device_info['model']}")

        # 2. Buka aplikasi Instagram
        package_name = "com.instagram.android"
        print("Membuka aplikasi Instagram...")
        d.app_start(package_name)
        time.sleep(5)  # Tunggu aplikasi terbuka sepenuhnya

        # 3. Masuk ke halaman Notifikasi (Lonceng/Notification)
        print("Mencoba membuka halaman Notifikasi...")
        xpath_notif = '//*[@resource-id="com.instagram.android:id/notification"]/android.view.ViewGroup[1]'
        
        if d.xpath(xpath_notif).exists:
            print("Mengklik ikon Notifikasi via XPath...")
            d.xpath(xpath_notif).click()
        elif d(resourceId="com.instagram.android:id/notification").exists:
            print("Mengklik ikon Notifikasi via resourceId...")
            d(resourceId="com.instagram.android:id/notification").click()
        elif d(descriptionContains="Notifikasi").exists:
            print("Mengklik ikon Notifikasi via description 'Notifikasi'...")
            d(descriptionContains="Notifikasi").click()
        elif d(descriptionContains="Notification").exists:
            print("Mengklik ikon Notifikasi via description 'Notification'...")
            d(descriptionContains="Notification").click()
        else:
            # Fallback klik menggunakan koordinat perkiraan di kanan atas layar
            print("Mengklik ikon Notifikasi via koordinat kalibrasi (0.94, 0.054)...")
            d.click(0.94, 0.054)
            
        time.sleep(4)  # Tunggu halaman notifikasi memuat

        # 4. Masuk ke "Permintaan Mengikuti" (Follow Requests)
        print("Mencari baris 'Permintaan Mengikuti'...")
        menemukan_permintaan = False
        
        # Cara 1: Cari berdasarkan Teks
        kata_kunci_permintaan = ["permintaan mengikuti", "follow requests", "permintaan", "requests"]
        for kata in kata_kunci_permintaan:
            el = d(textContains=kata)
            if el.exists:
                info = el.info
                txt = info.get('text', '')
                print(f"Menemukan menu berdasarkan teks: '{txt}'. Mengklik...")
                el.click()
                menemukan_permintaan = True
                break

        # Cara 2: Jika tidak ketemu via teks, cari berdasarkan resourceId / XPath yang diberikan user
        if not menemukan_permintaan:
            id_story_row = "com.instagram.android:id/activity_feed_newsfeed_story_row"
            id_story_row_short = "activity_feed_newsfeed_story_row"
            xpath_first_view = '//*[@resource-id="activity_feed_list"]/android.view.View[1]'

            if d(resourceId=id_story_row).exists:
                print("Mengklik baris permintaan mengikuti via resourceId (full)...")
                d(resourceId=id_story_row).click()
                menemukan_permintaan = True
            elif d(resourceId=id_story_row_short).exists:
                print("Mengklik baris permintaan mengikuti via resourceId (short)...")
                d(resourceId=id_story_row_short).click()
                menemukan_permintaan = True
            elif d.xpath(xpath_first_view).exists:
                print("Mengklik baris pertama di activity feed via XPath...")
                d.xpath(xpath_first_view).click()
                menemukan_permintaan = True

        # Cara 3: Fallback ke koordinat yang diberikan user (0.654, 0.136)
        if not menemukan_permintaan:
            print("Mencoba mengklik baris permintaan mengikuti via koordinat (0.654, 0.136)...")
            d.click(0.654, 0.136)
            menemukan_permintaan = True

        time.sleep(3)  # Tunggu halaman permintaan memuat

        # 5. Mulai proses konfirmasi permintaan
        print("\n[START] Memulai proses konfirmasi otomatis...")
        sudah_diklik_koordinat = set()
        tidak_ada_perubahan_scroll = 0
        max_scroll_tanpa_perubahan = 10
        total_dikonfirmasi = 0

        # Mendapatkan ukuran layar untuk scroll
        screen_size = d.window_size()
        width = screen_size[0]
        height = screen_size[1]

        # Batasan area klik agar tidak mengklik bagian header/footer
        y_min = int(height * 0.15)
        y_max = int(height * 0.85)

        while tidak_ada_perubahan_scroll < max_scroll_tanpa_perubahan:
            print("\nMencari tombol Konfirmasi di layar saat ini...")
            
            # Ambil semua button di layar
            buttons = d(className="android.widget.Button")
            tombol_diklik_di_layar_ini = 0

            for btn in buttons:
                try:
                    if not btn.exists:
                        continue

                    # Ambil informasi tombol dari .info
                    info = btn.info
                    txt = info.get('text', '')
                    desc = info.get('contentDescription', '')

                    txt_lower = txt.lower() if txt else ""
                    desc_lower = desc.lower() if desc else ""

                    # Ambil koordinat tombol
                    bounds = info.get('bounds', {})
                    if not bounds:
                        continue

                    x = (bounds['left'] + bounds['right']) // 2
                    y = (bounds['top'] + bounds['bottom']) // 2
                    koordinat = (x, y)

                    # Hitung ukuran tombol
                    btn_width = bounds['right'] - bounds['left']
                    btn_height = bounds['bottom'] - bounds['top']

                    # Pastikan tombol berada di area tengah layar (bukan header/footer)
                    if not (y_min <= y <= y_max):
                        continue

                    is_confirm_btn = False

                    # Deteksi tombol "Konfirmasi", "Konfirmasikan", "Confirm", "Accept", atau "Setuju"
                    keywords_confirm = ["konfirmasi", "confirm", "setuju", "accept", "approve"]
                    for kw in keywords_confirm:
                        if kw in txt_lower or kw in desc_lower:
                            is_confirm_btn = True
                            break

                    # Jika tombol kosong (tanpa teks/desc), pastikan berbentuk persegi panjang (lebar > tinggi)
                    # Ini sebagai fallback jika tombol konfirmasi di versi IG tersebut berupa tombol grafis tanpa teks
                    if txt == "" and desc == "" and btn_width > btn_height * 1.5:
                        is_confirm_btn = True

                    # Jika itu tombol konfirmasi dan belum pernah diklik di sesi ini
                    if is_confirm_btn and koordinat not in sudah_diklik_koordinat:
                        print(f"Mengklik tombol Konfirmasi di koordinat {koordinat} (Teks: '{txt}', Desc: '{desc}')")
                        btn.click()
                        
                        sudah_diklik_koordinat.add(koordinat)
                        tombol_diklik_di_layar_ini += 1
                        total_dikonfirmasi += 1
                        
                        # Jeda acak 2-4 detik agar tidak terdeteksi spam/bot
                        jeda = random.uniform(2.0, 4.0)
                        time.sleep(jeda)
                except Exception:
                    continue

            # Melakukan scroll ke bawah untuk memuat konten/permintaan baru
            print("Melakukan scroll ke bawah...")
            d.swipe(width // 2, int(height * 0.8), width // 2, int(height * 0.2), duration=0.5)
            time.sleep(3.0)  # Tunggu konten memuat setelah scroll

            if tombol_diklik_di_layar_ini == 0:
                tidak_ada_perubahan_scroll += 1
                print(f"Tidak menemukan tombol konfirmasi baru (Percobaan scroll kosong: {tidak_ada_perubahan_scroll}/{max_scroll_tanpa_perubahan})")
            else:
                tidak_ada_perubahan_scroll = 0

        print(f"\n[SELESAI] Proses selesai! Total permintaan dikonfirmasi: {total_dikonfirmasi}")

    except Exception as e:
        print(f"Terjadi kesalahan utama: {e}")

if __name__ == "__main__":
    konfirmasi_permintaan_follow()
