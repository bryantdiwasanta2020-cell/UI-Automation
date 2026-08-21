import sys
import uiautomator2 as u2
import time
from ig_helpers import connect_adb, open_instagram

def bot_chat(target_user, pesan_dm, device_pilihan=None):
    try:
        print("=========================================")
        print(f" JALANKAN BOT CHAT/DM")
        print(f" Target: @{target_user} -> Pesan: {pesan_dm}")
        print("=========================================")

        if device_pilihan is None:
            device_pilihan = sys.argv[3] if len(sys.argv) > 3 else "all"

        d = connect_adb(device_pilihan, action=None, step_label="[1] Menghubungkan ke perangkat Android...")
        width, height = d.window_size()

        open_instagram(d, device_pilihan, action=None, delay=6, step_label="[2] Membuka aplikasi Instagram...")
        
        # Bersihkan pop-up awal jika ada
        try:
            from bot_instagram_clear_popups import clear_any_popup_fast
            clear_any_popup_fast(d)
        except Exception as e:
            print(f"      -> Gagal memanggil popup cleaner: {e}")

        print(f"[3] Mencari profil target: @{target_user}...")
        
        # Bersihkan pop-up sebelum pencarian
        try:
            clear_any_popup_fast(d)
        except:
            pass
            
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

        print("[4] Klik tombol 'Kirim Pesan' / 'Message'...")
        msg_clicked = False
        for kw in ["Kirim Pesan", "Message", "Pesan"]:
            if d(text=kw).click_exists(timeout=3):
                print(f"      -> Klik: '{kw}'")
                msg_clicked = True
                break
        if not msg_clicked:
            for desc in ["Kirim Pesan", "Message", "Pesan"]:
                if d(descriptionContains=desc).click_exists(timeout=3):
                    print(f"      -> Klik desc: '{desc}'")
                    msg_clicked = True
                    break
        if not msg_clicked:
            if d(resourceId="com.instagram.android:id/profile_header_actions_top_container").exists:
                d(resourceId="com.instagram.android:id/profile_header_actions_top_container").click()
                time.sleep(2)
                for kw in ["Kirim Pesan", "Message", "Pesan"]:
                    if d(text=kw).click_exists(timeout=2):
                        msg_clicked = True
                        break
        if not msg_clicked:
            d.click(int(width * 0.5), int(height * 0.18))
        time.sleep(5)

        print(f"[5] Mengetik pesan DM: '{pesan_dm}'...")
        if d(resourceId="com.instagram.android:id/row_thread_composer_edittext").exists:
            d(resourceId="com.instagram.android:id/row_thread_composer_edittext").click()
            time.sleep(1.5)
            d(resourceId="com.instagram.android:id/row_thread_composer_edittext").set_text(pesan_dm)
            print("      -> Mengetik via row_thread_composer_edittext")
        elif d(resourceId="com.instagram.android:id/composer_content_container").exists:
            d(resourceId="com.instagram.android:id/composer_content_container").click()
            time.sleep(1.5)
            d.send_keys(pesan_dm)
            print("      -> Mengetik via composer_content_container + send_keys")
        elif d(className="android.widget.EditText").exists:
            d(className="android.widget.EditText").click()
            time.sleep(1.5)
            d(className="android.widget.EditText").set_text(pesan_dm)
            print("      -> Mengetik via EditText")
        else:
            d.click(int(width * 0.109), int(height * 0.9))
            time.sleep(1.5)
            d.send_keys(pesan_dm)
            print("      -> Mengetik via koordinat fallback")
        time.sleep(2)

        print("[6] Mengirim pesan...")
        if d(resourceId="com.instagram.android:id/row_thread_composer_send_button_icon").exists:
            d(resourceId="com.instagram.android:id/row_thread_composer_send_button_icon").click()
            print("      -> Kirim via send_button_icon")
        elif d(description="Kirim").exists:
            d(description="Kirim").click()
        elif d(description="Send").exists:
            d(description="Send").click()
        else:
            d.click(int(width * 0.89), int(height * 0.9))
        time.sleep(4)

        # Langkah 1: Tekan back 2 kali secara fisik untuk keluar dari chat detail dan inbox ke halaman utama
        # Ini memastikan kita sudah keluar dari sub-halaman sehingga tab bar bawah aktif dan tidak tertutup fragment/view lain
        print("      -> Mundur dari percakapan chat...")
        d.press("back")
        time.sleep(2)
        
        print("      -> Mundur dari inbox ke halaman utama...")
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
        print(f" CHAT/DM BERHASIL: @{target_user}")
        print("=========================================\n")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else ""
    pesan = sys.argv[2] if len(sys.argv) > 2 else ""
    device = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not target:
        if not sys.stdin.isatty():
            print("ERROR: target wajib disertakan.")
            sys.exit(1)
        try:
            print("\n--- MENJALANKAN BOT CHAT SECARA INTERAKTIF ---")
            target = input("Masukkan username target DM: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEksekusi dibatalkan.")
            sys.exit(1)

    if not target:
        print("ERROR: Target tidak boleh kosong!")
        sys.exit(1)

    if not pesan:
        if not sys.stdin.isatty():
            print("ERROR: pesan wajib disertakan.")
            sys.exit(1)
        try:
            pesan = input("Masukkan pesan DM yang ingin dikirim: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEksekusi dibatalkan.")
            sys.exit(1)

    if not pesan:
        print("ERROR: Pesan tidak boleh kosong!")
        sys.exit(1)

    if len(sys.argv) <= 3:
        if sys.stdin.isatty():
            try:
                ans_dev = input("Masukkan device ID (kosongkan/tekan Enter untuk 'all'): ").strip()
                if ans_dev:
                    device = ans_dev
                else:
                    device = "all"
            except (EOFError, KeyboardInterrupt):
                device = "all"
        else:
            device = "all"
            
    bot_chat(target, pesan, device)
