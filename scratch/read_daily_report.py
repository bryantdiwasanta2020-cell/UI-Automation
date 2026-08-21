import json
import os
from datetime import datetime

# Path to the centralized activity log file
log_file_path = "/home/me/TEAM/automation_2026/instagram/activity.logs.json"

def compile_daily_report(date_str="2026-08-20"):
    if not os.path.exists(log_file_path):
        print(f"Log file not found at: {log_file_path}")
        return

    logs = []
    with open(log_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                try:
                    logs.append(json.loads(line_str))
                except Exception as e:
                    pass

    # Filter logs by today's date
    today_logs = [log for log in logs if log.get("timestamp", "").startswith(date_str)]

    print(f"\n=============================================")
    print(f"   LAPORAN AKTIVITAS BOT INSTAGRAM ({date_str})")
    print(f"=============================================")
    print(f"Total Aktivitas Hari Ini: {len(today_logs)}")
    
    if not today_logs:
        print("Belum ada aktivitas tercatat untuk hari ini.")
        print("=============================================\n")
        return

    # Group by action status
    status_summary = {"complete": 0, "failed": 0, "on_progress": 0}
    action_counts = {}
    device_counts = {}
    account_summary = {}

    for entry in today_logs:
        status = entry.get("status", "unknown")
        action = entry.get("action", "unknown")
        device = entry.get("device_id", "unknown")
        user = entry.get("username", "unknown")
        
        status_summary[status] = status_summary.get(status, 0) + 1
        
        action_counts[action] = action_counts.get(action, 0) + 1
        device_counts[device] = device_counts.get(device, 0) + 1
        
        # Track details per device/account
        key = (device, user)
        if key not in account_summary:
            account_summary[key] = []
        account_summary[key].append(entry)

    print(f"\n[1] RINGKASAN STATUS:")
    print(f"  - Sukses (Complete) : {status_summary.get('complete', 0)}")
    print(f"  - Gagal (Failed)    : {status_summary.get('failed', 0)}")
    print(f"  - Berjalan (Running): {status_summary.get('on_progress', 0)}")

    print(f"\n[2] RINGKASAN AKSI:")
    for act, count in action_counts.items():
        print(f"  - {act.upper():<20} : {count} kali")

    print(f"\n[3] RINCIAN AKTIVITAS PER AKUN & DEVICE:")
    for (dev, usr), entries in account_summary.items():
        print(f"\n  • Device: {dev} | Akun: @{usr}")
        for entry in entries:
            time_part = entry.get("timestamp", "").split("T")[1][:5]
            action = entry.get("action", "unknown")
            status = entry.get("status", "unknown")
            err_msg = f" -> ERROR: {entry.get('error')}" if entry.get("error") else ""
            status_symbol = "✅" if status == "complete" else ("❌" if status == "failed" else "⏳")
            print(f"    [{time_part}] {action.upper():<18} {status_symbol} {status}{err_msg}")

    print(f"=============================================\n")

if __name__ == "__main__":
    compile_daily_report()
