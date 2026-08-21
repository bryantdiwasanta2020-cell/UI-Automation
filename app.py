from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import asyncio
import os
import sys
import subprocess
import json
import sqlite3
import hashlib
import secrets


app = FastAPI()

# ========================================================
# PENGATURAN CORS (DITARUH DI ATAS AGAR ANTI-BLOCK BROWSER)
# ========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)   

# Folder tempat menyimpan file upload media untuk kebutuhan post
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Inisialisasi database SQLite untuk antrean bot
DATABASE_FILE = "bot_queue.db"

def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            operator TEXT DEFAULT 'Admin Utama',
            waktu_eksekusi TEXT,
            device_id TEXT DEFAULT 'all',
            status TEXT DEFAULT 'PENDING',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            started_at TEXT,
            completed_at TEXT,
            error_message TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'Super Administrator',
            name TEXT DEFAULT 'Admin Root',
            avatar TEXT DEFAULT 'https://lh3.googleusercontent.com/aida-public/AB6AXuCu2vCTOSPK5r3-TblvZEKXEhPN0jWhZUcZb3MIu74ukghYOhv7fNHlM4ZakDjT2XI34MlwBUsgjpdSlJrCZSD9gtL02HuxD0zigQIfVdI-4OP49L_QIh6uG1_VfOp9vKNGBD7N5Cx9CwCzOwblkOl-m49xW-vfvXyBY4bRXySWef8Taum8m5wtwCOzZ3xtFL8TXxiZlVUecOX1fDy3AvcphT5dowIJk4TybtpOUDiA1K5d0BGWLDySs1tMLHF2nojK20BKgHCpewM'
        )
    """)
    # Check if users table is empty, if so, seed default user
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        password_plain = "admin123"
        password_hash = hashlib.sha256(password_plain.encode('utf-8')).hexdigest()
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, name)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", "admin@example.com", password_hash, "Super Administrator", "Admin Root"))
    conn.commit()
    conn.close()

init_db()

def execute_adb_command():
    # Daftar pilihan lokasi file executable adb
    adb_choices = [
        "adb",  # Mencoba adb yang terdaftar di system PATH
        r"C:\platform-tools-latest-windows\platform-tools\adb.exe",
        r"C:\platform-tools\adb.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe")
    ]
    
    last_error = None
    for adb_bin in adb_choices:
        try:
            output = subprocess.check_output([adb_bin, "devices"]).decode("utf-8")
            return adb_bin, output
        except Exception as e:
            last_error = e
            continue
            
    raise Exception(f"Tidak dapat menemukan adb di system PATH atau folder platform-tools standar. Error: {last_error}")

def is_instagram_active(adb_bin, device_id):
    try:
        # Gunakan sh -c agar shell pipe '|' diproses dengan benar di HP/emulator (sangat cepat, <50ms)
        cmd = [adb_bin, "-s", device_id, "shell", "sh", "-c", "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'"]
        output = subprocess.check_output(cmd, timeout=1.2).decode("utf-8", errors="ignore")
        if "com.instagram.android" in output or "com.instagram.lite" in output:
            return True
            
        # Fallback: periksa resumed activity di tumpukan activity manager
        cmd = [adb_bin, "-s", device_id, "shell", "sh", "-c", "dumpsys activity | grep -E 'mResumedActivity|topActivity'"]
        output = subprocess.check_output(cmd, timeout=1.2).decode("utf-8", errors="ignore")
        if "com.instagram.android" in output or "com.instagram.lite" in output:
            return True
            
        return False
    except Exception:
        return False


# Helper untuk memasukkan job ke antrean database
def queue_job(command_type: str, payload: dict, operator: str, waktu_eksekusi: str, device_id: str):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (command_type, payload, operator, waktu_eksekusi, device_id, status)
        VALUES (?, ?, ?, ?, ?, 'PENDING')
    """, (command_type, json.dumps(payload), operator, waktu_eksekusi, device_id))
    conn.commit()
    conn.close()

