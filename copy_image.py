import shutil
import os

src = "/home/me/.gemini/antigravity-ide/brain/5428f0a9-13a0-4509-9ada-c2467892bec9/grizzly_chips_1784812170531.png"
dst_png = "/home/me/TEAM/automation_2026/instagram/grizzly_chips.png"
dst_jpg = "/home/me/TEAM/automation_2026/instagram/grizzly_chips.jpg"

try:
    if os.path.exists(src):
        shutil.copy(src, dst_png)
        shutil.copy(src, dst_jpg)
        print("[SUCCESS] Foto berhasil disalin ke folder instagram/ sebagai grizzly_chips.png dan grizzly_chips.jpg!")
    else:
        print(f"[ERROR] Source file tidak ditemukan di: {src}")
except Exception as e:
    print(f"[ERROR] Gagal menyalin file: {e}")
