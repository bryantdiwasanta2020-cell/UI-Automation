import sys
import uiautomator2 as u2
import time
import os
from ig_helpers import connect_adb, open_instagram

def find_element(d, descriptions=[], texts=[], resource_ids=[]):
    # 1. Coba resource IDs dahulu
    for res_id in resource_ids:
        try:
            if d(resourceId=res_id).exists:
                return d(resourceId=res_id)
        except:
            pass
            
    # 2. Coba exact description match
    for desc in descriptions:
        try:
            if d(description=desc).exists:
                return d(description=desc)
        except:
            pass
            
    # 3. Coba exact text match
    for text in texts:
        try:
            if d(text=text).exists:
                return d(text=text)
        except:
            pass

    # 4. Coba description contains (sebagai fallback)
    for desc in descriptions:
        try:
            if d(descriptionContains=desc).exists:
                return d(descriptionContains=desc)
        except:
            pass
            
    # 5. Coba text contains (sebagai fallback terakhir, abaikan Name/Nama agar tidak tabrakan dengan Username)
    for text in texts:
        if text.lower() in ["name", "nama"]:
            continue
        try:
            if d(textContains=text).exists:
                return d(textContains=text)
        except:
            pass
            
    return None

def open_edit_profile(d, width, height):
    edit_clicked = False
    for text_val in ["Edit profil", "Edit Profile", "Edit profile", "Sunting profil"]:
        elem = d(text=text_val)
        if elem.exists:
            elem.click()
            edit_clicked = True
            print(f"      -> Klik tombol Edit Profil via teks '{text_val}'")
            break
    
    if not edit_clicked:
        if d(resourceId="com.instagram.android:id/edit_profile_button").exists:
            d(resourceId="com.instagram.android:id/edit_profile_button").click()
            print("      -> Klik tombol Edit Profil via resourceId")
        else:
            d.click(int(width * 0.5), int(height * 0.22))
            print("      -> Klik tombol Edit Profil via koordinat default")

