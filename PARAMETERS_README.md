# Dokumentasi Parameter Instagram Automation Bots

Berkas ini berisi panduan lengkap parameter untuk menjalankan masing-masing skrip bot Instagram, baik secara manual melalui **Terminal (CLI)** maupun melalui antrean **API Server (FastAPI)**.

---

## 💡 Fitur Eksekusi Multi-Device (Banyak HP Sekaligus secara Paralel)

Seluruh skrip bot utama mendukung eksekusi secara paralel pada banyak HP secara bersamaan. Fitur ini dapat dipicu melalui parameter `device_id` / `device_pilihan`:

1. **Banyak HP Tertentu (Comma-Separated):**
   Pisahkan Serial Number/ID perangkat menggunakan koma tanpa spasi.
   *Contoh:*
   ```bash
   python3 bot_ig_like.py "cristiano" "R9RY801LRPW,RF8N90XYZ12"
   ```
   
2. **Semua HP Terkoneksi (`all`):**
   Masukkan `"all"` (atau kata kunci `"semua"`) sebagai parameter device ID. Bot akan otomatis memindai seluruh perangkat yang aktif via ADB dan mengeksekusi perintah secara paralel menggunakan multi-threading.
   *Contoh:*
   ```bash
   python3 bot_ig_farming.py all 10
   ```

---

## 1. Bot Login (`bot_instagram_login.py`)
Digunakan untuk melakukan proses login akun Instagram, membersihkan akun tertaut (landing page), membatalkan Google Smart Lock, serta membersihkan pop-up beranda.

* **Parameter CLI**:
  ```bash
  python3 bot_instagram_login.py <username> <password> <device_id>
  ```
  * **Contoh**: 
    ```bash
    python3 bot_instagram_login.py "lukyytris13" "Bryant12345678" "R9RY801LRPW"
    ```

* **Parameter API Server (`/api/jalankan-bot-login`)**: 
  * `target` (String): Username Instagram (Form Data).
  * `password` (String): Password Instagram (Form Data).
  * `device_id` (String): ID perangkat (default: `"all"`).

---

## 2. Bot Like (`bot_ig_like.py`)
Digunakan untuk menyukai (like) postingan target via URL, ATAU mencari kata kunci/hashtag di Instagram dan menyukai sejumlah postingan secara massal.

* **Parameter CLI**:
  * **Mode 1: `target_url` (Like Postingan Target via URL)**
    *Format:*
    ```bash
    python3 bot_ig_like.py "<target_post_url>" [device_id] [my_account] target_url
    ```
    
    *Contoh:*
    ```bash
    python3 bot_ig_like.py "https://www.instagram.com/p/DbGhqbKE-Bn/" R9RY801LRPW christinesienap target_url
    ```
  * **Mode 2: `normal` (Like Berdasarkan Keyword/Hashtag Massal)**
    *Format:*
    ```bash
    python3 bot_ig_like.py "<keyword_atau_hashtag>" [limit_angka] [device_id] [my_account] normal
    ```
    *Contoh:*
    ```bash
    python3 bot_ig_like.py "kucing" 10 R9RY801LRPW christinesienap normal
    ```
  * **Kompatibilitas Mundur (Auto-detect Tanpa Mode):**
    ```bash
    python3 bot_ig_like.py "<target_user_atau_url>" [device_id] [my_account]
    python3 bot_ig_like.py "<keyword_atau_hashtag>" <limit_angka> [device_id] [my_account]
    ```

* **Parameter API Server (`/api/jalankan-bot-like` & `/api/jalankan-bot-like-by-keyword`)**:
  * `/api/jalankan-bot-like` (Target):
    * `target` (String): Username target atau URL postingan langsung.
    * `device_id` (String): ID perangkat (default: `"all"`).
    * `my_account` (String): Nama akun Anda untuk beralih (opsional).
  * `/api/jalankan-bot-like-by-keyword` (Keyword):
    * `keyword` (String): Kata kunci pencarian / hashtag.
    * `limit` (Integer): Jumlah postingan yang disukai (default: `10`).

---

## 3. Bot Comment (`bot_ig_comment.py`)
Digunakan untuk mengirimkan komentar pada postingan target via URL, ATAU mencari kata kunci/hashtag di Instagram dan mengomentari postingan secara massal.

