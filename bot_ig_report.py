import sys
import uiautomator2 as u2
import time
from ig_helpers import connect_adb, open_instagram

# Import activity logger if available
try:
    from activity_logger import log_activity, log_complete, log_error, log_step
except Exception:
    def log_activity(*a, **kw): return ""
    def log_complete(*a, **kw): return False
    def log_error(*a, **kw): return False
    def log_step(*a, **kw): return False

# Import popup cleaner if available
try:
    from bot_instagram_clear_popups import clear_any_popup_fast, check_and_clear_daily_limit
except Exception as e:
    # Fallback if the module is missing or cannot be imported
    def clear_any_popup_fast(d):
        return False
    def check_and_clear_daily_limit(d):
        return False

def safe_click(selector, timeout=2):
    if selector.click_exists(timeout=timeout):
        return True
    return False

def klik_kembali(d):
    btn_left = d(resourceId="com.instagram.android:id/left_action_bar_buttons")
    btn_back = d(resourceId="com.instagram.android:id/action_bar_button_back")
    if btn_left.exists:
        btn_left.click()
    elif btn_back.exists:
        btn_back.click()
    else:
        d.press("back")
    time.sleep(1.5)

def klik_konfirmasi(d):
    # Cek tombol konfirmasi menggunakan .exists (instan) alih-alih click_exists dengan timeout
    # Ini menghilangkan delay kumulatif puluhan detik jika tombol tidak ada di layar
    for kw in ["Ya, laporkan", "Kirim laporan", "Kirim", "Send", "Submit",
                "Berikutnya", "Lanjutkan", "Next", "Continue", "Paham",
                "OK", "Baik", "Oke", "Selesai", "Done", "Tutup", "Close",
                "Report account", "Laporkan akun", "Show profile", "Lihat profil"]:
        el_text = d(text=kw)
        if el_text.exists:
            el_text.click()
            print(f"      -> Konfirmasi: '{kw}'")
            return kw
        el_desc = d(descriptionContains=kw)
        if el_desc.exists:
            el_desc.click()
            print(f"      -> Konfirmasi via desc: '{kw}'")
            return kw
    return None

