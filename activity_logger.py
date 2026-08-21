"""
activity_logger.py
==================
Modul logging terpusat untuk semua aktivitas bot.
Mencatat setiap aksi bot ke dalam file JSON dengan struktur lengkap.

Struktur log entry:
{
    "id"        : "uuid unik per entri",
    "timestamp" : "2026-07-28T10:00:00+07:00",
    "sosmed"    : "instagram" | "facebook" | "tiktok" | ...,
    "action"    : "like" | "comment" | "report" | "follow" | ...,
    "username"  : "target_user" atau akun yang dipakai,
    "message"   : "teks komentar / caption / alasan lapor / pesan DM",
    "status"    : "on_progress" | "complete" | "failed",
    "error"     : null | "deskripsi error detail",
    "mode"      : "farming" | "manual",
    "device_id" : "id perangkat yang dipakai",
    "extra"     : { ... data tambahan opsional ... }
}
"""

import json
import os
import uuid
from datetime import datetime, timezone, timedelta

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(_BASE_DIR, "activity.logs.json")
WIB = timezone(timedelta(hours=7))

ACTION_LABELS = {
    "like"              : "Like Post",
    "like_target"       : "Like Post (Target)",
    "like_keyword"      : "Like Post (Keyword)",
    "like_by_keyword"   : "Like Post (Keyword)",
    "comment"           : "Komentar",
    "comment_target"    : "Komentar (Target)",
    "comment_keyword"   : "Komentar (Keyword)",
    "comment_by_keyword": "Komentar (Keyword)",
    "report"            : "Lapor Akun",
    "search_report"     : "Cari & Lapor",
    "follow"            : "Follow Akun",
    "follow_orang"      : "Follow Orang",
    "unfollow"          : "Unfollow Akun",
    "repost"            : "Repost",
    "repost_keyword"    : "Repost (Keyword)",
    "share"             : "Share Postingan",
    "chat"              : "Kirim DM",
    "post"              : "Upload Post",
    "post_story"        : "Upload Story",
    "post_reels"        : "Upload Reels",
    "farming"           : "Farming",
    "scraper"           : "Scraping Data",
    "manage"            : "Kelola Akun",
    "profile"           : "Edit Profil",
    "login"             : "Login Akun",
    "logout"            : "Logout Akun",
    "register"          : "Daftar Akun",
    "switch_account"    : "Ganti Akun",
    "fb_like"           : "Facebook Like",
    "fb_comment"        : "Facebook Komentar",
    "fb_post"           : "Facebook Post",
    "fb_login"          : "Facebook Login",
    "tt_like"           : "TikTok Like",
    "tt_comment"        : "TikTok Komentar",
}

SOSMED_MAP = {
    "fb_": "facebook",
    "tt_": "tiktok",
    "tw_": "twitter",
    "yt_": "youtube",
}


def _detect_sosmed(action):
    for prefix, platform in SOSMED_MAP.items():
        if action.lower().startswith(prefix):
            return platform
    return "instagram"


def _load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return []
        
        # Coba load sebagai JSON array
        if content.startswith("[") and content.endswith("]"):
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    return data
            except Exception:
                pass
                
        # Jika bukan array, parse sebagai JSON Lines (sebaris-sebaris)
        logs = []
        for line in content.splitlines():
            line = line.strip()
            if line:
                try:
                    logs.append(json.loads(line))
                except Exception:
                    pass
        return logs
    except Exception as e:
        print(f"[ActivityLogger] Gagal membaca log file: {e}")
        return []


def _save_logs(logs):
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            for entry in logs:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        print(f"[ActivityLogger] Gagal menyimpan log file: {e}")
        return False


def _write_jsonl_capped(file_path, new_entry, max_entries=50):
    entries = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        except Exception as e:
            print(f"[ActivityLogger] Gagal membaca {file_path} untuk capping: {e}")
            
    # Masukkan entri baru di posisi paling atas (indeks 0)
    entries.insert(0, new_entry)
    
    # Batasi maksimal 50
    entries = entries[:max_entries]
    
    # Simpan kembali ke file (overwrite)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[ActivityLogger] Gagal menulis ke {file_path}: {e}")