* **Parameter CLI**:
  * **Mode 1: `target_url` (Komentar Target via URL)**
    *Format:*
    ```bash
    python3 bot_ig_comment.py "<target_post_url>" "<isi_komentar>" [device_id] [my_account] target_url
    ```
    *Contoh:*
    ```bash
    python3 bot_ig_comment.py "https://www.instagram.com/p/DbGhqbKE-Bn/" "Keren sekali!" R9RY801LRPW "akun_saya_123" target_url
    ```
  * **Mode 2: `normal` (Komentar Berdasarkan Keyword/Hashtag Massal)**
    *Format:*
    ```bash
    python3 bot_ig_comment.py "<keyword_atau_hashtag>" [limit_angka] "<isi_komentar>" [device_id] [my_account] normal
    ```
    *Contoh:*
    ```bash
    python3 bot_ig_comment.py "fifa" 5 "Mantap!" R9RY801LRPW "akun_saya_123" normal
    ```
  * **Kompatibilitas Mundur (Auto-detect Tanpa Mode):**
    ```bash
    python3 bot_ig_comment.py "<target_user_atau_url>" "<isi_komentar>" [device_id] [my_account]
    python3 bot_ig_comment.py "<keyword_atau_hashtag>" <limit_angka> "<isi_komentar>" [device_id] [my_account]
    ```

* **Parameter API Server (`/api/jalankan-bot-comment`)**:
  * `target` (String): Username target, URL postingan langsung, atau kata kunci pencarian.
  * `komentar` (String): Teks komentar manual (opsional).
  * `limit` (Integer): Jumlah postingan yang dikomentari jika mode keyword (opsional, default: `5`).
  * `device_id` (String): ID perangkat (default: `"all"`).
  * `my_account` (String): Nama akun Anda untuk beralih (opsional).

---

## 4. Bot Repost (`bot_ig_repost.py`)
Digunakan untuk men-download media postingan target (via username/URL) dan mempostingnya kembali ke akun Anda sendiri, ATAU mencari keyword/hashtag dan merepost postingan secara beruntun.

* **Parameter CLI**:
  * **Mode 1: `username` (Repost dari Target Username - Tanpa Mode Tambahan)**
    *Format:*
    ```bash
    python3 bot_ig_repost.py <target_username> [caption_type] [custom_caption] [device_id] [my_account]
    ```
    *Contoh:*
    ```bash
    python3 bot_ig_repost.py "cristiano" credit "" R9RY801LRPW "akun_saya"
    ```
  * **Mode 2: `target_url` (Repost Langsung dari URL Postingan)**
    *Format:*
    ```bash
    python3 bot_ig_repost.py "<post_url>" [caption_type] [custom_caption] [device_id] [my_account] target_url
    ```
    *Contoh:*
    ```bash
    python3 bot_ig_repost.py "https://www.instagram.com/p/DbGhqbKE-Bn/" custom "Hasil repost" R9RY801LRPW "akun_saya" target_url
    ```
  * **Mode 3: `normal` (Repost Keyword Massal)**  
    *Format:*
    ```bash
    python3 bot_ig_repost.py "<keyword_atau_hashtag>" [limit] [device_id] [my_account] normal
    ```
    *Contoh:*
    ```bash
    python3 bot_ig_repost.py "kucing" 5 R9RY801LRPW "akun_saya" normal
    ```
  * **Kompatibilitas Mundur (Auto-detect Tanpa Mode):**
    ```bash
    python3 bot_ig_repost.py "<target_user_atau_url>" [caption_type] [custom_caption] [device_id] [my_account]
    python3 bot_ig_repost.py "<keyword_atau_hashtag>" <limit_angka> [device_id] [my_account]
    ```

* **Parameter API Server (`/api/jalankan-bot-repost`)**:
  * `target` (String): Username target, URL postingan, atau keyword/hashtag pencarian.
  * `caption_type` (String): Pilihan caption (`"credit"`, `"custom"`, atau `"blank"`).
  * `custom_caption` (String): Teks caption kustom jika tipe caption adalah `"custom"`.
  * `limit` (Integer): Jumlah postingan yang ingin diposting ulang jika mode keyword (default: `5`).
  * `device_id` (String): ID perangkat (default: `"all"`).
  * `my_account` (String): Nama akun Anda untuk beralih (opsional).

---

## 5. Bot Farming (`bot_ig_farming.py`)
Digunakan untuk melakukan penjelajahan beranda secara otomatis (scrolling, menyukai postingan random, berinteraksi dengan story/reels) agar aktivitas akun terlihat organik dan menghindari ban.

* **Parameter CLI**:
  ```bash
  python3 bot_ig_farming.py <device_id> <jumlah_post_farm>
  ```
  * **Contoh (Farming 20 postingan)**: 
    ```bash
    python3 bot_ig_farming.py R9RY801LRPW 20
    ```

* **Parameter API Server (`/api/jalankan-bot-farming`)**:
  * `device_id` (String): ID perangkat (default: `"all"`).
  * `jumlah` (Integer): Jumlah postingan yang akan dijelajahi (Form Data, default: `10`).

---

## 7. Bot Instagram Post Unified (`bot_ig_post.py`)
Menggabungkan fungsionalitas unggah Feed (post biasa), Reels, dan Story ke dalam satu berkas terpadu dengan penyebutan mode eksplisit di parameter awal.