def bot_profile(nama, username, bio, avatar_path, device_id="all"):
    try:
        print("=========================================")
        print(" JALANKAN BOT EDIT PROFILE INSTAGRAM")
        print(f" Target Device: {device_id}")
        print(f" Nama: {nama if nama else '-'}")
        print(f" Username: {username if username else '-'}")
        print(f" Bio: {bio if bio else '-'}")
        print(f" Avatar Path: {avatar_path if avatar_path else '-'}")
        print("=========================================")

        d = connect_adb(device_id, action=None, step_label="[1] Menghubungkan ke perangkat Android...")
        width, height = d.window_size()

        # 1. Pindah media avatar jika disediakan
        if avatar_path and os.path.exists(avatar_path):
            file_name = os.path.basename(avatar_path)
            remote_path = f"/sdcard/DCIM/Camera/{file_name}"
            print(f"[*] Mengirim foto profil baru ke HP: {remote_path}...")
            try:
                d.push(avatar_path, remote_path)
                d.shell(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://{remote_path}"')
                d.shell(f'media scan-file "{remote_path}"')
                print("      -> Upload media & media scanner scan berhasil")
                time.sleep(3)
            except Exception as upload_err:
                print(f"      -> Warning Gagal upload media ke DCIM: {upload_err}")
                try:
                    remote_path = f"/sdcard/Pictures/{file_name}"
                    d.push(avatar_path, remote_path)
                    d.shell(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://{remote_path}"')
                    d.shell(f'media scan-file "{remote_path}"')
                    print("      -> Upload media & media scanner scan berhasil (fallback Pictures)")
                    time.sleep(3)
                except Exception as e2:
                    print(f"      -> Gagal mengunggah media ke HP: {e2}")

        open_instagram(d, device_id, action=None, delay=6, step_label="[2] Membuka aplikasi Instagram...")
        
        # Bersihkan pop-up awal jika ada
        try:
            from bot_instagram_clear_popups import clear_any_popup_fast
            clear_any_popup_fast(d)
        except Exception as e:
            print(f"      -> Gagal memanggil popup cleaner: {e}")

        # 2. Masuk ke halaman Profil
        print("[3] Masuk ke halaman Profil...")
        profile_clicked = False
        
        # Cek XPath spesifik perangkat pengguna
        xpath_profile = '//*[@resource-id="com.instagram.android:id/profile_tab"]/android.view.ViewGroup[1]/android.widget.FrameLayout[1]'
        try:
            if d.xpath(xpath_profile).exists:
                d.xpath(xpath_profile).click()
                profile_clicked = True
                print("      -> Klik ikon profil via XPath spesifik")
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
                # Koordinat kalibrasi presisi perangkat (0.9, 0.916)
                d.click(int(width * 0.9), int(height * 0.916))
                print("      -> Klik ikon profil via koordinat kalibrasi (0.9, 0.916)")
        time.sleep(4)

        # SESSION 1: EDIT NAMA, USERNAME, DAN BIO
        if nama or username or bio:
            print("[4] Klik tombol Edit Profil (Sesi 1: Nama, Username & Bio)...")
            open_edit_profile(d, width, height)
            time.sleep(4)

            # A. Ubah Nama jika disediakan
            if nama:
                print(f"[5] Mengubah Nama Tampilan menjadi: {nama}...")
                name_field = find_element(d, 
                                          descriptions=["Nama", "Name"], 
                                          texts=["Nama", "Name"],
                                          resource_ids=["com.instagram.android:id/name", "com.instagram.android:id/full_name", "com.instagram.android:id/edit_profile_name"])
                if not name_field:
                    name_field = d(className="android.widget.EditText", instance=0)
                
                if name_field:
                    name_field.click()
                    time.sleep(3)
                    
                    name_input = d(className="android.widget.EditText")
                    if name_input.exists:
                        name_input.click()
                        time.sleep(1)
                        name_input.clear_text()
                        time.sleep(1)
                        name_input.set_text(nama)
                        time.sleep(2)
                        
                        # Simpan Nama (Klik centang)
                        done_btn = find_element(d, 
                                                descriptions=["Selesai", "Done", "Save", "Centang"],
                                                texts=["Selesai", "Done", "Save"],
                                                resource_ids=["com.instagram.android:id/action_bar_button_done"])
                        if done_btn:
                            done_btn.click()
                        else:
                            d.click(int(width * 0.92), int(height * 0.06))
                        print("      -> Nama disubmit")
                        time.sleep(3)

                        # Cek dialog konfirmasi "Ubah nama" / "Change name"
                        confirm_dialog_btn = find_element(d,
                                                          descriptions=["Ubah nama", "Change name", "Ganti nama", "Ubah", "Change", "Ubah Nama"],
                                                          texts=["Ubah nama", "Change name", "Ganti nama", "Ubah", "Change", "Ubah Nama"])
                        if confirm_dialog_btn:
                            confirm_dialog_btn.click()
                            print("      -> Klik konfirmasi dialog Ubah Nama")
                            time.sleep(3)
                else:
                    print("      -> Field Nama tidak ditemukan!")

            # B. Ubah Username jika disediakan
            if username:
                print(f"[5.5] Mengubah Username menjadi: {username}...")
                username_field = find_element(d, 
                                              descriptions=["Nama pengguna", "Username"], 
                                              texts=["Nama pengguna", "Username"],
                                              resource_ids=["com.instagram.android:id/username", "com.instagram.android:id/edit_profile_username", "com.instagram.android:id/username_value"])
                if not username_field:
                    # Di halaman Edit Profil, EditText kedua biasanya adalah Username
                    username_field = d(className="android.widget.EditText", instance=1)
                
                if username_field:
                    username_field.click()
                    time.sleep(3)
                    
                    username_input = d(className="android.widget.EditText")
                    if username_input.exists:
                        username_input.click()
                        time.sleep(1)
                        username_input.clear_text()
                        time.sleep(1)
                        username_input.set_text(username)
                        time.sleep(3) # Tunggu pengecekan ketersediaan username di layar
                        
                        # Simpan Username (Klik centang)
                        done_btn = find_element(d, 
                                                descriptions=["Selesai", "Done", "Save", "Centang"],
                                                texts=["Selesai", "Done", "Save"],
                                                resource_ids=["com.instagram.android:id/action_bar_button_done"])
                        if done_btn:
                            done_btn.click()
                        else:
                            d.click(int(width * 0.92), int(height * 0.06))
                        print("      -> Username disubmit")
                        time.sleep(3)

                        # Cek dialog konfirmasi "Ganti nama pengguna" / "Change username"
                        confirm_usr_btn = find_element(d,
                                                       descriptions=["Ganti nama pengguna", "Change username", "Ubah", "Change", "Ubah Nama Pengguna"],
                                                       texts=["Ganti nama pengguna", "Change username", "Ubah", "Change", "Ubah Nama Pengguna"])
                        if confirm_usr_btn:
                            confirm_usr_btn.click()
                            print("      -> Klik konfirmasi dialog Ubah Username")
                            time.sleep(3)
                else:
                    print("      -> Field Username tidak ditemukan!")

            # C. Ubah Bio jika disediakan
            if bio:
                print(f"[6] Mengubah Bio menjadi: {bio}...")
                bio_field = None
                
                # 1. Coba cari EditText yang text-nya adalah salah satu placeholder umum bio kosong
                for placeholder in ["Let them know", "Beri tahu orang lain", "Tulis bio...", "Bio", "Biografi"]:
                    try:
                        elem = d(className="android.widget.EditText", text=placeholder)
                        if elem.exists:
                            bio_field = elem
                            print(f"      -> Menemukan bio_field via placeholder text: '{placeholder}'")
                            break
                    except:
                        pass
                
                # 2. Coba cari sibling EditText dari label TextView "Bio" atau "Biografi"
                if not bio_field:
                    for label in ["Bio", "Biografi"]:
                        try:
                            # Coba dengan text label
                            lbl = d(text=label)
                            if lbl.exists:
                                sibling = lbl.sibling(className="android.widget.EditText")
                                if sibling.exists:
                                    bio_field = sibling
                                    print(f"      -> Menemukan bio_field via sibling text '{label}'")
                                    break
                            
                            # Coba dengan description label
                            lbl_desc = d(description=label)
                            if lbl_desc.exists:
                                sibling = lbl_desc.sibling(className="android.widget.EditText")
                                if sibling.exists:
                                    bio_field = sibling
                                    print(f"      -> Menemukan bio_field via sibling description '{label}'")
                                    break
                        except:
                            pass

                # 3. Coba cari EditText berdasarkan koordinat y (y-ratio sekitar 0.50 - 0.62)
                if not bio_field:
                    try:
                        edit_texts = d(className="android.widget.EditText")
                        for idx, elem in enumerate(edit_texts):
                            if elem.exists:
                                info = elem.info
                                bounds = info.get('bounds', {})
                                top = bounds.get('top', 0)
                                bottom = bounds.get('bottom', 0)
                                y_ratio = ((top + bottom) / 2) / height
                                if 0.50 <= y_ratio <= 0.62:
                                    bio_field = elem
                                    print(f"      -> Menemukan bio_field via koordinat y ({y_ratio:.3f}) pada EditText index {idx}")
                                    break
                    except Exception as err:
                        print(f"      -> Gagal mencari via koordinat y: {err}")

                # 4. Fallback ke index 2 (EditText ke-3) jika ada setidaknya 3 EditText
                if not bio_field:
                    try:
                        edit_texts = d(className="android.widget.EditText")
                        if len(edit_texts) >= 3:
                            bio_field = edit_texts[2]
                            print("      -> Menemukan bio_field via fallback EditText index 2")
                    except:
                        pass

                # Proses klik ke halaman Bio
                if bio_field:
                    bio_field.click()
                    print("      -> Mengklik field Bio yang ditemukan")
                    time.sleep(3)
                else:
                    # Klik via koordinat default kalibrasi user (0.554, 0.535)
                    print(f"      -> Klik field Bio via koordinat default: ({int(width * 0.554)}, {int(height * 0.535)})")
                    d.click(int(width * 0.554), int(height * 0.535))
                    time.sleep(3)

                # Di dalam halaman Bio
                bio_input = d(className="android.widget.EditText")
                if bio_input.exists:
                    bio_input.click()
                    time.sleep(1)
                    bio_input.clear_text()
                    time.sleep(1)
                    bio_input.set_text(bio)
                    time.sleep(2)
                    
                    # Simpan halaman Bio
                    done_btn = find_element(d, 
                                            descriptions=["Selesai", "Done", "Save", "Centang"],
                                            texts=["Selesai", "Done", "Save"],
                                            resource_ids=["com.instagram.android:id/action_bar_button_done"])
                    if done_btn:
                        done_btn.click()
                        print("      -> Bio disimpan di sub-halaman")
                    else:
                        d.click(int(width * 0.92), int(height * 0.06))
                        print("      -> Bio disimpan via koordinat centang")
                    time.sleep(3)
                else:
                    print("      -> Field input Bio terpisah tidak muncul!")

            # Simpan seluruh perubahan teks di halaman Edit Profil utama
            print("[7] Menyimpan seluruh perubahan Nama, Username & Bio...")
            save_btn = find_element(d, 
                                    descriptions=["Selesai", "Done", "Save", "Centang"],
                                    texts=["Selesai", "Done", "Save"],
                                    resource_ids=["com.instagram.android:id/action_bar_button_done"])
            if save_btn:
                save_btn.click()
                print("      -> Perubahan teks disimpan via tombol centang")
            else:
                d.click(int(width * 0.92), int(height * 0.06))
                print("      -> Perubahan teks disimpan via koordinat centang")
            time.sleep(5)

        # SESSION 2: EDIT FOTO PROFIL
        if avatar_path and os.path.exists(avatar_path):
            print("[8] Klik tombol Edit Profil (Sesi 2: Foto Profil)...")
            open_edit_profile(d, width, height)
            time.sleep(4)

            print("[9] Mengganti Foto Profil...")
            change_photo_btn = None
            
            # 1. Cari berdasarkan resourceId
            if d(resourceId="com.instagram.android:id/change_avatar_button").exists:
                change_photo_btn = d(resourceId="com.instagram.android:id/change_avatar_button")
                print("      -> Menemukan change_photo_btn via resourceId")
            
            # 2. Cari berdasarkan teks/deskripsi
            if not change_photo_btn:
                for txt in ["Edit picture or avatar", "Edit gambar atau avatar", "Edit foto atau avatar", "Ganti foto", "Ganti foto profil", "Change photo", "Change profile photo"]:
                    if d(text=txt).exists:
                        change_photo_btn = d(text=txt)
                        print(f"      -> Menemukan change_photo_btn via teks '{txt}'")
                        break
                    elif d(descriptionContains=txt).exists:
                        change_photo_btn = d(descriptionContains=txt)
                        print(f"      -> Menemukan change_photo_btn via deskripsi '{txt}'")
                        break
            
            # 3. Klik tombol
            if change_photo_btn:
                change_photo_btn.click()
                print("      -> Klik tombol ganti foto profil")
            else:
                # Klik via koordinat default kalibrasi user (0.436, 0.23)
                print(f"      -> Klik tombol ganti foto profil via koordinat default: ({int(width * 0.436)}, {int(height * 0.23)})")
                d.click(int(width * 0.436), int(height * 0.23))
            time.sleep(3)

            # Klik "Foto profil baru" / "Choose from library" dari pop-up
            option_clicked = False
            for opt_text in ["Choose from library", "Choose from Library", "Foto profil baru", "New profile photo", "New Profile Photo", "Pilih dari Galeri", "Pilih dari galeri"]:
                elem = d(text=opt_text)
                if elem.exists:
                    elem.click()
                    option_clicked = True
                    print(f"      -> Memilih opsi '{opt_text}'")
                    break
                elem_desc = d(descriptionContains=opt_text)
                if elem_desc.exists:
                    elem_desc.click()
                    option_clicked = True
                    print(f"      -> Memilih opsi '{opt_text}' via deskripsi")
                    break
            
            if not option_clicked:
                d.click(int(width * 0.5), int(height * 0.85))
                print("      -> Memilih opsi foto profil baru via koordinat default")
            time.sleep(4)

            # Pilih foto pertama dari galeri
            print("      -> Memilih foto pertama dari galeri...")
            photo_clicked = False
            try:
                # Cari ImageView pertama di bagian grid (y-ratio antara 0.4 dan 0.8)
                images = d(className="android.widget.ImageView")
                for img in images:
                    if img.exists:
                        info = img.info
                        bounds = info.get('bounds', {})
                        top = bounds.get('top', 0)
                        y_ratio = top / height
                        if 0.40 <= y_ratio <= 0.80:
                            img.click()
                            photo_clicked = True
                            print(f"      -> Foto dipilih via ImageView pada y_ratio {y_ratio:.3f}")
                            break
            except Exception as e:
                print(f"      -> Gagal mencari ImageView galeri secara dinamis: {e}")
                
            if not photo_clicked:
                # Koordinat fallback
                print("      -> Menggunakan koordinat fallback untuk foto pertama")
                d.click(int(width * 0.12), int(height * 0.56))
                time.sleep(1.5)
                # Jika koordinat di atas meleset, coba klik koordinat alternatif
                d.click(int(width * 0.12), int(height * 0.45))
            time.sleep(3)

            # Klik tombol Next/Berikutnya di kanan atas (Pilih foto)
            print("      -> Klik 'Next' halaman Galeri...")
            next_btn = find_element(d, 
                                    descriptions=["Berikutnya", "Next"],
                                    texts=["Berikutnya", "Next"],
                                    resource_ids=["com.instagram.android:id/next_button_text", "com.instagram.android:id/action_bar_button_action"])
            if next_btn:
                next_btn.click()
            else:
                d.click(int(width * 0.92), int(height * 0.06))
            time.sleep(4)

            # Klik tombol Next/Berikutnya di kanan atas (Halaman filter/edit foto)
            print("      -> Konfirmasi foto profil (Next/Done)...")
            next_btn2 = find_element(d, 
                                     descriptions=["Berikutnya", "Next", "Done", "Selesai"],
                                     texts=["Berikutnya", "Next", "Done", "Selesai"],
                                     resource_ids=["com.instagram.android:id/next_button_text", "com.instagram.android:id/action_bar_button_action"])
            if next_btn2:
                next_btn2.click()
            else:
                d.click(int(width * 0.92), int(height * 0.06))
            
            print("      -> Menunggu proses upload foto profil...")
            time.sleep(8)

        # 8. Kembali ke Beranda Instagram (dengan forced stop + restart agar bersih)
        print("[10] Kembali ke Beranda Instagram...")
        try:
            print("      -> Menghentikan paksa (kill) aplikasi Instagram...")
            d.app_stop("com.instagram.android")
            time.sleep(2.0)
            
            print("      -> Membuka kembali aplikasi Instagram...")
            d.app_start("com.instagram.android")
            time.sleep(5.0)
            
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
            
        print("=========================================")
        print(" EDIT PROFILE INSTAGRAM SELESAI")
        print("=========================================\n")

    except Exception as e:
        print(f"ERROR: {e}")
        raise e

if __name__ == "__main__":
    nama = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else ""
    username = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else ""
    bio = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "-" else ""
    avatar = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "-" else ""
    device = sys.argv[5] if len(sys.argv) > 5 else "all"
    
    bot_profile(nama, username, bio, avatar, device)