def bot_report(target_user, device_pilihan="all", alasan_pilihan="Sesuatu tentang akun ini", my_account=""):
    d = None
    width, height = 720, 1600
    log_id = log_activity("report", username=target_user, status="on_progress", mode="manual", device_id=device_pilihan, extra={"alasan": alasan_pilihan, "my_account": my_account})
    try:
        print("=========================================")
        print(f" JALANKAN BOT REPORT TARGET: @{target_user}")
        if alasan_pilihan:
            print(f" Alasan: {alasan_pilihan}")
        if my_account:
            print(f" Menggunakan Akun Saya: {my_account}")
        print("=========================================")

        d = connect_adb(device_pilihan, action="report", step_label="[1] Menghubungkan ke perangkat Android...")
        width, height = d.window_size()

        # Hentikan paksa dahulu agar bersih dari cache/halaman lama
        d.app_stop("com.instagram.android")
        time.sleep(2.0)
        open_instagram(d, device_pilihan, action="report", delay=5, step_label="[2] Membuka aplikasi Instagram...")
        clear_any_popup_fast(d)

        # === PROSES SWAP AKUN DI AWAL (JIKA PARAMETER DIBERIKAN) ===
        if my_account and my_account.strip() != "":
            print(f"[PRE-RUN] Mengganti akun ke: '{my_account}'...")
            
            # 1. Mengklik tombol Profil kanan bawah (dengan verifikasi halaman profil aktif)
            profile_active = False
            for check_prof in range(3):
                profile_tab = None
                if d(resourceId="com.instagram.android:id/profile_tab").exists:
                    profile_tab = d(resourceId="com.instagram.android:id/profile_tab")
                else:
                    sel = d(descriptionMatches="(?i).*(profile|profil).*", packageName="com.instagram.android")
                    if sel.exists:
                        profile_tab = sel
                            
                if profile_tab:
                    try:
                        profile_tab.click()
                        print("      -> Mengklik tab Profil via selector...")
                        time.sleep(3.0)
                    except:
                        pass
                else:
                    print("      -> Mengklik tab Profil via koordinat fallback...")
                    d.click(int(width * 0.90), int(height * 0.93))
                    time.sleep(1.5)
                    d.click(int(width * 0.90), int(height * 0.914))
                    time.sleep(2.0)
                
                clear_any_popup_fast(d)
                
                # Verifikasi jika nama akun/title bar profil muncul
                if d(resourceId="com.instagram.android:id/action_bar_title").exists or d(resourceId="com.instagram.android:id/title_with_badge_container").exists:
                    profile_active = True
                    break
                else:
                    print(f"      -> Halaman profil belum aktif (percobaan {check_prof+1}/3). Mencoba klik ulang tab Profil...")
            
            clean_acc = my_account.replace("@", "").strip().lower()
            
            # Cek apakah sudah berada di akun tersebut
            current_username = ""
            action_bar_title = d(resourceId="com.instagram.android:id/action_bar_title")
            title_badge = d(resourceId="com.instagram.android:id/title_with_badge_container")
            if action_bar_title.exists:
                current_username = action_bar_title.info.get("text", "").strip().lower()
            elif title_badge.exists:
                child_tv = title_badge.child(className="android.widget.TextView")
                if child_tv.exists:
                    current_username = child_tv.info.get("text", "").strip().lower()
                    
            if current_username == clean_acc:
                print(f"[PRE-RUN] Sudah berada di akun '{clean_acc}'. Melanjutkan perintah...")
            else:
                # 2. Mengklik Nama Pengguna di pojok atas (tengah/kiri) untuk membuka menu ganti akun
                print(f"      -> Akun saat ini '{current_username}' berbeda dengan target '{clean_acc}'. Membuka menu ganti akun...")
                if action_bar_title.exists:
                    action_bar_title.click()
                elif title_badge.exists:
                    title_badge.click()
                else:
                    # Fallback koordinat atas (Bryant Kalibrasi: 0.25, 0.06)
                    d.click(int(width * 0.25), int(height * 0.06))
                time.sleep(3.5)
                
                # 3. Cari nama akun dalam daftar pop-up bawah
                btn_acc = d(text=clean_acc)
                if not btn_acc.exists:
                    btn_acc = d(textContains=clean_acc)
                    
                if btn_acc.exists:
                    print(f"      -> Akun '{clean_acc}' ditemukan di daftar. Mengklik untuk beralih...")
                    btn_acc.click()
                    time.sleep(6.0)
                    clear_any_popup_fast(d)
                    
                    # Cek jika bottom sheet pilihan akun masih terbuka di layar
                    is_sheet_open = (
                        d(resourceId="com.instagram.android:id/bottom_sheet_container").exists or
                        d(textMatches="(?i).*(tambahkan akun|add account).*").exists
                    )
                    if is_sheet_open:
                        print("      -> Bottom sheet pilihan akun masih terbuka. Menekan BACK untuk menutup...")
                        d.press("back")
                        time.sleep(2.0)
                    
                    # Pastikan aplikasi Instagram tetap terbuka di foreground
                    if d.app_current().get('package') != 'com.instagram.android':
                        print("      -> Terdeteksi keluar dari Instagram, membuka kembali...")
                        d.app_start("com.instagram.android")
                        time.sleep(5.0)
                        
                    print(f"[PRE-RUN] Sukses beralih ke akun '{clean_acc}'. Melanjutkan perintah...")
                else:
                    print(f"[PRE-RUN] Akun '{clean_acc}' tidak ditemukan di menu ganti akun!")
                    print("      -> Menutup menu ganti akun (mengirim BACK)...")
                    d.press("back")
                    time.sleep(1.5)
                    print("akun tidak ditemukan")
                    print("=========================================\n")
                    raise Exception("Akun kustom tidak ditemukan")

        print(f"[3] Mencari profil target: @{target_user}...")
        
        # Pastikan Instagram aktif di foreground
        if d.app_current().get('package') != 'com.instagram.android':
            print("      -> Instagram terdeteksi tidak aktif. Membuka kembali...")
            d.app_start("com.instagram.android")
            time.sleep(5.0)
            
        # === NAVIGASI KE HALAMAN PENCARIAN (DENGAN RETRY & VERIFIKASI) ===
        search_opened = False
        print("      -> Membuka halaman Pencarian...")
        for check_search in range(5):
            # Cek jika kolom pencarian atau input teks pencarian sudah aktif/muncul di layar
            input_text = d(resourceId="com.instagram.android:id/action_bar_search_edit_text")
            search_bar = d(resourceId="com.instagram.android:id/search_bar")
            if input_text.exists or search_bar.exists:
                search_opened = True
                print("      -> Halaman Pencarian aktif.")
                break
                
            # Coba cari tombol search tab di menu bawah
            search_tab = None
            if d(resourceId="com.instagram.android:id/search_tab").exists:
                search_tab = d(resourceId="com.instagram.android:id/search_tab")
            else:
                # Pencocokan deskripsi mengandung kata kunci pencarian/jelajah
                sel = d(descriptionMatches="(?i).*(search|cari|explore|jelajahi).*", packageName="com.instagram.android")
                if sel.exists:
                    search_tab = sel
                        
            if search_tab:
                try:
                    search_tab.click()
                    print("      -> Mengklik tab Pencarian via selector...")
                    time.sleep(2.5)
                    continue
                except:
                    pass
                    
            # Fallback koordinat Y = 0.93 (Y profil/home universal) dan 0.914, baru 0.96 sebagai opsi terakhir
            print("      -> Mengklik tab Pencarian via koordinat fallback...")
            d.click(int(width * 0.30), int(height * 0.93))
            time.sleep(1.5)
            d.click(int(width * 0.30), int(height * 0.914))
            time.sleep(1.5)
            
        if not search_opened:
            print("[-] WARNING: Halaman pencarian terdeteksi belum aktif, mencoba klik koordinat langsung sekali lagi.")
            d.click(int(width * 0.30), int(height * 0.93))
            time.sleep(1.5)
            d.click(int(width * 0.30), int(height * 0.914))
            time.sleep(1.5)

        print("      Mengklik kotak input pencarian...")
        input_text = d(resourceId="com.instagram.android:id/action_bar_search_edit_text")
        search_bar = d(resourceId="com.instagram.android:id/search_bar")
        edit_text = d(className="android.widget.EditText")
        
        if input_text.exists:
            input_text.click()
        elif search_bar.exists:
            search_bar.click()
        elif edit_text.exists:
            edit_text.click()
        else:
            d.click(int(width * 0.5), int(height * 0.06))
        time.sleep(1.5)

        print(f"      Mengetik nama akun: {target_user}")
        try:
            if input_text.exists:
                input_text.clear_text()
            elif edit_text.exists:
                edit_text.clear_text()
        except Exception as e:
            print(f"      -> Info: Gagal membersihkan teks input ({e})")
        d.send_keys(target_user)
        time.sleep(2)

        d.press("enter")
        time.sleep(2.5)

        print("      Memilih profil teratas...")
        row_username = d(resourceId="com.instagram.android:id/row_search_user_username", text=target_user)
        row_username_contains = d(resourceId="com.instagram.android:id/row_search_user_username", textContains=target_user)
        akun_target_text = d(text=target_user, className="android.widget.TextView")
        akun_target_contains = d(textContains=target_user, className="android.widget.TextView")
        container_1 = d(resourceId="com.instagram.android:id/row_search_user_info_container")
        container_2 = d(resourceId="com.instagram.android:id/row_search_user_container")
        
        clicked_target = False
        for selector in [row_username, row_username_contains, akun_target_text, akun_target_contains, container_1, container_2]:
            if selector.exists:
                try:
                    selector.click()
                    clicked_target = True
                    break
                except Exception as e:
                    print(f"      -> Info: Gagal klik selector ({e})")
                    
        if not clicked_target:
            print("      -> Klik default koordinat pencarian teratas...")
            d.click(int(width * 0.5), int(height * 0.19))
            clicked_target = True

        time.sleep(3.0)

        # Verifikasi profil target berhasil terbuka
        profil_terbuka = False
        print("      -> Memverifikasi profil target berhasil dibuka...")
        for check_profil in range(4):
            # Cek apakah elemen stats profil (Postingan/Posts/Pengikut/Followers) sudah tampil di layar
            # Ini sangat penting karena stats hanya ada di halaman profil, bukan di pencarian
            has_profile_stats = d(textMatches="(?i).*(postingan|posts|pengikut|followers|mengikuti|following).*").exists
            
            # Cek tombol back (Kembali) di action bar atas (hanya ada di halaman profil target/bukan pencarian utama)
            has_back = d(resourceId="com.instagram.android:id/action_bar_button_back").exists or d(descriptionContains="Kembali").exists or d(descriptionContains="Back").exists
            
            # Profil terbuka jika tombol back ada DAN statistik profil terdeteksi di layar
            if has_back and has_profile_stats:
                profil_terbuka = True
                print("      -> Profil target berhasil dibuka!")
                break
            else:
                print(f"      -> Profil target belum terbuka (percobaan {check_profil+1}). Mengklik ulang...")
                # Tutup keyboard jika masih menghalangi layar
                d.press("back")
                time.sleep(1.5)
                # Coba klik ulang baris pencarian teratas
                for selector in [row_username, row_username_contains, container_1, container_2]:
                    if selector.exists:
                        try:
                            selector.click()
                            break
                        except Exception as e:
                            print(f"      -> Info: Gagal klik selector ({e})")
                            
                else:
                    d.click(int(width * 0.5), int(height * 0.19))
                time.sleep(3.0)

        if not profil_terbuka:
            raise Exception("Gagal membuka halaman profil target @{}".format(target_user))

        clear_any_popup_fast(d)

        print("[4] Membuka menu opsi (titik tiga)...")
        log_step("open_options", status="complete", device_id=device_pilihan, action="report")
        
        opsi_btn = d(descriptionContains="Opsi")
        options_btn = d(descriptionContains="Options")
        overflow_btn = d(resourceId="com.instagram.android:id/action_bar_overflow_menu_button")
        match_desc = d(descriptionMatches="(?i).*(opsi|option|more|lainnya).*")
        right_btn = d(resourceId="com.instagram.android:id/action_bar_right_button")
        
        menu_clicked = False
        for opt_selector in [overflow_btn, match_desc, right_btn, opsi_btn, options_btn]:
            if opt_selector.exists:
                try:
                    opt_selector.click()
                    menu_clicked = True
                    break
                except:
                    pass
        if not menu_clicked:
            print("      -> Mencoba klik koordinat default tiga titik di kanan atas...")
            d.click(int(width * 0.935), int(height * 0.054))
            menu_clicked = True
            
        time.sleep(2.5)

        # Verifikasi menu opsi terbuka
        menu_open = False
        print("      -> Memverifikasi menu opsi terbuka...")
        for verify_step in range(3):
            # Jeda agar menu selesai me-render
            time.sleep(1.5)
            # Check if any common menu option text is visible
            if d(textMatches="(?i).*(laporkan|report|blokir|block|restrict|batasi|salin url|copy profile url).*").exists:
                menu_open = True
                print("      -> Menu opsi berhasil dibuka!")
                break
            else:
                print(f"      -> Menu opsi belum terbuka (percobaan {verify_step+1}). Mengklik ulang...")
                for opt_selector in [overflow_btn, match_desc, right_btn, opsi_btn, options_btn]:
                    if opt_selector.exists:
                        try:
                            opt_selector.click()
                            break
                        except:
                            print("<<error>>")
                else:
                    d.click(int(width * 0.935), int(height * 0.054))

        if not menu_open:
            raise Exception("Gagal membuka menu opsi profil target.")

        print("[5] Klik 'Laporkan' / 'Report'...")
        log_step("click_report", status="complete", device_id=device_pilihan, action="report")
        
        clicked_report = False
        for report_text in ["Laporkan", "Laporkan...", "Report", "Report..."]:
            btn_rep = d(text=report_text)
            if btn_rep.exists:
                btn_rep.click()
                print(f"      -> Klik: '{report_text}'")
                clicked_report = True
                break
        
        if not clicked_report:
            # Cari matches case-insensitive
            btn_rep_cont = d(textMatches="(?i).*(laporkan|report).*")
            if btn_rep_cont.exists:
                print(f"      -> Klik matches: '{btn_rep_cont.info.get('text')}'")
                btn_rep_cont.click()
                clicked_report = True
                
        if not clicked_report:
            raise Exception("Tombol Laporkan/Report tidak ditemukan di menu opsi!")
            
        time.sleep(3.5)

        # Verifikasi apakah dialog/wizard lapor terbuka
        wizard_open = False
        print("      -> Memverifikasi dialog lapor terbuka...")
        for check_wiz in range(4):
            # Cek teks khas wizard lapor
            is_wiz = d(textMatches="(?i).*(laporkan|report|mengapa anda melaporkan|why are you reporting|pilih alasan|select a reason|sesuatu tentang).*").exists
            if is_wiz:
                wizard_open = True
                print("      -> Dialog lapor berhasil terbuka!")
                break
            else:
                print(f"      -> Dialog lapor belum terbuka (percobaan {check_wiz+1}). Menunggu...")
                time.sleep(2.0)
                
        if not wizard_open:
            raise Exception("Gagal masuk ke dialog/wizard Laporan Instagram.")

        print("[6] Navigasi alasan report...")
        log_step("report_wizard", status="on_progress", device_id=device_pilihan, action="report")
        alasan_sudah_dipilih = False
        opsi_diklik = set()
        laporan_selesai = False
        langkah_kosong = 0

        for loop_idx in range(25):
            time.sleep(1.5)

            # Cek jika keluar dari dialog lapor tengah jalan
            is_wiz_active = d(textMatches="(?i).*(laporkan|report|mengapa anda|why are you|pilih alasan|select a reason|sesuatu tentang|laporan terkirim|report submitted|terima kasih|thank you).*").exists
            if not is_wiz_active:
                if d(textMatches="(?i).*(selesai|done|tutup|close|laporan terkirim|report submitted).*").exists:
                    print("      -> Laporan selesai (terdeteksi tombol akhir).")
                    laporan_selesai = True
                    break
                else:
                    print("      -> Terdeteksi keluar dari dialog Laporan. Menghentikan loop.")
                    break

            # 1. Coba klik konfirmasi/submit/done terlebih dahulu
            kw_terklik = klik_konfirmasi(d)
            if kw_terklik:
                langkah_kosong = 0
                if any(f in kw_terklik.lower() for f in ["selesai", "done", "tutup", "close", "paham", "profile", "profil"]):
                    laporan_selesai = True
                    break
                continue

            # 2. Jika target alasan belum terpilih, cari target alasan di layar saat ini
            tombol_alasan_diklik = False
            if not alasan_sudah_dipilih:
                mapping_alasan = {
                    "Sesuatu tentang akun ini": ["Sesuatu tentang akun ini", "Something about this account"],
                    "Postingan tertentu": ["Postingan tertentu", "A specific post", "Something they posted"],
                    "Dia berpura-pura menjadi orang lain": ["Dia berpura-pura menjadi orang lain", "They're pretending to be someone else", "Pretending to be someone else"],
                    "Dia mungkin berusia di bawah usia minimal": ["Dia mungkin berusia di bawah usia minimal", "They may be under the minimum age", "Under the minimum age"],
                    "Akun mungkin diretas": ["Akun mungkin diretas", "Account may be hacked", "May be hacked"],
                    "Hal lain": ["Hal lain", "Something else"]
                }
                
                kandidat = mapping_alasan.get(alasan_pilihan, [alasan_pilihan])
                for opt in kandidat:
                    el_opt = d(text=opt)
                    el_opt_cont = d(textContains=opt)
                    if el_opt.exists:
                        el_opt.click()
                        print(f"      -> Alasan kustom terpilih: '{opt}'")
                        alasan_sudah_dipilih = True
                        tombol_alasan_diklik = True
                        break
                    elif el_opt_cont.exists:
                        el_opt_cont.click()
                        print(f"      -> Alasan kustom terpilih (Contains): '{opt}'")
                        alasan_sudah_dipilih = True
                        tombol_alasan_diklik = True
                        break
                        
            if tombol_alasan_diklik:
                langkah_kosong = 0
                continue

            # 3. Jika belum selesai, navigasikan via fallback kategori standar
            tombol_fallback_diklik = False
            if not laporan_selesai:
                daftar_alasan_fallback = [
                    "Sesuatu tentang akun ini", "Something about this account",
                    "Dia berpura-pura menjadi orang lain", "They're pretending to be someone else",
                    "Dia mungkin berusia di bawah usia minimal", "They may be under the minimum age",
                    "Akun mungkin diretas", "Account may be hacked",
                    "Postingan tertentu", "Something they posted",
                    "Hal lain", "Something else",
                    "Saya", "Me",
                    "Seseorang yang saya ikuti", "Someone I follow",
                    "Tokoh atau figur publik", "A celebrity or public figure",
                    "Sebuah bisnis atau organisasi", "A business or organization",
                    "Orang yang saya kenal", "Someone I know"
                ]
                for alasan in daftar_alasan_fallback:
                    if alasan not in opsi_diklik:
                        el_alasan = d(text=alasan)
                        el_alasan_cont = d(textContains=alasan)
                        if el_alasan.exists:
                            el_alasan.click()
                            print(f"      -> Alasan fallback: '{alasan}'")
                            opsi_diklik.add(alasan)
                            tombol_fallback_diklik = True
                            break
                        elif el_alasan_cont.exists:
                            el_alasan_cont.click()
                            print(f"      -> Alasan fallback (Contains): '{alasan}'")
                            opsi_diklik.add(alasan)
                            tombol_fallback_diklik = True
                            break

            if tombol_fallback_diklik:
                langkah_kosong = 0
                continue

            # 4. Klik element clickable teratas (untuk mencari jalan keluar wizard)
            if not laporan_selesai:
                semua = []
                for el in d(clickable=True):
                    try:
                        info = el.info
                        b = info.get('bounds')
                        teks = info.get('text', '') or info.get('contentDescription', '') or ''
                        teks_clean = teks.strip().lower()
                        # Jangan klik tombol profil umum, tombol back global, atau input pencarian/pengaturan
                        if b and teks.strip() and teks not in opsi_diklik:
                            if any(x in teks_clean for x in ["message", "kirim pesan", "follow", "ikuti", "following", "mengikuti", "post", "postingan", "pengikut", "followers", "search", "cari", "tulis komentar", "write a comment", "quiet mode", "mode senyap", "sleep mode"]):
                                continue
                            y = (b['top'] + b['bottom']) // 2
                            if y > height * 0.15:
                                semua.append((teks, (b['left'] + b['right']) // 2, y))
                    except Exception as e:
                        print(f"      -> Info: Gagal mengambil bounds element ({e})")
                semua.sort(key=lambda x: x[2])

                if semua:
                    teks, x, y = semua[0]
                    d.click(x, y)
                    print(f"      -> Mengklik opsi clickable: '{teks}'")
                    opsi_diklik.add(teks)
                    langkah_kosong = 0
                    continue

            # 5. Fallback langkah kosong
            langkah_kosong += 1
            if langkah_kosong >= 5:
                d.click(int(width * 0.5), int(height * 0.5))
                time.sleep(1.5)
                if langkah_kosong >= 7:
                    break

        print(f"      Status laporan: {'Selesai' if laporan_selesai else 'Terputus (Limit / Gagal)'}")
        if laporan_selesai:
            log_complete(log_id, message="Reported account successfully")
        else:
            log_error(log_id, error="Laporan terputus - limit/gagal")

    except Exception as e:
        print(f"ERROR saat proses pelaporan: {e}")
        log_error(log_id, error=str(e))

    # === ALUR KEMBALI KE BERANDA (Selalu dijalankan baik sukses, limit, maupun gagal) ===
    if d is not None:
        # Jeda sejenak untuk membiarkan modal dialog laporan selesai menutup/transisi animasinya
        time.sleep(3.0)
        print("[7] Kembali ke Beranda utama Instagram dan menyegarkan (refresh) feed...")
        try:
            print("      -> Menghentikan paksa (kill) aplikasi Instagram...")
            d.app_stop("com.instagram.android")
            time.sleep(2.0)
            
            print("      -> Membuka kembali aplikasi Instagram...")
            d.app_start("com.instagram.android")
            time.sleep(5.0)
            clear_any_popup_fast(d)
            
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
            print("      [SUKSES] Halaman Beranda berhasil di-refresh.")
        except Exception as opt_err:
            print(f"      -> Gagal kembali/refresh Beranda: {opt_err}")
            
    print("=========================================")
    print(f" PROSES REPORT SELESAI: @{target_user}")
    print("=========================================\n")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else ""
    device_id = sys.argv[2] if len(sys.argv) > 2 else "all"
    alasan = sys.argv[3] if len(sys.argv) > 3 else "Sesuatu tentang akun ini"
    my_account = sys.argv[4] if len(sys.argv) > 4 else ""
    
    bot_report(target, device_id, alasan, my_account)