* **Parameter CLI**:
  * **Mode 1: `post` (Posting Feed Biasa)**
    *Format:*
    ```bash
    python3 bot_ig_post.py post "<file_path>" "[caption]" [device_id] [my_account]
    ```
    *Contoh:*
    ```bash
    python3 bot_ig_post.py post "/home/me/TEAM/automation_2026/instagram/gambar.png" "Ini caption feed!" R9RY801LRPW
    ```
  * **Mode 2: `reels` (Posting Reels Video)**
    *Format:*
    ```bash
    python3 bot_ig_post.py reels "<file_path>" "[caption]" [device_id] [my_account]
    ```
    *Contoh:*
    ```bash
    python3 bot_ig_post.py reels "/home/me/TEAM/automation_2026/instagram/video.mp4" "Ini reels caption!" R9RY801LRPW
    ```
  * **Mode 3: `story` (Posting Story)**
    *Format:*
    ```bash
    python3 bot_ig_post.py story "<file_path>" [device_id] [my_account]
    ```
    *Contoh:*
    ```bash
    python3 bot_ig_post.py story "/home/me/TEAM/automation_2026/instagram/gambar.png" R9RY801LRPW
    ```
  * **Kompatibilitas Mundur (Auto-detect Tanpa Mode):**
    ```bash
    python3 bot_ig_post.py "<file_path>" [device_id] [my_account]
    python3 bot_ig_post.py "<file_path>" "<caption_text>" [device_id] [my_account]
    ```

### Parameter API Server
API server lama masih dapat dipanggil secara transparan:
* **Feed (`/api/jalankan-bot-post`)**
* **Reels (`/api/jalankan-bot-post-reels`)**
* **Story (`/api/jalankan-bot-post-story`)**
  * `file_media` (File): Berkas gambar atau video.
  * `caption` (String): Deskripsi postingan (Form Data, hanya untuk Feed & Reels).
  * `device_id` (String): ID perangkat (default: `"all"`).
  * `operator` (String): Nama operator (default: `"Admin Utama"`).
  * `waktu_eksekusi` (String): Waktu penjadwalan (opsional).

---

## 10. Bot Follow Orang (`bot_ig_follow_orang.py`)
Digunakan untuk mem-follow akun target secara otomatis. Mendukung navigasi langsung ke URL/Username profil target tertentu, atau melakukan pemindaian scroll & follow otomatis dari daftar aktivitas Notifikasi.

* **Parameter CLI**:
  ```bash
  python3 bot_ig_follow_orang.py [target_url] [device_id] [my_account]
  ```
  * **Contoh (Follow Spesifik Profil/Username)**: 
    ```bash
    python3 bot_ig_follow_orang.py "cristiano" R9RY801LRPW
    ```
  * **Contoh dengan Ganti Akun Aktif**: 
    ```bash
    python3 bot_ig_follow_orang.py "https://www.instagram.com/cristiano/" R9RY801LRPW "akun_saya_123"
    ```
  * **Contoh (Follow dari Notifikasi / Lonceng)**: 
    ```bash
    python3 bot_ig_follow_orang.py "" R9RY801LRPW
    ```

* **Parameter API Server (`/api/jalankan-bot-follow-orang`)**:
  * `target_url` (String): Username target atau URL profil langsung (opsional, kosongkan untuk mengambil dari daftar Notifikasi).
  * `my_account` (String): Nama akun Anda untuk beralih (opsional).
  * `device_id` (String): ID perangkat (default: `"all"`).
  * `operator` (String): Nama operator (default: `"Admin Utama"`).
  * `waktu_eksekusi` (String): Waktu penjadwalan (opsional).

---

## 11. Bot Report (`bot_ig_report.py`)
Digunakan untuk melaporkan (report) akun target secara otomatis dengan alasan tertentu.

* **Parameter CLI**:
  ```bash
  python3 bot_ig_report.py <target> [device_id] [alasan] [my_account]
  ```
  * **Contoh**: 
    ```bash
    python3 bot_ig_report.py "spam_account" R9RY801LRPW "Dia berpura-pura menjadi orang lain" "akun_saya_123"
    ```

* **Parameter API Server (`/api/jalankan-bot-report`)**:
  * `target` (String): Username target yang akan dilaporkan.
  * `alasan` (String): Alasan pelaporan (default: `"Sesuatu tentang akun ini"`).
  * `my_account` (String): Nama akun Anda untuk beralih (opsional).
  * `device_id` (String): ID perangkat (default: `"all"`).
  * `operator` (String): Nama operator (default: `"Admin Utama"`).
  * `waktu_eksekusi` (String): Waktu penjadwalan (opsional).

