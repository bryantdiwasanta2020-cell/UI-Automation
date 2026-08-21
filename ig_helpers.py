import time
import uiautomator2 as u2

def connect_adb(device_pilihan="all", action=None, step_label="[1] Menghubungkan ke perangkat Android via ADB..."):
    """
    Menghubungkan ke perangkat Android via ADB / uiautomator2,
    mengatur orientasi layar ke Portrait ('n'), serta mengembalikan instance uiautomator2 device.
    """
    if action:
        from activity_logger import log_step
        log_step("connect_device", status="complete", device_id=device_pilihan, action=action)
        
    print(step_label)
    if not device_pilihan or device_pilihan == "all" or device_pilihan == "Semua Akun Aktif" or device_pilihan == "Semua Akun Aktif (18 Device)":
        d = u2.connect()
    else:
        if isinstance(device_pilihan, list):
            device_pilihan = device_pilihan[0] if device_pilihan else "all"
        if device_pilihan == "all" or device_pilihan == "Semua Akun Aktif" or device_pilihan == "Semua Akun Aktif (18 Device)":
            d = u2.connect()
        else:
            d = u2.connect(device_pilihan)

    print("[SYSTEM] Mengatur orientasi layar ke Portrait...")
    try:
        d.freeze_rotation(False)
        d.set_orientation("n")
    except Exception as e:
        print(f"[SYSTEM] Gagal mengatur orientasi layar ke Portrait: {e}")
    time.sleep(1)
    setup_system_popup_watcher(d)
    check_and_clear_system_popups(d)
    return d

def open_instagram(d, device_pilihan="all", action=None, delay=5.0, step_label="[2] Membuka aplikasi Instagram..."):
    """
    Membuka aplikasi Instagram, mencatat step log_step('open_app'),
    serta melakukan jeda tunggu terstandar.
    """
    if action:
        from activity_logger import log_step
        log_step("open_app", status="complete", device_id=device_pilihan, action=action)
        
    print(step_label)
    d.app_start("com.instagram.android")
    time.sleep(delay)

def setup_system_popup_watcher(d):
    """
    Mengaktifkan watcher uiautomator2 di latar belakang untuk mendeteksi
    dan menutup otomatis popup sistem / telepon / USSD / operator / popup sembarang.
    """
    try:
        if hasattr(d, 'watcher'):
            d.watcher.reset()
            d.watcher('SYS_MMI_OK').when('//*[contains(@text, "invalid MMI") or contains(@text, "Connection problem") or contains(@text, "MMI code")]/ancestor::*//*[@resource-id="android:id/button1" or @text="OK"]').click()
            d.watcher('SYS_CANCEL_BTN2').when('//*[@resource-id="android:id/button2" and @package!="com.instagram.android"]').click()
            d.watcher('SYS_CANCEL_TXT').when('//*[@package!="com.instagram.android" and (@text="Cancel" or @text="CANCEL" or @text="Batal" or @text="BATAL")]').click()
            d.watcher('SYS_PHONE_CANCEL').when('//*[@package="com.android.phone"]//*[@resource-id="android:id/button2"]').click()
            d.watcher.start(1.0)
            print("[SYSTEM] Watcher popup sistem otomatis aktif (background 1s interval).")
            return True
    except Exception as e:
        print(f"[SYSTEM] Warning: Gagal mengaktifkan watcher popup sistem: {e}")
    return False

def check_and_clear_system_popups(d):
    """
    Pemeriksaan langsung untuk mendeteksi & menutup popup sistem/telepon/USSD/operator.
    """
    try:
        mmi_popup = d(textContains="invalid MMI") or d(textContains="Connection problem") or d(textContains="MMI code")
        if mmi_popup.exists:
            btn_ok = d(resourceId="android:id/button1") or d(text="OK") or d(text="Ok")
            if btn_ok.exists:
                print("[SYSTEM POPUP] Mendeteksi popup 'Connection problem or invalid MMI code.'. Mengklik OK...")
                btn_ok.click()
                time.sleep(1.0)
                return True

        btn2 = d(resourceId="android:id/button2")
        if btn2.exists:
            try:
                curr = d.app_current()
                pkg = curr.get("package", "") if isinstance(curr, dict) else ""
            except:
                pkg = ""
            if pkg != "com.instagram.android":
                btn_text = btn2.info.get("text", "") or btn2.info.get("contentDescription", "") or "Cancel"
                print(f"[SYSTEM POPUP] Mendeteksi popup sistem dengan tombol button2 ('{btn_text}'). Mengklik Cancel...")
                btn2.click()
                time.sleep(1.0)
                return True

        try:
            curr = d.app_current()
            pkg = curr.get("package", "") if isinstance(curr, dict) else ""
        except Exception:
            pkg = ""

        if pkg and pkg not in ["com.instagram.android", "com.google.android.youtube"]:
            for selector in [
                d(textMatches="(?i)^(cancel|batal|tutup|close|dismiss|abaikan|ignore)$"),
                d(descriptionMatches="(?i)^(cancel|batal|tutup|close|dismiss|abaikan|ignore)$"),
                d(resourceId="android:id/button2"),
                d(resourceId="android:id/button1", textMatches="(?i)^(cancel|batal)$")
            ]:
                if selector.exists:
                    txt = selector.info.get("text", "") or selector.info.get("contentDescription", "")
                    print(f"[SYSTEM POPUP] Mendeteksi popup sistem ({pkg}) dengan tombol '{txt}'. Mengklik Cancel...")
                    selector.click()
                    time.sleep(1.0)
                    return True

        for cancel_sel in [
            d(text="Cancel"), d(text="Batal"), d(text="CANCEL"), d(text="BATAL"),
            d(description="Cancel"), d(description="Batal")
        ]:
            if cancel_sel.exists:
                info = cancel_sel.info
                if info.get("className") in ["android.widget.Button", "android.widget.TextView"]:
                    print(f"[SYSTEM POPUP] Mendeteksi tombol '{info.get('text')}' di layar. Mengklik Cancel...")
                    cancel_sel.click()
                    time.sleep(1.0)
                    return True

    except Exception as e:
        print(f"[SYSTEM POPUP] Warning saat memproses popup sistem: {e}")

    return False
