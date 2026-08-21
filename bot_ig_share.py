import sys
import uiautomator2 as u2
import time
import re
from ig_helpers import connect_adb, open_instagram

def bot_share(target_user, tujuan_share):
    try:
        print("=========================================")
        print(f" JALANKAN BOT SHARE")
        print(f" Target: @{target_user} -> Share ke: @{tujuan_share}")
        print("=========================================")

        device_pilihan = sys.argv[3] if len(sys.argv) > 3 else "all"

        d = connect_adb(device_pilihan, action=None, step_label="[1] Menghubungkan ke perangkat Android...")
        width, height = d.window_size()

        open_instagram(d, device_pilihan, action=None, delay=6, step_label="[2] Membuka aplikasi Instagram...")

        print(f"[3] Mencari profil target: @{target_user}...")
        if d(resourceId="com.instagram.android:id/search_tab").exists:
            d(resourceId="com.instagram.android:id/search_tab").click()
        elif d(descriptionContains="Cari").exists:
            d(descriptionContains="Cari").click()
        elif d(descriptionContains="Search").exists:
            d(descriptionContains="Search").click()
        else:
            d.click(int(width * 0.30), int(height * 0.96))
        time.sleep(4)

        print("      Mengklik kotak input pencarian...")
        if d(resourceId="com.instagram.android:id/action_bar_search_edit_text").exists:
            d(resourceId="com.instagram.android:id/action_bar_search_edit_text").click()
        elif d(resourceId="com.instagram.android:id/search_bar").exists:
            d(resourceId="com.instagram.android:id/search_bar").click()
        elif d(className="android.widget.EditText").exists:
            d(className="android.widget.EditText").click()
        else:
            d.click(int(width * 0.5), int(height * 0.06))
        time.sleep(2)

        print(f"      Mengetik nama akun: {target_user}")
        try:
            if d(resourceId="com.instagram.android:id/action_bar_search_edit_text").exists:
                d(resourceId="com.instagram.android:id/action_bar_search_edit_text").clear_text()
            elif d(className="android.widget.EditText").exists:
                d(className="android.widget.EditText").clear_text()
        except:
            pass
        d.send_keys(target_user)
        time.sleep(3)

        d.press("enter")
        time.sleep(4)

        print("      Memilih profil teratas...")
        akun_target_text = d(text=target_user, className="android.widget.TextView")
        akun_target_contains = d(textContains=target_user, className="android.widget.TextView")
        if akun_target_text.exists:
            akun_target_text.click()
        elif akun_target_contains.exists:
            akun_target_contains.click()
        elif d(resourceId="com.instagram.android:id/row_search_user_info_container").exists:
            d(resourceId="com.instagram.android:id/row_search_user_info_container").click()
        elif d(resourceId="com.instagram.android:id/row_search_user_container").exists:
            d(resourceId="com.instagram.android:id/row_search_user_container").click()
        else:
            d.click(int(width * 0.5), int(height * 0.24))
        time.sleep(5)

        print("[4] Membuka postingan teratas target...")
        post_clicked = False
        
        # JALANKAN PROSES SEARCH DALAM SATU RPC CALL VIA XPATH (Sangat Cepat!)
        print("      -> Mendapatkan daftar postingan via XPath...")
        try:
            image_views = d.xpath('//android.widget.ImageView').all()
            candidate_posts = []
            
            # 1. Coba cari berdasarkan deskripsi konten terlebih dahulu
            for el in image_views:
                desc = el.attrib.get('content-desc', '') or ''
                # Ambil bounds koordinat
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
                    x_center = (bounds['left'] + bounds['right']) // 2
                    y_center = (bounds['top'] + bounds['bottom']) // 2
                    el_width = bounds['right'] - bounds['left']
                    
                    # Validasi deskripsi postingan (bahasa Indonesia / Inggris)
                    is_post_desc = any(p in desc for p in ["Foto oleh", "Photo by", "Video oleh", "Video by", "Postingan oleh", "Post oleh", "Media oleh"])
                    
                    if is_post_desc and int(height * 0.35) < y_center < int(height * 0.90) and el_width > int(width * 0.28):
                        print(f"      -> Menemukan postingan terbaru via deskripsi: '{desc}' pada koordinat ({x_center}, {y_center})")
                        el.click()
                        post_clicked = True
                        break
                        
                    # Simpan sebagai kandidat kolom pertama jika deskripsi kosong/tidak cocok
                    if 0 < x_center < int(width * 0.35) and int(height * 0.35) < y_center < int(height * 0.90) and el_width > int(width * 0.28):
                        candidate_posts.append((y_center, el, x_center, y_center))
            
            # 2. Jika tidak ada yang cocok via deskripsi, klik kandidat gambar teratas di kolom pertama
            if not post_clicked and candidate_posts:
                candidate_posts.sort(key=lambda x: x[0])
                target_el = candidate_posts[0][1]
                target_x = candidate_posts[0][2]
                target_y = candidate_posts[0][3]
                print(f"      -> Deskripsi tidak cocok, mengklik ImageView teratas di kolom pertama pada ({target_x}, {target_y})")
                target_el.click()
                post_clicked = True
                
        except Exception as e:
            print(f"      -> Gagal memproses XPath: {e}")
            
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
            # Koordinat A (tanpa sorotan/bio pendek): sekitar y = 0.55
            # Koordinat B (dengan sorotan/bio panjang): sekitar y = 0.74
            print("      -> Menggunakan koordinat presisi fallback pertama (tanpa sorotan)...")
            d.click(int(width * 0.168), int(height * 0.55))
            time.sleep(2)
            print("      -> Menggunakan koordinat presisi fallback kedua (dengan sorotan)...")
            d.click(int(width * 0.168), int(height * 0.741))
            post_clicked = True
            
        time.sleep(4)

        print("[5] Klik ikon pesawat (Share/DM)...")
        share_clicked = False
        for desc in ["Kirim", "Send", "Share"]:
            el = d(descriptionContains=desc)
            if el.exists:
                el.click()
                share_clicked = True
                print(f"      -> Klik share via description: {desc}")
                break
        if not share_clicked:
            if d(resourceId="com.instagram.android:id/row_feed_button_share").exists:
                d(resourceId="com.instagram.android:id/row_feed_button_share").click()
                share_clicked = True
            elif d(resourceId="com.instagram.android:id/direct_share_send_to_container").exists:
                print("      -> Form share sudah terbuka")
                share_clicked = True
            else:
                d.click(int(width * 0.89), int(height * 0.65))
        time.sleep(3)

        print(f"[6] Mencari tujuan share: @{tujuan_share}...")
        search_field = None
        if d(resourceId="com.instagram.android:id/direct_share_search_edit_text").exists:
            search_field = d(resourceId="com.instagram.android:id/direct_share_search_edit_text")
        elif d(resourceId="com.instagram.android:id/recipients_search_edit_text").exists:
            search_field = d(resourceId="com.instagram.android:id/recipients_search_edit_text")
        elif d(className="android.widget.EditText").exists:
            search_field = d(className="android.widget.EditText")

        if search_field:
            search_field.click()
            time.sleep(1)
            try:
                search_field.clear_text()
            except:
                pass
            search_field.set_text(tujuan_share)
            print("      -> Mengetik tujuan share")
        else:
            d.click(int(width * 0.3), int(height * 0.1))
            time.sleep(1)
            d.send_keys(tujuan_share)
        time.sleep(3)

        print("      Memilih kontak hasil pencarian...")
        tujuan_text = d(text=tujuan_share, className="android.widget.TextView")
        tujuan_contains = d(textContains=tujuan_share, className="android.widget.TextView")
        if tujuan_text.exists:
            tujuan_text.click()
        elif tujuan_contains.exists:
            tujuan_contains.click()
        elif d(resourceId="com.instagram.android:id/row_search_user_info_container").exists:
            d(resourceId="com.instagram.android:id/row_search_user_info_container").click()
        else:
            d.click(int(width * 0.3), int(height * 0.18))
        time.sleep(2)

        print("[7] Mengirim (Send)...")
        if d(resourceId="com.instagram.android:id/direct_share_send_button").exists:
            d(resourceId="com.instagram.android:id/direct_share_send_button").click()
        elif d(text="Kirim").exists:
            d(text="Kirim").click()
        elif d(text="Send").exists:
            d(text="Send").click()
        elif d(description="Kirim").exists:
            d(description="Kirim").click()
        else:
            d.click(int(width * 0.89), int(height * 0.95))
        time.sleep(4)

        # Langkah 1: Tekan back 3 kali secara fisik untuk keluar dari Post Detail, Profile Target, dan Hasil Pencarian
        # Ini memastikan kita sudah keluar dari sub-halaman sehingga tab bar bawah aktif dan tidak tertutup fragment profil
        print("      -> Mundur dari postingan detail ke profil...")
        d.press("back")
        time.sleep(2)
        
        print("      -> Mundur dari profil target ke hasil pencarian...")
        d.press("back")
        time.sleep(2)
        
        print("      -> Mundur dari hasil pencarian ke pencarian utama...")
        d.press("back")
        time.sleep(2)

        # Langkah 2: Klik tab Beranda (Home) di pojok kiri bawah untuk kembali ke Feed utama
        home_clicked = False
        for i in range(3):
            # Prioritaskan mencari tombol Beranda via elemen/ikon (Sangat Robust untuk berbagai HP)
            btn_home = None
            for rid in ["com.instagram.android:id/feed_tab", "com.instagram.android:id/home_tab"]:
                if d(resourceId=rid).exists:
                    btn_home = d(resourceId=rid)
                    break
            
            if not btn_home:
                for desc in ["Beranda", "Home", "Feed"]:
                    if d(descriptionContains=desc).exists:
                        btn_home = d(descriptionContains=desc)
                        break

            # Eksekusi klik pada ikon jika ditemukan
            if btn_home:
                print("      -> Menemukan ikon Beranda. Mengklik via elemen fisik (Aman & Akurat)...")
                try:
                    btn_home.click()
                    time.sleep(1.5)
                    home_clicked = True
                    break
                except Exception as e:
                    print(f"      -> Gagal klik via elemen: {e}, mencoba alternatif...")

            # Jika deteksi elemen gagal, gunakan fallback koordinat presisi (sebagai jaring pengaman terakhir)
            if (d(resourceId="com.instagram.android:id/feed_tab").exists or \
                d(resourceId="com.instagram.android:id/home_tab").exists or \
                d(descriptionContains="Beranda").exists or \
                d(descriptionContains="Home").exists):
                
                print("      -> Mengklik Beranda via koordinat fallback (0.095, 0.918)...")
                d.click(int(width * 0.095), int(height * 0.918))
                time.sleep(1.5)
                home_clicked = True
                break
            else:
                print(f"      -> Tab Beranda tidak terlihat, mencoba kembali (percobaan {i+1})...")
                d.press("back")
                time.sleep(2)

        if not home_clicked:
            # Fallback koordinat terakhir jika semuanya tidak terdeteksi
            print("      -> Mengklik tab Beranda via koordinat fallback terakhir...")
            d.click(int(width * 0.095), int(height * 0.918))
            time.sleep(3)

        print("=========================================")
        print(f" SHARE BERHASIL: @{target_user} -> @{tujuan_share}")
        print("=========================================\n")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else ""
    tujuan = sys.argv[2] if len(sys.argv) > 2 else ""
    bot_share(target, tujuan)