---

## 12. Bot Switch Account (`switch_akun_ig.py`)
Digunakan untuk beralih (switch) akun aktif Instagram pada perangkat tertentu secara otomatis.

* **Parameter CLI**:
  ```bash
  python3 switch_akun_ig.py <target_username> [device_id]
  ```
  * **Contoh**: 
    ```bash
    python3 switch_akun_ig.py "lukyytris13" R9RY801LRPW
    ```

---

## 13. Bot Logout Account (`bot_instagram_logout.py`)
Digunakan untuk melakukan proses logout akun Instagrram dai perangkat Android, mendukung mode logout satu akun saja atau seluruh akun sekaligus.

* **Parameter CLI**:
  ```bash
  python3 bot_instagram_logout.py [device_id] [mode]
  ```
  * **Contoh (Logout Satu Akun saja)**: 
    ```bash
    python3 bot_instagram_logout.py R9RY801LRPW single
    ```
  * **Contoh (Logout Semua Akun)**: 
    ```bash
    python3 bot_instagram_logout.py R9RY801LRPW all
    ```

* **Parameter API Server (`/api/jalankan-bot-logout`)**:
  * `device_id` (String): ID perangkat (default: `"all"`).
  * `mode` (String): Mode logout (`"single"` / `"all"`).

---

## 14. Bot Scraper Target (`bot_ig_scraper.py`)
Digunakan untuk mengekstrak data pengikut (followers) dari akun kompetitor atau daftar komentator (comments) dari postingan tertentu secara otomatis. Hasil ekstraksi disaring dan disimpan ke dalam file teks `scraped_targets.txt`.

* **Parameter CLI**:
  ```bash
  python3 bot_ig_scraper.py <target> [tipe] [limit] [device_id]
  ```
  * **Contoh (Scrape Followers)**: 
    ```bash
    python3 bot_ig_scraper.py "cristiano" followers 100 R9RY801LRPW
    ```
  * **Contoh (Scrape Komentator dari URL Postingan)**: 
    ```bash
    python3 bot_ig_scraper.py "https://www.instagram.com/p/DbGhqbKE-Bn/" comments 50 R9RY801LRPW
    ```

* **Parameter API Server (`/api/jalankan-bot-scraper`)**:
  * `target_competitor` (String): Username target kompetitor atau URL postingan langsung (Form Data).
  * `scrape_type` (String): Tipe scraping (`"followers"` / `"comments"`, default: `"followers"`).
  * `limit` (Integer): Jumlah target maksimal yang ingin diekstrak (default: `50`).
  * `device_id` (String): ID perangkat (default: `"all"`).
  * `operator` (String): Nama operator (default: `"Admin Utama"`).
  * `waktu_eksekusi` (String): Waktu penjadwalan (opsional).

---

## 15. Bot Edit Profile (`bot_ig_profile.py`)
Digunakan untuk mengubah nama tampilan, username, bio, dan foto profil akun Instagram secara otomatis.

* **Parameter CLI**:
  ```bash
  python3 bot_ig_profile.py <nama> <username> <bio> <avatar_path> [device_id]
  ```
  * *Catatan:* Gunakan tanda strip (`"-"`) pada parameter tertentu jika tidak ingin diubah.
  * **Contoh (Mengubah Nama dan Bio)**:
    ```bash
    python3 bot_ig_profile.py "Budi Santoso" "-" "Akun Resmi Budi" "-" "R9RY801LRPW"
    ```
  * **Contoh (Hanya Mengubah Foto Profil)**:
    ```bash
    python3 bot_ig_profile.py "-" "-" "-" "/home/me/TEAM/automation_2026/instagram/gambar.png" "R9RY801LRPW"
    ```

* **Parameter API Server (`/api/jalankan-bot-profile`)**:
  * `nama` (String, opsional): Nama tampilan baru (Form Data).
  * `username` (String, opsional): Username baru (Form Data).
  * `bio` (String, opsional): Deskripsi bio baru (Form Data).
  * `file_avatar` (File, opsional): Berkas file gambar foto profil (Multipart/Form-Data).
  * `device_id` (String): ID perangkat (default: `"all"`).
  * `operator` (String): Nama operator (default: `"Admin Utama"`).
  * `waktu_eksekusi` (String): Waktu penjadwalan (opsional).

---

## 16. Bot Check Akun Perangkat (`check_akun_device.py`)
Digunakan untuk mendeteksi dan menampilkan daftar username akun Instagram yang terdaftar/aktif pada perangkat tertentu secara otomatis (baik dalam posisi login maupun logout).

* **Parameter CLI**:
  ```bash
  python3 check_akun_device.py [device_id]
  ```
  * **Contoh**: 
    ```bash
    python3 check_akun_device.py R9RY801LRPW
    ```
