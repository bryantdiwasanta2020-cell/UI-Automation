import uiautomator2 as u2

try:
    print("Menghubungkan ke HP via UiAutomator2...")
    d = u2.connect()
    
    print("\n=== INFORMASI APLIKASI AKTIF ===")
    current = d.app_current()
    print(f"Package: {current.get('package', 'Unknown')}")
    print(f"Activity: {current.get('activity', 'Unknown')}")
    
    print("\n=== DAFTAR ELEMEN TEKS YANG TERLIHAT DI LAYAR ===")
    # Dapatkan seluruh elemen di layar
    elements = d(classNameMatches=".*")
    found_any = False
    for i in range(elements.count):
        try:
            el = elements[i]
            text = el.info.get("text", "")
            desc = el.info.get("contentDescription", "")
            cid = el.info.get("resourceName", "")
            cname = el.info.get("className", "")
            
            if text or desc:
                found_any = True
                print(f"[{cname}] ID: {cid} | Text: '{text}' | Desc: '{desc}'")
        except Exception:
            pass
            
    if not found_any:
        print("Tidak ada elemen dengan teks/deskripsi yang terdeteksi.")
        
    print("\n================================================")
except Exception as e:
    print(f"Terjadi kesalahan diagnosa: {e}")