def _write_spec_logs(sosmed, action_key, username, message, status, error, mode, device_id):
    if not device_id or device_id == "all":
        return

    safe_dev = "".join(c for c in device_id if c.isalnum() or c in "-_")
    if not safe_dev:
        return

    # Map values to match log.md spec
    mapped_mode = "farming" if mode == "farming" else "campaign"
    
    # Map action name
    mapped_action = action_key
    if "like" in action_key:
        mapped_action = "like"
    elif "comment" in action_key:
        mapped_action = "comment"
    elif "repost" in action_key:
        mapped_action = "repost"
    elif "report" in action_key:
        mapped_action = "report"
    elif "login" in action_key:
        mapped_action = "login"
    elif "switch_account" in action_key:
        mapped_action = "switch_account"
    elif "post_story" in action_key:
        mapped_action = "post_story"
    elif "post_reels" in action_key:
        mapped_action = "post_reels"
    elif "post" in action_key:
        mapped_action = "post"

    # Map message type: "text" | "media"
    mapped_msg = message
    if mapped_msg not in ("text", "media"):
        mapped_msg = "text" if "comment" in action_key or "chat" in action_key else "media"

    now_wib = datetime.now(WIB)
    now_wib_str = now_wib.strftime("%Y-%m-%d %H:%M:%S")
    date_str = now_wib.strftime("%Y-%m-%d")

    # 1. Write to log_device/
    dev_dir = os.path.join(_BASE_DIR, "Document", "log_device")
    os.makedirs(dev_dir, exist_ok=True)
    dev_file = os.path.join(dev_dir, f"{safe_dev}.jsonl")
    dev_entry = {
        "sosmed": sosmed or "instagram",
        "action": mapped_action,
        "username": username or "",
        "message": mapped_msg,
        "status": status,
        "error": error,
        "mode": mapped_mode,
        "timestamp": now_wib_str
    }
    _write_jsonl_capped(dev_file, dev_entry, 50)

    # 2. Write to log_action/
    action_dir = os.path.join(_BASE_DIR, "Document", "log_action")
    os.makedirs(action_dir, exist_ok=True)
    action_file = os.path.join(action_dir, f"{date_str}_{sosmed or 'instagram'}_{mapped_action}_{safe_dev}.jsonl")
    action_entry = {
        "step": mapped_action,
        "status": status,
        "error": error,
        "timestamp": now_wib_str
    }
    _write_jsonl_capped(action_file, action_entry, 50)


def log_step(step, status="complete", error=None, device_id="", action="like", sosmed="instagram"):
    """
    Mencatat step detail ke dalam log_action/
    """
    if not device_id or device_id == "all":
        return
        
    safe_dev = "".join(c for c in device_id if c.isalnum() or c in "-_")
    if not safe_dev:
        return
        
    # Map action name
    mapped_action = action
    if "like" in action:
        mapped_action = "like"
    elif "comment" in action:
        mapped_action = "comment"
    elif "repost" in action:
        mapped_action = "repost"
    elif "report" in action:
        mapped_action = "report"
    elif "login" in action:
        mapped_action = "login"
    elif "switch_account" in action:
        mapped_action = "switch_account"
    elif "post_story" in action:
        mapped_action = "post_story"
    elif "post_reels" in action:
        mapped_action = "post_reels"
    elif "post" in action:
        mapped_action = "post"

    action_dir = os.path.join(_BASE_DIR, "Document", "log_action")
    os.makedirs(action_dir, exist_ok=True)
    now_wib = datetime.now(WIB)
    date_str = now_wib.strftime("%Y-%m-%d")
    action_file = os.path.join(action_dir, f"{date_str}_{sosmed or 'instagram'}_{mapped_action}_{safe_dev}.jsonl")
    
    action_entry = {
        "step": step,
        "status": status,
        "error": error,
        "timestamp": now_wib.strftime("%Y-%m-%d %H:%M:%S")
    }
    _write_jsonl_capped(action_file, action_entry, 50)


def log_activity(action, username="", message="", status="on_progress",
                 error=None, mode="manual", device_id="", sosmed=None,
                 extra=None, log_id=None):
    """
    Mencatat satu entri aktivitas bot ke dalam file log JSON.
    Mengembalikan log_id (UUID) yang bisa dipakai untuk update status nanti.
    """
    if log_id is None:
        log_id = str(uuid.uuid4())
    if sosmed is None:
        sosmed = _detect_sosmed(action)

    action_label = ACTION_LABELS.get(action, action.replace("_", " ").title())
    now_wib = datetime.now(WIB)

    entry = {
        "id"        : log_id,
        "timestamp" : now_wib.strftime("%Y-%m-%dT%H:%M:%S+07:00"),
        "sosmed"    : sosmed,
        "action"    : action_label,
        "action_key": action,
        "username"  : username,
        "message"   : message,
        "status"    : status,
        "error"     : error,
        "mode"      : mode,
        "device_id" : device_id,
        "extra"     : extra or {}
    }

    logs = _load_logs()
    logs.insert(0, entry)
    logs = logs[:50]
    _save_logs(logs)

    # Tulis juga ke format spesifikasi baru log_device/ dan log_action/
    _write_spec_logs(sosmed, action, username, message, status, error, mode, device_id)

    icons = {"on_progress": "⏳", "complete": "✅", "failed": "❌"}
    icon = icons.get(status, "📋")
    print(f"[ActivityLogger] {icon} [{now_wib.strftime('%H:%M:%S')}] {sosmed.upper()} | {action_label} | @{username} | {status}")
    if error:
        print(f"[ActivityLogger]    ⚠️  Error: {error}")

    return log_id