# ========================================================
# RUTE API 1: PENGHITUNG ANGKA KOTAK STATISTIK DASHBOARD
# ========================================================
@app.get("/api/statistik")
async def get_statistik():
    # 1. Hitung data riil Sukses & Gagal + Waktu Grafik dari file activity_logs.json
    sukses_count = 0
    gagal_count = 0
    h00 = h06 = h12 = h18 = h_skrg = 0
    logs = []
    
    log_file = "activity.logs.json" if os.path.exists("activity.logs.json") else "activity_logs.json"
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                content = f.read().strip()
            
            parsed_logs = []
            if content:
                # Coba parse sebagai JSON Array
                if content.startswith("[") and content.endswith("]"):
                    try:
                        parsed_logs = json.loads(content)
                    except:
                        pass
                # Jika gagal atau bukan array, parse sebagai JSON Lines
                if not parsed_logs:
                    for line in content.splitlines():
                        line = line.strip()
                        if line:
                            try:
                                parsed_logs.append(json.loads(line))
                            except:
                                pass
                                
            if isinstance(parsed_logs, list):
                logs = parsed_logs
                sukses_count = sum(1 for l in logs if l.get("status", "").lower() in ("sukses", "complete"))
                gagal_count = sum(1 for l in logs if l.get("status", "").lower() in ("gagal", "error"))
                
                for l in logs:
                    waktu_str = l.get("waktu", "") or l.get("timestamp", "")
                    if waktu_str:
                        try:
                            waktu_clean = waktu_str.strip()
                            if "T" in waktu_clean: # format ISO timestamp dari activity_logger baru
                                # cth: 2026-07-29T10:27:00+07:00
                                time_part = waktu_clean.split("T")[1]
                                jam = int(time_part.split(":")[0])
                            else:
                                if " " in waktu_clean:
                                    waktu_clean = waktu_clean.split(" ")[1]
                                jam = int(waktu_clean.split(":")[0])
                            
                            if 0 <= jam < 6: h00 += 1
                            elif 6 <= jam < 12: h06 += 1
                            elif 12 <= jam < 18: h12 += 1
                            elif 18 <= jam <= 23: h18 += 1
                        except:
                            pass
        except Exception as e:
            print(f" Gagal membaca JSON log: {e}")

    # Batang SKRG diisi nilai total sukses saat ini sebagai indikator aktivitas teratas
    h_skrg = sukses_count

    # 2. Hitung Antrean riil dan ambil log aktif (PENDING / RUNNING) dari SQLite
    antrean_count = 0
    active_logs = []
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        # Hitung job yang statusnya benar-benar PENDING
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'PENDING'")
        antrean_count = cursor.fetchone()[0]
        
        # Ambil daftar job yang sedang antre (PENDING) atau sedang jalan (RUNNING)
        cursor.execute("""
            SELECT command_type, payload, operator, waktu_eksekusi, device_id, status, created_at, started_at
            FROM jobs 
            WHERE status IN ('PENDING', 'RUNNING')
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        for r in rows:
            cmd_type, payload_str, op, w_eks, dev_id, status, cr_at, st_at = r
            try:
                payload = json.loads(payload_str)
            except:
                payload = {}
            
            act_map = {
                "like": "LIKE POST",
                "comment": "COMMENT POST",
                "post": "UPLOAD POST",
                "post_story": "UPLOAD STORY",
                "post_reels": "UPLOAD REELS",
                "report": "REPORT ACCOUNT",
                "share": "SHARE POST",
                "chat": "SEND DM",
                "manage": "MANAGE ACCOUNT",
                "profile": "EDIT PROFILE",
                "repost": "REPOST POST",
                "login": "LOGIN ACCOUNT",
                "fb_login": "FB LOGIN",
                "fb_like": "FB LIKE",
                "fb_comment": "FB COMMENT",
                "fb_post": "FB POST",
                "farming": "IG FARMING",
                "scraper": "SCRAPER DATA"
            }
            aktivitas = act_map.get(cmd_type, f"{cmd_type.upper()}")
            target = payload.get("target", "") or payload.get("fb_target", "") or payload.get("fb_page_id", "") or payload.get("file_path", "") or payload.get("target_competitor", "") or "-"
            
            waktu_log = cr_at
            if status == "RUNNING" and st_at:
                waktu_log = st_at
            elif w_eks:
                waktu_log = f"{w_eks} (Scheduled)"
                
            active_logs.append({
                "waktu": waktu_log,
                "akun": dev_id,
                "aktivitas": aktivitas,
                "target": target,
                "status": status # 'PENDING' atau 'RUNNING'
            })
        conn.close()
    except Exception as db_err:
        print(f"Gagal memproses data antrean dari DB: {db_err}")

    # Gabungkan log antrean aktif (Pending/Running) ke bagian depan history log
    merged_logs = active_logs + logs

    # 3. Hitung HP Android Nyata + Ambil teks mentah Terminal ADB
    device_count = 0
    terminal_output = "$ adb devices\nList of devices attached\n"
    instagram_online_devices = []
    try:
        adb_bin, output = execute_adb_command()
        terminal_output = f"$ {adb_bin} devices\n{output.strip()}"
        lines = output.strip().split("\n")[1:]
        
        connected_devices = []
        for line in lines:
            if line.strip() and len(line.split()) >= 2 and "device" in line.split()[1]:
                connected_devices.append(line.split()[0])
                
        device_count = len(connected_devices)
        
        # Periksa apakah aplikasi Instagram sedang aktif di masing-masing perangkat
        for dev_id in connected_devices:
            if is_instagram_active(adb_bin, dev_id):
                instagram_online_devices.append(dev_id)
                
    except Exception as adb_error:
        terminal_output += f" Gagal membaca adb lokal secara riil.\nDetail: {adb_error}"
        device_count = 0

    # 4. RETURN DATA UTUH
    return {
        "sukses": sukses_count,
        "gagal": gagal_count,
        "device_aktif": device_count,
        "antrean": antrean_count,
        "terminal": terminal_output,
        "instagram_online_devices": instagram_online_devices,
        "grafik": {
            "h00": h00,
            "h06": h06,
            "h12": h12,
            "h18": h18,
            "skrg": h_skrg
        },
        "logs": merged_logs
    }

# ========================================================
# RUTE API UTAMA KENDALI BOT (MASUK QUEUE SQLITE)
# ========================================================

# 1. BOT LIKE
@app.post("/api/jalankan-bot-like")
async def run_bot_like(
    target: str = Form(...),
    platform: str = Form('instagram'),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        if platform == 'facebook':
            # Expect Facebook fields in the request form
            fb_page_id = Form(None)  # placeholder, actual extraction done below
            fb_target = Form(...)
            fb_token = Form(...)
            # Since FastAPI cannot directly read dynamic forms inside this function, we will retrieve from request
            # However for simplicity, we rely on Form fields above; using default values will work if they are provided.
            # Queue Facebook Like job
            payload = {"fb_page_id": fb_page_id, "fb_target": fb_target, "fb_token": fb_token}
            queue_job("fb_like", payload, operator, waktu_eksekusi, device_id)
            return {"status": "success", "message": f"Facebook Like job queued by {operator}!"}
        else:
            # Existing Instagram like handling
            queue_job("like", {"target": target}, operator, waktu_eksekusi, device_id)
            return {"status": "success", "message": f"Skrip Like berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}
    # 1c. BOT LIKE BY KEYWORD
@app.post("/api/jalankan-bot-like-by-keyword")
async def run_bot_like_by_keyword(
    keyword: str = Form(...),
    limit: int = Form(10),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        queue_job("like_by_keyword", {"keyword": keyword, "limit": limit}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Skrip Like by Keyword berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}
# 1b. BOT FACEBOOK LIKE
@app.post("/api/jalankan-bot-fb-like")
async def run_bot_facebook_like(
    fb_page_id: str = Form(None),
    fb_target: str = Form(...),
    fb_token: str = Form(...),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        payload = {"fb_page_id": fb_page_id, "fb_target": fb_target, "fb_token": fb_token}
        queue_job("fb_like", payload, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Facebook Like job queued by {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to queue Facebook Like: {str(e)}"}

# 1c. BOT FACEBOOK COMMENT
@app.post("/api/jalankan-bot-fb-comment")
async def run_bot_fb_comment(
    fb_target: str = Form(...),
    fb_comment_text: str = Form(...),
    fb_token: str = Form(...),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        payload = {"fb_target": fb_target, "fb_comment_text": fb_comment_text, "fb_token": fb_token}
        queue_job("fb_comment", payload, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Facebook Comment job queued by {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to queue Facebook Comment: {str(e)}"}

# 1d. BOT FACEBOOK POST
@app.post("/api/jalankan-bot-fb-post")
async def run_bot_fb_post(
    fb_page_id: str = Form("me"),
    fb_post_type: str = Form("status"),
    fb_message: str = Form(...),
    fb_link_url: str = Form(None),
    fb_token: str = Form(...),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        payload = {
            "fb_page_id": fb_page_id,
            "fb_post_type": fb_post_type,
            "fb_message": fb_message,
            "fb_link_url": fb_link_url or "",
            "fb_token": fb_token
        }
        queue_job("fb_post", payload, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Facebook Post job queued by {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to queue Facebook Post: {str(e)}"}

# 2. BOT COMMENT
@app.post("/api/jalankan-bot-comment")
async def run_bot_comment(
    target: str = Form(...),
    komentar: str = Form(None),
    file_komentar: UploadFile = File(None),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        komentar_final = komentar or ""
        if file_komentar and file_komentar.filename:
            original_filename = file_komentar.filename
            ext = os.path.splitext(original_filename)[1]
            base = os.path.splitext(original_filename)[0]
            safe_base = "".join(c for c in base if c.isalnum() or c in "-_")
            if not safe_base:
                safe_base = "comment"
            safe_filename = f"comment_{safe_base}_{int(datetime.now().timestamp())}{ext}"
            file_path = os.path.join(UPLOAD_DIR, safe_filename)
            
            with open(file_path, "wb") as buffer:
                buffer.write(await file_komentar.read())
            komentar_final = file_path
            
        queue_job("comment", {"target": target, "komentar": komentar_final}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Skrip Komen berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 3. BOT POST
@app.post("/api/jalankan-bot-post")
async def run_bot_post(caption: str = Form(...), file_media: UploadFile = File(...), operator: str = Form("Admin Utama"), waktu_eksekusi: str = Form(None), device_id: str = Form("all")):
    try:
        # Bersihkan nama file agar aman dari spasi/karakter aneh dan beri timestamp unik agar tidak bentrok di Galeri HP
        original_filename = file_media.filename
        ext = os.path.splitext(original_filename)[1]
        base = os.path.splitext(original_filename)[0]
        safe_base = "".join(c for c in base if c.isalnum() or c in "-_")
        if not safe_base:
            safe_base = "upload"
        safe_filename = f"{safe_base}_{int(datetime.now().timestamp())}{ext}"
        
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file_media.read())
            
        queue_job("post", {"caption": caption, "file_path": file_path}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Upload postingan berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 3.5 BOT POST STORY
@app.post("/api/jalankan-bot-post-story")
async def run_bot_post_story(file_media: UploadFile = File(...), operator: str = Form("Admin Utama"), waktu_eksekusi: str = Form(None), device_id: str = Form("all")):
    try:
        original_filename = file_media.filename
        ext = os.path.splitext(original_filename)[1]
        base = os.path.splitext(original_filename)[0]
        safe_base = "".join(c for c in base if c.isalnum() or c in "-_")
        if not safe_base:
            safe_base = "upload_story"
        safe_filename = f"{safe_base}_{int(datetime.now().timestamp())}{ext}"
        
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file_media.read())
            
        queue_job("post_story", {"file_path": file_path}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Upload postingan story berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 3.6 BOT POST REELS
@app.post("/api/jalankan-bot-post-reels")
async def run_bot_post_reels(caption: str = Form(...), file_media: UploadFile = File(...), operator: str = Form("Admin Utama"), waktu_eksekusi: str = Form(None), device_id: str = Form("all")):
    try:
        original_filename = file_media.filename
        ext = os.path.splitext(original_filename)[1]
        base = os.path.splitext(original_filename)[0]
        safe_base = "".join(c for c in base if c.isalnum() or c in "-_")
        if not safe_base:
            safe_base = "upload_reels"
        safe_filename = f"{safe_base}_{int(datetime.now().timestamp())}{ext}"
        
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file_media.read())
            
        queue_job("post_reels", {"caption": caption, "file_path": file_path}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Upload Reels berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 4. BOT REPORT
@app.post("/api/jalankan-bot-report")
async def run_bot_report(
    target: str = Form(...),
    alasan: str = Form("Sesuatu tentang akun ini"),
    my_account: str = Form(""),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        queue_job("report", {"target": target, "alasan": alasan, "my_account": my_account}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Skrip Report berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 5. BOT SHARE
@app.post("/api/jalankan-bot-share")
async def run_bot_share(target: str = Form(...), tujuan_share: str = Form(...), operator: str = Form("Admin Utama"), waktu_eksekusi: str = Form(None), device_id: str = Form("all")):
    try:
        queue_job("share", {"target": target, "tujuan_share": tujuan_share}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Skrip Share berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 6. BOT CHAT / DM
@app.post("/api/jalankan-bot-chat")
async def run_bot_chat(target: str = Form(...), pesan: str = Form(...), operator: str = Form("Admin Utama"), waktu_eksekusi: str = Form(None), device_id: str = Form("all")):
    try:
        queue_job("chat", {"target": target, "pesan": pesan}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Skrip Chat/DM berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 7. BOT MANAGE
@app.post("/api/jalankan-bot-manage")
async def run_bot_manage(target: str = Form(...), aksi: str = Form("follow"), operator: str = Form("Admin Utama"), waktu_eksekusi: str = Form(None), device_id: str = Form("all")):
    try:
        queue_job("manage", {"target": target, "aksi": aksi}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Skrip Manage berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 8. BOT PROFILE
@app.post("/api/jalankan-bot-profile")
async def run_bot_profile(
    nama: str = Form(None),
    username: str = Form(None),
    bio: str = Form(None),
    file_avatar: UploadFile = File(None),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        avatar_path = ""
        if file_avatar and file_avatar.filename:
            original_filename = file_avatar.filename
            ext = os.path.splitext(original_filename)[1]
            base = os.path.splitext(original_filename)[0]
            safe_base = "".join(c for c in base if c.isalnum() or c in "-_")
            if not safe_base:
                safe_base = "avatar"
            safe_filename = f"avatar_{safe_base}_{int(datetime.now().timestamp())}{ext}"
            file_path = os.path.join(UPLOAD_DIR, safe_filename)
            
            with open(file_path, "wb") as buffer:
                buffer.write(await file_avatar.read())
            avatar_path = file_path
            
        queue_job("profile", {"nama": nama or "", "username": username or "", "bio": bio or "", "avatar_path": avatar_path}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Skrip Edit Profil berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 9. BOT REPOST
@app.post("/api/jalankan-bot-repost")
async def run_bot_repost(
    target: str = Form(...),
    caption_type: str = Form("credit"),
    custom_caption: str = Form(None),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        queue_job("repost", {"target": target, "caption_type": caption_type, "custom_caption": custom_caption or ""}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Repost postingan berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 10. BOT LOGIN INSTAGRAM
@app.post("/api/jalankan-bot-login")
async def run_bot_login(
    username: str = Form(...),
    password: str = Form(...),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        queue_job("login", {"username": username, "password": password}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Login akun {username} berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 10b. BOT LOGIN FACEBOOK
@app.post("/api/jalankan-bot-fb-login")
async def run_bot_fb_login(
    username: str = Form("uyug"),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        queue_job("fb_login", {"username": username}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Login Facebook akun {username} berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 11. BOT FARMING INSTAGRAM
@app.post("/api/jalankan-bot-farming")
async def run_bot_farming(
    jumlah_post: int = Form(10),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        queue_job("farming", {"jumlah_post": jumlah_post}, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Farming bot ({jumlah_post} post) berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 12. BOT SCRAPER INSTAGRAM
@app.post("/api/jalankan-bot-scraper")
async def run_bot_scraper(
    target_competitor: str = Form(...),
    scrape_type: str = Form("followers"),
    limit: int = Form(50),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        queue_job("scraper", {
            "target_competitor": target_competitor,
            "scrape_type": scrape_type,
            "limit": limit
        }, operator, waktu_eksekusi, device_id)
        return {"status": "success", "message": f"Scraper bot ({scrape_type} dari @{target_competitor}, limit {limit}) berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 12b. BOT FOLLOW ORANG INSTAGRAM
@app.post("/api/jalankan-bot-follow-orang")
async def run_bot_follow_orang(
    target_url: str = Form(""),
    my_account: str = Form(""),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    try:
        queue_job("follow_orang", {
            "target_url": target_url,
            "my_account": my_account
        }, operator, waktu_eksekusi, device_id)
        
        target_desc = f"@{target_url}" if target_url else "Notifikasi"
        return {"status": "success", "message": f"Follow Orang bot ({target_desc}) berhasil dimasukkan ke antrean oleh {operator}!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memasukkan perintah ke antrean: {str(e)}"}

# 13. API AMBIL DATA SCRAPED TARGETS
@app.get("/api/get-scraped-targets")
async def get_scraped_targets():
    file_path = "scraped_targets.txt"
    if not os.path.exists(file_path):
        return {"status": "success", "count": 0, "targets": []}
    try:
        with open(file_path, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        unique_targets = list(sorted(set(lines)))
        return {"status": "success", "count": len(unique_targets), "targets": unique_targets}
    except Exception as e:
        return {"status": "error", "message": f"Gagal membaca data targets: {str(e)}"}

# 14. BOT BULK CHAT KE TARGET SCRAPING
@app.post("/api/jalankan-bot-bulk-chat")
async def run_bot_bulk_chat(
    pesan: str = Form(...),
    operator: str = Form("Admin Utama"),
    waktu_eksekusi: str = Form(None),
    device_id: str = Form("all")
):
    file_path = "scraped_targets.txt"
    if not os.path.exists(file_path):
        return {"status": "error", "message": "Belum ada data target di scraped_targets.txt. Silakan jalankan Scraper Bot terlebih dahulu!"}
        
    try:
        with open(file_path, "r") as f:
            targets = [line.strip() for line in f if line.strip()]
        unique_targets = list(sorted(set(targets)))
        
        if not unique_targets:
            return {"status": "error", "message": "File scraped_targets.txt kosong!"}
            
        # Masukkan masing-masing target ke antrean
        for target in unique_targets:
            actual_username = target.split('|')[0].strip() if '|' in target else target.strip()
            queue_job("chat", {"target": actual_username, "pesan": pesan}, operator, waktu_eksekusi, device_id)
            
        return {"status": "success", "message": f"Berhasil memasukkan {len(unique_targets)} tugas Chat/DM massal ke antrean!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memproses bulk chat: {str(e)}"}

# ========================================================
# RUTE API BARU: LOGIN DAN PENGATURAN KREDENSIAL
# ========================================================

# 1. API LOGIN
@app.post("/api/login")
async def login_api(username: str = Form(...), password: str = Form(...)):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Hash input password
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        # Cari user berdasarkan username/email dan password_hash
        cursor.execute("""
            SELECT username, email, role, name, avatar FROM users
            WHERE (username = ? OR email = ?) AND password_hash = ?
        """, (username, username, password_hash))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # Generate random session token
            session_token = secrets.token_hex(24)
            return {
                "status": "success",
                "message": "Login berhasil!",
                "token": session_token,
                "user": {
                    "username": user[0],
                    "email": user[1],
                    "role": user[2],
                    "name": user[3],
                    "avatar": user[4]
                }
            }
        else:
            return {
                "status": "error",
                "message": "Username atau kata sandi salah!"
            }
    except Exception as e:
        return {"status": "error", "message": f"Terjadi kesalahan sistem: {str(e)}"}

# 2. API UBAH KATA SANDI
@app.post("/api/change-password")
async def change_password(
    username: str = Form(...),
    old_password: str = Form(...),
    new_password: str = Form(...)
):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Hash sandi lama & baru
        old_hash = hashlib.sha256(old_password.encode('utf-8')).hexdigest()
        new_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
        
        # Validasi sandi lama
        cursor.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", (username, old_hash))
        user_row = cursor.fetchone()
        
        if not user_row:
            conn.close()
            return {"status": "error", "message": "Kata sandi lama tidak cocok!"}
        
        # Update sandi baru
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, username))
        conn.commit()
        conn.close()
        
        return {"status": "success", "message": "Kata sandi berhasil diperbarui!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal memperbarui kata sandi: {str(e)}"}


# 3. API SCAN INSTAGRAM ACCOUNTS DARI PERANGKAT VIA ADB
@app.post("/api/scan-device-accounts")
async def scan_device_accounts(device_id: str = Form(...)):
    try:
        # Jalankan bot_ig_scan_accounts.py secara real-time
        try:
            adb_bin, _ = execute_adb_command()
        except:
            adb_bin = "adb"
            
        python_bin = sys.executable
        cmd = [python_bin, "bot_ig_scan_accounts.py", device_id]
        
        # Jalankan secara sinkronus dengan timeout 90 detik
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90, cwd=os.getcwd())
        stdout = proc.stdout
        
        # Cari baris "__SCAN_RESULT__:" di stdout
        accounts = []
        for line in stdout.split("\n"):
            if line.startswith("__SCAN_RESULT__:"):
                accounts = json.loads(line.replace("__SCAN_RESULT__:", "").strip())
                break
                
        return {
            "status": "success",
            "device_id": device_id,
            "accounts": accounts,
            "output": stdout
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Scan timeout. Pastikan device terhubung, kunci layar dibuka, dan USB Debugging aktif!"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Gagal memindai akun: {str(e)}"
        }


# Melayani file statis (HTML, CSS, JS) langsung dari folder root via FastAPI (Anti-Live Server)
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
