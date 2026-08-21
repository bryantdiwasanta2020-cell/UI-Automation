import sys
import uiautomator2 as u2
import time
import random
from ig_helpers import connect_adb

def bot_manage(target_user, aksi, device_pilihan="all"):
    try:
        print("=========================================")
        print(f" JALANKAN BOT MANAGE: {aksi}")
        print(f" Target: @{target_user}")
        print("=========================================")

        print("[1] Menghubungkan ke perangkat Android...")
        d = connect_adb(device_pilihan)
        width, height = d.window_size()

        print("[2] Membuka aplikasi Instagram...")
        d.app_start("com.instagram.android")
        time.sleep(6)
        
        # Bersihkan pop-up awal jika ada
        try:
            from bot_instagram_clear_popups import clear_any_popup_fast
            clear_any_popup_fast(d)
        except Exception as e:
            print(f"      -> Gagal memanggil popup cleaner: {e}")

        # Mulai langsung dari halaman depan untuk penanganan mandiri per aksi
        time.sleep(2)

        if aksi.lower() in ["accept_request", "accept"]:
            print("[3] Memulai proses Accept Follow Request...")
            # Masuk ke Beranda terlebih dahulu karena ikon Notifikasi berada di Beranda
            print("      Mengklik Beranda untuk mencari ikon Notifikasi...")
            if d(resourceId="com.instagram.android:id/feed_tab").exists:
                d(resourceId="com.instagram.android:id/feed_tab").click()
            elif d(resourceId="com.instagram.android:id/home_tab").exists:
                d(resourceId="com.instagram.android:id/home_tab").click()
            else:
                d.click(int(width * 0.095), int(height * 0.918))
            time.sleep(3)
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
                print("Mengklik ikon Notifikasi via koordinat kalibrasi (0.94, 0.054)...")
                d.click(int(width * 0.94), int(height * 0.054))
                
            time.sleep(4)

            # Langsung tembak koordinat presisi user (0.886, 0.14)
            x_coord = int(width * 0.886)
            y_coord = int(height * 0.14)
            print(f"Mengklik baris 'Permintaan Mengikuti' via koordinat: ({x_coord}, {y_coord})...")
            d.click(x_coord, y_coord)

            # Tunggu 5 detik agar halaman terbuka penuh
            print("Menunggu halaman Permintaan Mengikuti terbuka...")
            time.sleep(5)

            print("\n[START] Memulai proses konfirmasi dan follow back otomatis (tanpa scroll)...")
            total_dikonfirmasi = 0
            total_follow_back = 0
            keywords_confirm = ["konfirmasi", "confirm", "setuju", "accept", "approve"]
            keywords_follow_back = ["ikuti balik", "follow back", "follow", "ikuti"]

            y_min = int(height * 0.15)
            y_max = int(height * 0.85)

            # 1. Cari dan klik semua tombol Konfirmasi di layar
            print("Mencari tombol Konfirmasi di layar...")
            buttons = d(className="android.widget.Button")
            for btn in buttons:
                try:
                    if not btn.exists:
                        continue
                    info = btn.info
                    txt = info.get('text', '') or ""
                    desc = info.get('contentDescription', '') or ""
                    txt_lower = txt.lower()
                    desc_lower = desc.lower()
                    
                    bounds = info.get('bounds', {})
                    if not bounds:
                        continue
                    
                    y = (bounds['top'] + bounds['bottom']) // 2
                    if not (y_min <= y <= y_max):
                        continue

                    is_confirm_btn = False
                    for kw in keywords_confirm:
                        if kw in txt_lower or kw in desc_lower:
                            is_confirm_btn = True
                            break

                    btn_width = bounds['right'] - bounds['left']
                    btn_height = bounds['bottom'] - bounds['top']
                    if txt == "" and desc == "" and btn_width > btn_height * 1.5:
                        is_confirm_btn = True

                    if is_confirm_btn:
                        print(f"Mengklik tombol Konfirmasi (Teks: '{txt}', Desc: '{desc}')")
                        btn.click()
                        total_dikonfirmasi += 1
                        time.sleep(random.uniform(2.0, 3.5))
                except Exception as e:
                    print(f"Error saat klik konfirmasi: {e}")
                    continue

            # Berikan waktu agar tombol berubah status di layar
            time.sleep(3.0)

            # 2. Cari dan klik semua tombol Follow Back di layar
            print("Mencari tombol Follow Back di layar...")
            buttons = d(className="android.widget.Button")
            for btn in buttons:
                try:
                    if not btn.exists:
                        continue
                    info = btn.info
                    txt = info.get('text', '') or ""
                    desc = info.get('contentDescription', '') or ""
                    txt_lower = txt.lower()
                    desc_lower = desc.lower()
                    
                    bounds = info.get('bounds', {})
                    if not bounds:
                        continue
                    
                    y = (bounds['top'] + bounds['bottom']) // 2
                    if not (y_min <= y <= y_max):
                        continue

                    is_follow_back = False
                    for kw in keywords_follow_back:
                        if kw in txt_lower or kw in desc_lower:
                            # Abaikan jika tulisannya "mengikuti", "following", atau "diikuti"
                            if "mengikuti" not in txt_lower and "following" not in txt_lower and "diikuti" not in txt_lower:
                                is_follow_back = True
                                break

                    if is_follow_back:
                        print(f"Mengklik tombol Follow Back (Teks: '{txt}', Desc: '{desc}')")
                        btn.click()
                        total_follow_back += 1
                        time.sleep(random.uniform(2.0, 3.5))
                except Exception as e:
                    print(f"Error saat klik follow back: {e}")
                    continue

            print(f"\n[SELESAI] Selesai melakukan konfirmasi ({total_dikonfirmasi}) & follow back ({total_follow_back}).")
            
            # Kembali ke Beranda khusus untuk accept_request (back 2x lalu klik Home)
            print("Kembali ke Beranda...")
            d.press("back")
            time.sleep(1.5)
            d.press("back")
            time.sleep(1.5)
            if d(resourceId="com.instagram.android:id/feed_tab").exists:
                d(resourceId="com.instagram.android:id/feed_tab").click()
            elif d(resourceId="com.instagram.android:id/home_tab").exists:
                d(resourceId="com.instagram.android:id/home_tab").click()
            else:
                d.click(int(width * 0.095), int(height * 0.918))
            time.sleep(2)

        elif aksi.lower() in ["switch_account", "switch"]:
            print(f"[3] Memulai proses Switch Account ke: {target_user}...")
            print(" Mengklik tombol Profil (Kanan Bawah)...")
            profile_clicked = False
            xpath_profile = '//*[@resource-id="com.instagram.android:id/profile_tab"]/android.view.ViewGroup[1]/android.widget.FrameLayout[1]'
            try:
                if d.xpath(xpath_profile).exists:
                    d.xpath(xpath_profile).click()
                    profile_clicked = True
                    print("      -> Klik ikon profil via XPath")
            except:
                pass
                
            if not profile_clicked:
                for descriptor in ["Profil", "Profile", "Profile tab", "Tab profil", "Self profile"]:
                    elem = d(descriptionContains=descriptor)
                    if elem.exists:
                        elem.click()
                        profile_clicked = True
                        print(f"      -> Klik ikon profil via deskripsi '{descriptor}'")
                        break
            
            if not profile_clicked:
                if d(resourceId="com.instagram.android:id/profile_tab").exists:
                    d(resourceId="com.instagram.android:id/profile_tab").click()
                    print("      -> Klik ikon profil via resourceId profile_tab")
                else:
                    d.click(int(width * 0.9), int(height * 0.916))
                    print("      -> Klik ikon profil via koordinat")
            time.sleep(4)
            
            print(" Menekan lama tombol Profil untuk memunculkan menu ganti akun...")
            profile_btn = None
            xpath_profile = '//*[@resource-id="com.instagram.android:id/profile_tab"]/android.view.ViewGroup[1]/android.widget.FrameLayout[1]'
            
            if d.xpath(xpath_profile).exists:
                profile_btn = d.xpath(xpath_profile)
            elif d(resourceId="com.instagram.android:id/profile_tab").exists:
                profile_btn = d(resourceId="com.instagram.android:id/profile_tab")
                
            if profile_btn:
                try:
                    profile_btn.long_click()
                    print("      -> Long click via element berhasil")
                except:
                    d.touch.long_click(int(width * 0.9), int(height * 0.916), duration=2.0)
                    print("      -> Fallback: Long click via koordinat kalibrasi")
            else:
                d.touch.long_click(int(width * 0.9), int(height * 0.916), duration=2.0)
                print("      -> Long click via koordinat kalibrasi")
            time.sleep(3)
            
            print(f" Mencari dan mengklik nama akun: {target_user}...")
            cleaned_target = target_user.replace('@', '').strip().lower()
            
            target_variations = [cleaned_target, target_user, target_user.lower()]
            account_clicked = False
            for target_var in target_variations:
                if d(text=target_var).exists:
                    d(text=target_var).click()
                    account_clicked = True
                    print(f"      -> Berhasil klik akun via text '{target_var}'")
                    break
                elif d(textContains=target_var).exists:
                    d(textContains=target_var).click()
                    account_clicked = True
                    print(f"      -> Berhasil klik akun via textContains '{target_var}'")
                    break
                    
            if not account_clicked:
                print("   Menggunakan koordinat cadangan untuk memilih akun kedua di daftar switcher...")
                d.click(int(width * 0.5), int(height * 0.72))
            time.sleep(5)
            print(" Berhasil ganti akun!")
            
            # Ganti akun mereload IG, cukup klik Home Tab agar bersih
            print("Memastikan berada di Beranda Instagram...")
            home_tab_clicked = False
            if d(resourceId="com.instagram.android:id/feed_tab").exists:
                d(resourceId="com.instagram.android:id/feed_tab").click()
                home_tab_clicked = True
            elif d(resourceId="com.instagram.android:id/home_tab").exists:
                d(resourceId="com.instagram.android:id/home_tab").click()
                home_tab_clicked = True
            elif d(descriptionContains="Beranda").exists:
                d(descriptionContains="Beranda").click()
                home_tab_clicked = True
            elif d(descriptionContains="Home").exists:
                d(descriptionContains="Home").click()
                home_tab_clicked = True
                
            if not home_tab_clicked:
                d.click(int(width * 0.095), int(height * 0.918))
            time.sleep(3)

        elif aksi.lower() in ["logout", "log_out"]:
            print("[3] Memulai proses Log Out Akun via bot_instagram_logout...")
            try:
                from bot_instagram_logout import run_logout_bot
                run_logout_bot(device_pilihan)
            except Exception as e:
                print(f"      -> Gagal memanggil modul logout: {e}")

        else:
            # ORIGINAL FOLLOW / UNFOLLOW SEARCH & ACT FLOW
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

            # Klik tab "Akun" / "Accounts"
            print("      Mengklik tab 'Akun' / 'Accounts' untuk menyaring hasil...")
            tab_akun = None
            
            # Coba menggunakan resourceId dan teks khusus dari XML dump pengguna
            for txt in ["Accounts", "Akun", "ACCOUNTS", "AKUN"]:
                if d(resourceId="com.instagram.android:id/tab_button_name_text", text=txt).exists:
                    tab_akun = d(resourceId="com.instagram.android:id/tab_button_name_text", text=txt)
                    break
                elif d.xpath(f'//*[@text="{txt}"]').exists:
                    tab_akun = d.xpath(f'//*[@text="{txt}"]')
                    break
            
            # Coba cari di seluruh TextView dengan resourceId tab_button_name_text
            if not tab_akun:
                for elem in d(resourceId="com.instagram.android:id/tab_button_name_text"):
                    try:
                        if elem.exists:
                            txt = elem.info.get('text', '') or ''
                            if txt.lower() in ["akun", "accounts"]:
                                tab_akun = elem
                                break
                    except:
                        pass
                        
            # Cari di seluruh TextView untuk pencarian case-insensitive umum
            if not tab_akun:
                for elem in d(className="android.widget.TextView"):
                    try:
                        if elem.exists:
                            txt = elem.info.get('text', '') or ''
                            desc = elem.info.get('contentDescription', '') or ''
                            if txt.lower() in ["akun", "accounts"] or desc.lower() in ["akun", "accounts", "tab akun", "accounts tab"]:
                                tab_akun = elem
                                break
                    except:
                        pass
            
            if not tab_akun:
                # Fallback: Cari menggunakan contains secara kasar
                for txt in ["Akun", "Accounts", "akun", "accounts"]:
                    if d(textContains=txt).exists:
                        tab_akun = d(textContains=txt)
                        break
                    elif d(descriptionContains=txt).exists:
                        tab_akun = d(descriptionContains=txt)
                        break
            
            if tab_akun:
                tab_akun.click()
                print("      -> Tab Akun berhasil diklik via elemen")
            else:
                # Koordinat kalibrasi presisi perangkat pengguna (0.359, 0.12)
                d.click(int(width * 0.359), int(height * 0.12))
                print("      -> Klik tab Akun via koordinat kalibrasi (0.359, 0.12)")
            time.sleep(3)

            print("      Memilih profil teratas dari tab Akun...")
            cleaned_target = target_user.replace('@', '').strip().lower()
            
            akun_target_text = d(text=cleaned_target, className="android.widget.TextView")
            akun_target_text_orig = d(text=target_user, className="android.widget.TextView")
            akun_target_contains = d(textContains=cleaned_target, className="android.widget.TextView")
            
            if akun_target_text.exists:
                akun_target_text.click()
            elif akun_target_text_orig.exists:
                akun_target_text_orig.click()
            elif akun_target_contains.exists:
                akun_target_contains.click()
            elif d(resourceId="com.instagram.android:id/row_search_user_info_container").exists:
                d(resourceId="com.instagram.android:id/row_search_user_info_container").click()
            elif d(resourceId="com.instagram.android:id/row_search_user_container").exists:
                d(resourceId="com.instagram.android:id/row_search_user_container").click()
            else:
                # Klik posisi baris pertama di bawah tab (biasanya y = 24% tinggi layar)
                d.click(int(width * 0.5), int(height * 0.24))
            time.sleep(5)

            if aksi.lower() == "unfollow":
                print(f"[4] Melakukan UNFOLLOW @{target_user}...")
                if d(text="Mengikuti").exists:
                    d(text="Mengikuti").click()
                    time.sleep(2)
                    if d(text="Berhenti Mengikuti").exists:
                        d(text="Berhenti Mengikuti").click()
                    elif d(text="Unfollow").exists:
                        d(text="Unfollow").click()
                    elif d(textContains="Berhenti").exists:
                        d(textContains="Berhenti").click()
                    print("      -> Berhasil unfollow")
                elif d(text="Following").exists:
                    d(text="Following").click()
                    time.sleep(2)
                    if d(text="Unfollow").exists:
                        d(text="Unfollow").click()
                    print("      -> Berhasil unfollow")
            else:
                print(f"[4] Melakukan FOLLOW @{target_user}...")
                if d(text="Ikuti").exists:
                    d(text="Ikuti").click()
                    print("      -> Berhasil follow (Ikuti)")
                elif d(text="Follow").exists:
                    d(text="Follow").click()
                    print("      -> Berhasil follow (Follow)")
                else:
                    print("      -> Tombol follow tidak ditemukan (mungkin sudah follow)")
            time.sleep(3)

            print("[5] Kembali ke Beranda...")
            # 1. Klik kembali pertama (dari profil target ke hasil pencarian)
            print("      Mengklik kembali pertama (ke hasil pencarian)...")
            back_btn1 = None
            for desc in ["Kembali", "Back", "Navigate up", "Arahkan ke atas"]:
                if d(descriptionContains=desc).exists:
                    back_btn1 = d(descriptionContains=desc)
                    break
            
            if not back_btn1 and d(resourceId="com.instagram.android:id/action_bar_button_back").exists:
                back_btn1 = d(resourceId="com.instagram.android:id/action_bar_button_back")
            elif not back_btn1 and d(resourceId="com.instagram.android:id/left_action_bar_buttons").exists:
                back_btn1 = d(resourceId="com.instagram.android:id/left_action_bar_buttons")
                
            if back_btn1:
                back_btn1.click()
            else:
                # Cukup gunakan tombol kembali fisik Android
                d.press("back")
            time.sleep(2.5)

            # 2. Klik kembali kedua (dari hasil pencarian ke tab cari / beranda utama)
            print("      Mengklik kembali kedua (ke beranda/cari)...")
            back_btn2 = None
            for desc in ["Kembali", "Back", "Navigate up", "Arahkan ke atas"]:
                if d(descriptionContains=desc).exists:
                    back_btn2 = d(descriptionContains=desc)
                    break
            
            if not back_btn2 and d(resourceId="com.instagram.android:id/action_bar_button_back").exists:
                back_btn2 = d(resourceId="com.instagram.android:id/action_bar_button_back")
            elif not back_btn2 and d(resourceId="com.instagram.android:id/left_action_bar_buttons").exists:
                back_btn2 = d(resourceId="com.instagram.android:id/left_action_bar_buttons")
                
            if back_btn2:
                back_btn2.click()
            else:
                # Cukup gunakan tombol kembali fisik Android
                d.press("back")
            time.sleep(2.5)

            # 3. Klik tab Beranda Instagram (Kiri Bawah) untuk memastikan di Home Feed
            print("      Mengklik ikon Beranda Instagram...")
            home_tab_clicked = False
            if d(resourceId="com.instagram.android:id/feed_tab").exists:
                d(resourceId="com.instagram.android:id/feed_tab").click()
                home_tab_clicked = True
            elif d(resourceId="com.instagram.android:id/home_tab").exists:
                d(resourceId="com.instagram.android:id/home_tab").click()
                home_tab_clicked = True
            elif d(descriptionContains="Beranda").exists:
                d(descriptionContains="Beranda").click()
                home_tab_clicked = True
            elif d(descriptionContains="Home").exists:
                d(descriptionContains="Home").click()
                home_tab_clicked = True
                
            if not home_tab_clicked:
                d.click(int(width * 0.095), int(height * 0.918))
            time.sleep(3)

        print("=========================================")
        print(f" MANAGE ({aksi}) BERHASIL: @{target_user}")
        print("=========================================\n")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else ""
    aksi = sys.argv[2] if len(sys.argv) > 2 else "follow"
    device = sys.argv[3] if len(sys.argv) > 3 else "all"
    
    if not target:
        if not sys.stdin.isatty():
            print("ERROR: target (username) wajib disertakan.")
            sys.exit(1)
        try:
            print("\n--- MENJALANKAN BOT MANAGE SECARA INTERAKTIF ---")
            target = input("Masukkan username target: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEksekusi dibatalkan.")
            sys.exit(1)

    if not target:
        print("ERROR: Target tidak boleh kosong!")
        sys.exit(1)

    if len(sys.argv) <= 2 and sys.stdin.isatty():
        try:
            ans_aksi = input("Masukkan aksi ('follow' / 'unfollow' / 'block', default 'follow'): ").strip()
            if ans_aksi:
                aksi = ans_aksi
        except (EOFError, KeyboardInterrupt):
            pass

    if len(sys.argv) <= 3 and sys.stdin.isatty():
        try:
            ans_dev = input("Masukkan device ID (kosongkan/tekan Enter untuk 'all'): ").strip()
            if ans_dev:
                device = ans_dev
        except (EOFError, KeyboardInterrupt):
            pass
            
    bot_manage(target, aksi, device)