def update_log_status(log_id, status, error=None, message=None, extra_update=None):
    """
    Update status log yang sudah ada (on_progress -> complete/error).
    """
    logs = _load_logs()
    found = False
    for entry in logs:
        if entry.get("id") == log_id:
            entry["status"] = status
            entry["updated_at"] = datetime.now(WIB).strftime("%Y-%m-%dT%H:%M:%S+07:00")
            if error is not None:
                entry["error"] = error
            if message is not None:
                entry["message"] = message
            if extra_update:
                if not isinstance(entry.get("extra"), dict):
                    entry["extra"] = {}
                entry["extra"].update(extra_update)
            found = True
            
            # Tulis update status ke format spesifikasi baru log_device/ dan log_action/
            _write_spec_logs(
                entry.get("sosmed"),
                entry.get("action_key"),
                entry.get("username"),
                message or entry.get("message"),
                status,
                error or entry.get("error"),
                entry.get("mode"),
                entry.get("device_id")
            )
            break

    if found:
        _save_logs(logs)
        icons = {"on_progress": "⏳", "complete": "✅", "failed": "❌"}
        icon = icons.get(status, "📋")
        print(f"[ActivityLogger] {icon} Update log [{log_id[:8]}...] -> {status}")
    else:
        print(f"[ActivityLogger] ⚠️  Log ID tidak ditemukan: {log_id}")
    return found


def log_complete(log_id, message=None, extra_update=None):
    """Shortcut: tandai log sebagai complete."""
    return update_log_status(log_id, "complete", message=message, extra_update=extra_update)


def log_error(log_id, error, extra_update=None):
    """Shortcut: tandai log sebagai failed dengan deskripsi."""
    return update_log_status(log_id, "failed", error=error, extra_update=extra_update)


def get_recent_logs(limit=50):
    """Ambil log terbaru (urutan terbaru di atas)."""
    logs = _load_logs()
    return list(reversed(logs[-limit:])) if logs else []


def get_logs_by_status(status):
    """Filter log berdasarkan status."""
    return [e for e in _load_logs() if e.get("status") == status]


def get_logs_by_sosmed(sosmed):
    """Filter log berdasarkan platform sosmed."""
    return [e for e in _load_logs() if e.get("sosmed", "").lower() == sosmed.lower()]


def get_logs_by_action(action_key):
    """Filter log berdasarkan action_key."""
    return [e for e in _load_logs() if e.get("action_key", "") == action_key]


def get_summary():
    """Ringkasan statistik dari semua log."""
    logs = _load_logs()
    if not logs:
        return {"total": 0, "complete": 0, "failed": 0, "on_progress": 0, "by_sosmed": {}, "by_action": {}}
    summary = {
        "total"      : len(logs),
        "complete"   : sum(1 for e in logs if e.get("status") == "complete"),
        "failed"      : sum(1 for e in logs if e.get("status") == "failed"),
        "on_progress": sum(1 for e in logs if e.get("status") == "on_progress"),
        "by_sosmed"  : {},
        "by_action"  : {}
    }
    for entry in logs:
        sm = entry.get("sosmed", "unknown")
        ak = entry.get("action_key", "unknown")
        summary["by_sosmed"][sm] = summary["by_sosmed"].get(sm, 0) + 1
        summary["by_action"][ak] = summary["by_action"].get(ak, 0) + 1
    return summary


# --------------------------------------------------------
# Kompatibilitas mundur dengan queue_worker.py lama
# --------------------------------------------------------
def append_to_activity_logs(device_id, command_type, target, status):
    """Fungsi lama untuk kompatibilitas. Dipetakan ke log_activity()."""
    status_map = {"SUKSES": "complete", "GAGAL": "failed", "RUNNING": "on_progress"}
    log_status = status_map.get(status.upper(), "complete")
    error_msg = None if log_status != "failed" else f"Job gagal: {command_type} pada target {target}"
    log_activity(
        action    = command_type,
        username  = target,
        message   = "",
        status    = log_status,
        error     = error_msg,
        mode      = "farming" if command_type == "farming" else "manual",
        device_id = device_id,
        extra     = {"target": target}
    )


if __name__ == "__main__":
    print("=== Demo Activity Logger ===")
    lid = log_activity("comment", "cristiano", "Keren banget!", "on_progress", device_id="test-device")
    log_complete(lid, extra_update={"post_url": "https://instagram.com/p/abc123"})
    log_activity("farming", "myaccount", status="complete", mode="farming", device_id="192.168.1.1:5555", extra={"posts": 15})
    log_activity("report", "spammer", "Spam account", status="failed", error="Report limit reached", device_id="test-device")
    print("\n=== Summary ===")
    print(json.dumps(get_summary(), indent=2, ensure_ascii=False))
