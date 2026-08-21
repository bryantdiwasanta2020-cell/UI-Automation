import sqlite3
import json
import time
import subprocess
import os
import sys
from datetime import datetime

DATABASE_FILE = "bot_queue.db"

# Import activity logger (modul terpusat)
try:
    from activity_logger import log_activity, log_complete, log_error, append_to_activity_logs
except Exception as e:
    print(f"[WARNING] Gagal import activity_logger: {e}")
    # Fallback sederhana jika modul tidak tersedia
    def append_to_activity_logs(device_id, command_type, target, status):
        pass
    def log_activity(*a, **kw): return ""
    def log_complete(*a, **kw): return False
    def log_error(*a, **kw): return False

def get_log_file():
    if os.path.exists("activity.logs.json"):
        return "activity.logs.json"
    elif os.path.exists("activity_logs.json"):
        return "activity_logs.json"
    return "activity.logs.json"  # Default fallback

def get_next_job():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Cari ID job PENDING yang paling lama (terjadwal atau dibuat paling awal)
    cursor.execute("""
        SELECT id FROM jobs 
        WHERE status = 'PENDING' 
          AND (waktu_eksekusi IS NULL OR waktu_eksekusi = '' OR waktu_eksekusi <= ?)
        ORDER BY COALESCE(waktu_eksekusi, created_at) ASC, id ASC
        LIMIT 1
    """, (current_time,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
        
    job_id = row[0]
    
    # 2. Klaim job secara atomik dengan mengupdate statusnya menjadi RUNNING
    cursor.execute("""
        UPDATE jobs 
        SET status = 'RUNNING', started_at = ? 
        WHERE id = ? AND status = 'PENDING'
    """, (now_str, job_id))
    
    conn.commit()
    
    # Periksa apakah klaim berhasil (mencegah kondisi balapan/race condition)
    if cursor.rowcount > 0:
        cursor.execute("SELECT id, command_type, payload, operator, waktu_eksekusi, device_id FROM jobs WHERE id = ?", (job_id,))
        job_data = cursor.fetchone()
        conn.close()
        return job_data
        
    conn.close()
    return None

# append_to_activity_logs sudah dipindah ke activity_logger.py
# Fungsi ini dipertahankan sebagai proxy untuk kompatibilitas mundur
# (Sudah di-import dari activity_logger di atas)

def update_job_status(job_id, status, error_message=None):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE jobs 
        SET status = ?, completed_at = ?, error_message = ? 
        WHERE id = ?
    """, (status, now_str, error_message, job_id))
    conn.commit()
    conn.close()

def run_worker():
    print("==================================================")
    print("  INSTADB QUEUE WORKER AGENT RUNNING...")
    print(" Memantau antrean tabel 'jobs' secara real-time...")
    print("==================================================")
    
    while True:
        try:
            job = get_next_job()
            if job:
                job_id, cmd_type, payload_str, operator, waktu_eksekusi, device_id = job
                
                print(f"\n [CLAIMED] Job ID: {job_id} | Type: {cmd_type} | Target Device: {device_id}")
                try:
                    payload = json.loads(payload_str)
                except Exception as ex:
                    payload = {}
                    print(f" Gagal memproses payload JSON: {ex}")
                
                # Petakan command bot sesuai dengan tipe input
                cmd = []
                target_value = ""
                
                # Kita gunakan sys.executable agar python interpreter yang dipanggil sama persis
                python_bin = sys.executable
                
                if cmd_type == "like":
                    target_value = payload.get("target", "")
                    cmd = [python_bin, "bot_ig_like.py", "like_target", target_value, device_id, payload.get("my_account", "")]
                elif cmd_type == "like_by_keyword":
                    target_value = payload.get("keyword", "")
                    limit_val = payload.get("limit", 10)
                    cmd = [python_bin, "bot_ig_like.py", "like_keyword", target_value, str(limit_val), device_id]
                elif cmd_type == "comment":
                    target_value = payload.get("target", "")
                    cmd = [python_bin, "bot_ig_comment.py", "comment_target", target_value, payload.get("komentar", ""), device_id, payload.get("my_account", "")]
                elif cmd_type == "comment_by_keyword":
                    target_value = payload.get("keyword", "")
                    limit_val = payload.get("limit", 5)
                    cmd = [python_bin, "bot_ig_comment.py", "comment_keyword", target_value, str(limit_val), payload.get("komentar", ""), device_id]
                elif cmd_type == "post":
                    target_value = payload.get("file_path", "")
                    cmd = [python_bin, "bot_ig_post.py", target_value, payload.get("caption", ""), device_id]
                elif cmd_type == "post_story":
                    target_value = payload.get("file_path", "")
                    cmd = [python_bin, "bot_ig_post_story.py", target_value, device_id]
                elif cmd_type == "post_reels":
                    target_value = payload.get("file_path", "")
                    cmd = [python_bin, "bot_ig_post_reels.py", target_value, payload.get("caption", ""), device_id]
                elif cmd_type == "report":
                    target_value = payload.get("target", "")
                    alasan = payload.get("alasan", "Sesuatu tentang akun ini")
                    cmd = [python_bin, "bot_ig_report.py", target_value, device_id, alasan, payload.get("my_account", "")]
                elif cmd_type == "share":
                    target_value = payload.get("target", "")
                    cmd = [python_bin, "bot_ig_share.py", target_value, payload.get("tujuan_share", ""), device_id]
                elif cmd_type == "fb_like":
                    target_value = payload.get("fb_target", "")
                    fb_page_id = payload.get("fb_page_id", "")
                    fb_token = payload.get("fb_token", "")
                    cmd = [python_bin, "bot_facebook_like.py", fb_page_id, target_value, fb_token, device_id]
                elif cmd_type == "fb_comment":
                    target_value = payload.get("fb_target", "")
                    fb_comment_text = payload.get("fb_comment_text", "")
                    fb_token = payload.get("fb_token", "")
                    cmd = [python_bin, "bot_facebook_comment.py", target_value, fb_comment_text, fb_token, device_id]
                elif cmd_type == "fb_post":
                    target_value = payload.get("fb_page_id", "me")
                    fb_post_type = payload.get("fb_post_type", "status")
                    fb_message = payload.get("fb_message", "")
                    fb_link_url = payload.get("fb_link_url", "")
                    fb_token = payload.get("fb_token", "")
                    cmd = [python_bin, "bot_facebook_post.py", target_value, fb_post_type, fb_message, fb_link_url, fb_token, device_id]
                elif cmd_type == "chat":
                    target_value = payload.get("target", "")
                    cmd = [python_bin, "bot_ig_chat.py", target_value, payload.get("pesan", ""), device_id]
                elif cmd_type == "manage":
                    target_value = payload.get("target", "")
                    cmd = [python_bin, "bot_ig_manage.py", target_value, payload.get("aksi", ""), device_id]
                elif cmd_type == "profile":
                    target_value = payload.get("nama", "") or payload.get("username", "") or payload.get("bio", "") or payload.get("avatar_path", "")
                    cmd = [
                        python_bin,
                        "bot_ig_profile.py",
                        payload.get("nama", "") or "-",
                        payload.get("username", "") or "-",
                        payload.get("bio", "") or "-",
                        payload.get("avatar_path", "") or "-",
                        device_id
                    ]
                elif cmd_type == "repost":
                    target_value = payload.get("target", "")
                    cmd = [
                        python_bin,
                        "bot_ig_repost.py",
                        target_value,
                        payload.get("caption_type", "credit"),
                        payload.get("custom_caption", "") or "-",
                        device_id
                    ]
                elif cmd_type == "follow_orang":
                    target_value = payload.get("target_url", "")
                    cmd = [
                        python_bin,
                        "bot_ig_follow_orang.py",
                        target_value,
                        device_id,
                        payload.get("my_account", "")
                    ]
                elif cmd_type == "login":
                    target_value = payload.get("username", "")
                    cmd = [
                        python_bin,
                        "bot_instagram_login_master.py",
                        target_value,
                        payload.get("password", ""),
                        device_id
                    ]
                elif cmd_type == "fb_login":
                    target_value = payload.get("username", "")
                    cmd = [
                        python_bin,
                        "bot_facebook_login.py",
                        target_value,
                        device_id
                    ]
                elif cmd_type == "farming":
                    target_value = str(payload.get("jumlah_post", 10))
                    cmd = [
                        python_bin,
                        "bot_ig_farming.py",
                        device_id,
                        target_value
                    ]
                elif cmd_type == "scraper":
                    target_value = payload.get("target_competitor", "")
                    cmd = [
                        python_bin,
                        "bot_ig_scraper.py",
                        target_value,
                        payload.get("scrape_type", "followers"),
                        str(payload.get("limit", 50)),
                        device_id
                    ]
                
                if not cmd:
                    print(f" Tipe perintah '{cmd_type}' tidak dikenal. Mengabaikan.")
                    update_job_status(job_id, "GAGAL", f"Tipe perintah '{cmd_type}' tidak dikenal.")
                    append_to_activity_logs(device_id, cmd_type, target_value, "GAGAL")
                    continue
                
                print(f" Menjalankan skrip: {' '.join(cmd)}")
                
                # Eksekusi secara sinkronus agar berjalan berurutan satu per satu
                # Gunakan cwd=os.getcwd() untuk memastikan folder berjalan di root workspace
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
                
                if result.returncode == 0:
                    print(f" [SUCCESS] Job ID: {job_id} berhasil diselesaikan.")
                    update_job_status(job_id, "SUKSES")
                    append_to_activity_logs(device_id, cmd_type, target_value, "SUKSES")
                else:
                    error_msg = result.stderr or result.stdout or "Error tidak diketahui"
                    print(f" [FAILED] Job ID: {job_id} gagal. Detail: {error_msg}")
                    update_job_status(job_id, "GAGAL", error_msg)
                    append_to_activity_logs(device_id, cmd_type, target_value, "GAGAL")
            else:
                # Tidur sebentar jika tidak ada antrean pending
                time.sleep(2)
        except KeyboardInterrupt:
            print("\n Worker dihentikan oleh pengguna.")
            break
        except Exception as e:
            print(f" Terjadi kesalahan pada main loop worker: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_worker()
