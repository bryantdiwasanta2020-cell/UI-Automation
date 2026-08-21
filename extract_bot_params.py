#!/usr/bin/env python3
"""
Bot Parameter Extractor (Instagram Only)
----------------------------------------
Skrip bot ini secara otomatis menganalisis seluruh file `bot_ig_*.py` / `bot_instagram_*.py` di direktori workspace,
mengekstrak parameter command line (CLI) & API, lalu mencetak output .txt yang rapi ke folder `txt/r/`.
Seluruh bot non-Instagram (seperti Facebook) dieksklusi / dihapus.
"""

import os
import re
import sys
import glob
import ast

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "txt", "r")

# Manual & enriched metadata map for full accuracy based on PARAMETERS_README & app.py
BOT_KNOWLEDGE = {
    "bot_instagram_login.py": {
        "title": "Bot Login Instagram",
        "description": "Melakukan proses login akun Instagram, membersihkan landing page, membatalkan Google Smart Lock, dan membersihkan pop-up beranda.",
        "params": [
            {"name": "username", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Username Instagram untuk login"},
            {"name": "password", "pos": 2, "req": True, "type": "String", "default": "", "desc": "Password Instagram"},
            {"name": "device_id", "pos": 3, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB (cth: R9RY801LRPW atau 'all')"}
        ],
        "examples": [
            'python3 bot_instagram_login.py "lukyytris13" "Bryant12345678" "R9RY801LRPW"',
            'python3 bot_instagram_login.py "user_saya" "pass123" "all"'
        ],
        "api_endpoint": "/api/jalankan-bot-login"
    },
    "bot_ig_like.py": {
        "title": "Bot Like Postingan & Keyword Instagram",
        "description": "Memberikan Like (Suka) pada postingan target via username/URL, ATAU mencari kata kunci/hashtag di Instagram dan menyukai sejumlah postingan.",
        "params": [
            {"name": "mode_atau_target", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Mode ('like_target' atau 'like_keyword'), atau langsung username/URL/hashtag target"},
            {"name": "target_atau_limit", "pos": 2, "req": False, "type": "String", "default": "", "desc": "Target username/URL (jika menggunakan mode), limit postingan (jika keyword/hashtag), atau ID Perangkat Android ADB"},
            {"name": "device_id_atau_my_account", "pos": 3, "req": False, "type": "String", "default": "", "desc": "ID Perangkat Android ADB, atau nama akun Anda untuk swap di awal"},
            {"name": "my_account", "pos": 4, "req": False, "type": "String", "default": "", "desc": "Nama akun Anda untuk swap di awal (opsional, jika menggunakan mode)"}
        ],
        "examples": [
            'python3 bot_ig_like.py like_target "cristiano" R9RY801LRPW',
            'python3 bot_ig_like.py like_keyword "kucing" 50 R9RY801LRPW',
            'python3 bot_ig_like.py "cristiano" R9RY801LRPW',
            'python3 bot_ig_like.py "#kucing" 10 all'
        ],
        "api_endpoint": "/api/jalankan-bot-like"
    },
    "bot_ig_comment.py": {
        "title": "Bot Komentar & Keyword Instagram",
        "description": "Mengirimkan komentar pada postingan target via username/URL, ATAU mencari kata kunci/hashtag di Instagram dan mengomentari postingan secara masal.",
        "params": [
            {"name": "mode_atau_target", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Mode ('comment_target' atau 'comment_keyword'), atau langsung username/URL/hashtag target"},
            {"name": "target_atau_limit", "pos": 2, "req": False, "type": "String", "default": "", "desc": "Target username/URL (jika menggunakan mode), limit postingan (jika keyword/hashtag), atau komentar kustom"},
            {"name": "komentar_atau_device", "pos": 3, "req": False, "type": "String", "default": "", "desc": "Teks komentar/path file txt, atau ID Perangkat Android ADB"},
            {"name": "device_atau_my_account", "pos": 4, "req": False, "type": "String", "default": "", "desc": "ID Perangkat Android ADB, atau nama akun Anda untuk swap di awal"},
            {"name": "my_account", "pos": 5, "req": False, "type": "String", "default": "", "desc": "Nama akun Anda untuk swap di awal (opsional, jika menggunakan mode)"}
        ],
        "examples": [
            'python3 bot_ig_comment.py comment_target "cristiano" "keren" R9RY801LRPW',
            'python3 bot_ig_comment.py comment_keyword "kucing" 5 "lucu" R9RY801LRPW',
            'python3 bot_ig_comment.py "cristiano" "" R9RY801LRPW',
            'python3 bot_ig_comment.py "#kucing" 5 "" R9RY801LRPW'
        ],
        "api_endpoint": "/api/jalankan-bot-comment"
    },
    "bot_ig_repost.py": {
        "title": "Bot Repost & Keyword Instagram",
        "description": "Mengunduh media postingan target (via username/URL) dan mempostingnya kembali, ATAU mencari keyword/hashtag dan merepost postingan secara beruntun.",
        "params": [
            {"name": "mode_atau_target", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Mode ('username', 'url', 'keyword'), atau langsung username/URL/hashtag target"},
            {"name": "target_atau_limit", "pos": 2, "req": False, "type": "String", "default": "", "desc": "Target/URL (jika menggunakan mode), limit postingan (jika keyword/hashtag), atau tipe caption"},
            {"name": "caption_type_atau_device", "pos": 3, "req": False, "type": "String", "default": "", "desc": "Tipe caption ('credit'/'custom'/'blank'), atau ID Perangkat Android ADB"},
            {"name": "custom_caption_atau_my_account", "pos": 4, "req": False, "type": "String", "default": "", "desc": "Teks custom caption, atau nama akun Anda untuk swap di awal"},
            {"name": "device_id", "pos": 5, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB (jika menggunakan mode)"},
            {"name": "my_account", "pos": 6, "req": False, "type": "String", "default": "", "desc": "Nama akun Anda untuk swap/ganti akun di awal (opsional)"}
        ],
        "examples": [
            'python3 bot_ig_repost.py username "cristiano" credit "" R9RY801LRPW',
            'python3 bot_ig_repost.py keyword "kucing" 5 R9RY801LRPW',
            'python3 bot_ig_repost.py "https://www.instagram.com/p/DbGhqbKE-Bn/" custom "Hasil repost" R9RY801LRPW',
            'python3 bot_ig_repost.py "#kucing" 5 R9RY801LRPW'
        ],
        "api_endpoint": "/api/jalankan-bot-repost"
    },
    "bot_ig_farming.py": {
        "title": "Bot Farming / Warmup Instagram",
        "description": "Melakukan penjelajahan beranda secara otomatis (scrolling, menyukai postingan random, berinteraksi) agar aktivitas terlihat organik.",
        "params": [
            {"name": "device_id", "pos": 1, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"},
            {"name": "jumlah_post_farm", "pos": 2, "req": False, "type": "Integer", "default": "10", "desc": "Jumlah postingan yang akan dijelajahi"}
        ],
        "examples": [
            'python3 bot_ig_farming.py R9RY801LRPW 20',
            'python3 bot_ig_farming.py all 10'
        ],
        "api_endpoint": "/api/jalankan-bot-farming"
    },
    "bot_ig_post.py": {
        "title": "Bot Instagram Post (Unified)",
        "description": "Mengunggah gambar/video ke Feed, Reels, atau Story (otomatis mendeteksi tipe postingan).",
        "params": [
            {"name": "file_path", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Path file gambar/video di server/lokal"},
            {"name": "caption_text_atau_device_id", "pos": 2, "req": False, "type": "String", "default": "", "desc": "Teks caption (untuk Feed/Reels) atau ID Perangkat (untuk Story)"},
            {"name": "device_id_atau_my_account", "pos": 3, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB, atau nama akun Anda untuk swap di awal"},
            {"name": "my_account", "pos": 4, "req": False, "type": "String", "default": "", "desc": "Nama akun Anda untuk swap di awal (opsional)"}
        ],
        "examples": [
            'python3 bot_ig_post.py "/path/to/gambar.png" "Ini caption feed!" R9RY801LRPW',
            'python3 bot_ig_post.py "/path/to/video.mp4" "Ini caption Reels!" R9RY801LRPW',
            'python3 bot_ig_post.py "/path/to/gambar.png" R9RY801LRPW',
            'python3 bot_ig_post.py "/path/to/gambar.png" "Caption" R9RY801LRPW "akun_saya"'
        ],
        "api_endpoint": "/api/jalankan-bot-post"
    },
    "bot_ig_post_reels.py": {
        "title": "Bot Post Reels Instagram",
        "description": "Mengunggah video ke tab Reels Instagram.",
        "params": [
            {"name": "file_path_video", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Path file video .mp4 di server/lokal"},
            {"name": "caption_text", "pos": 2, "req": False, "type": "String", "default": "", "desc": "Teks deskripsi / caption Reels"},
            {"name": "device_id", "pos": 3, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_ig_post_reels.py "/path/to/video.mp4" "Ini Reels seru!" R9RY801LRPW'
        ],
        "api_endpoint": "/api/jalankan-bot-post-reels"
    },
    "bot_ig_post_story.py": {
        "title": "Bot Post Story Instagram",
        "description": "Mengunggah gambar atau video ke Instagram Story.",
        "params": [
            {"name": "file_path", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Path file media gambar/video"},
            {"name": "device_id", "pos": 2, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_ig_post_story.py "/path/to/gambar.png" R9RY801LRPW'
        ],
        "api_endpoint": "/api/jalankan-bot-post-story"
    },

    "bot_ig_report.py": {
        "title": "Bot Report Instagram",
        "description": "Melapor (report) akun target secara otomatis.",
        "params": [
            {"name": "target", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Username target report"},
            {"name": "device_id", "pos": 2, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"},
            {"name": "alasan", "pos": 3, "req": False, "type": "String", "default": "Sesuatu tentang akun ini", "desc": "Alasan pelaporan akun target"},
            {"name": "my_account", "pos": 4, "req": False, "type": "String", "default": "", "desc": "Nama akun Anda untuk swap/ganti akun di awal (opsional)"}
        ],
        "examples": [
            'python3 bot_ig_report.py "spam_account" R9RY801LRPW',
            'python3 bot_ig_report.py "spam_account" R9RY801LRPW "Dia berpura-pura menjadi orang lain" "akun_saya_123"'
        ],
        "api_endpoint": "/api/jalankan-bot-report"
    },
    "bot_ig_share.py": {
        "title": "Bot Share Instagram",
        "description": "Membagikan (share) postingan terbaru dari profil target ke Direct Message penerima.",
        "params": [
            {"name": "target_user", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Username target yang postingannya ingin dibagikan"},
            {"name": "recipient", "pos": 2, "req": True, "type": "String", "default": "", "desc": "Username penerima DM"},
            {"name": "device_id", "pos": 3, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_ig_share.py "cristiano" "teman_ig" R9RY801LRPW'
        ],
        "api_endpoint": "/api/jalankan-bot-share"
    },
    "bot_ig_chat.py": {
        "title": "Bot Direct Message / Chat Instagram",
        "description": "Mengirimkan pesan singkat (DM) ke akun Instagram target.",
        "params": [
            {"name": "target_user", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Username Instagram penerima pesan"},
            {"name": "pesan", "pos": 2, "req": True, "type": "String", "default": "", "desc": "Teks pesan yang ingin dikirim"},
            {"name": "device_id", "pos": 3, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_ig_chat.py "halo_target" "Halo, salam kenal!" R9RY801LRPW'
        ],
        "api_endpoint": "/api/jalankan-bot-chat"
    },
    "bot_ig_manage.py": {
        "title": "Bot Manage Instagram (Follow/Unfollow)",
        "description": "Mengelola hubungan akun seperti Follow atau Unfollow target.",
        "params": [
            {"name": "target", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Username target Instagram"},
            {"name": "aksi", "pos": 2, "req": False, "type": "String", "default": "follow", "desc": "Aksi yang dilakukan: 'follow' atau 'unfollow'"},
            {"name": "device_id", "pos": 3, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_ig_manage.py "target_user" follow R9RY801LRPW',
            'python3 bot_ig_manage.py "target_user" unfollow R9RY801LRPW'
        ],
        "api_endpoint": "/api/jalankan-bot-manage"
    },
    "bot_ig_profile.py": {
        "title": "Bot Edit Profile Instagram",
        "description": "Mengubah data profil Instagram (Nama, Username, Bio, Foto Avatar).",
        "params": [
            {"name": "nama", "pos": 1, "req": False, "type": "String", "default": "-", "desc": "Nama tampilan baru (gunakan '-' jika tidak diubah)"},
            {"name": "username", "pos": 2, "req": False, "type": "String", "default": "-", "desc": "Username baru (gunakan '-' jika tidak diubah)"},
            {"name": "bio", "pos": 3, "req": False, "type": "String", "default": "-", "desc": "Bio profil baru (gunakan '-' jika tidak diubah)"},
            {"name": "avatar_path", "pos": 4, "req": False, "type": "String", "default": "-", "desc": "Path gambar avatar baru (gunakan '-' jika tidak diubah)"},
            {"name": "device_id", "pos": 5, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_ig_profile.py "Budi Tech" "-" "Official Account" "-" R9RY801LRPW'
        ],
        "api_endpoint": "/api/jalankan-bot-profile"
    },
    "bot_ig_scraper.py": {
        "title": "Bot Scraper Instagram Target",
        "description": "Mengambil data pengikut (followers) kompetitor atau daftar komentator (comments) dari postingan.",
        "params": [
            {"name": "target", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Username target kompetitor atau URL postingan langsung"},
            {"name": "tipe", "pos": 2, "req": False, "type": "String", "default": "followers", "desc": "Tipe scraping: 'followers' atau 'comments'"},
            {"name": "limit", "pos": 3, "req": False, "type": "Integer", "default": "50", "desc": "Jumlah username target yang ingin diekstrak"},
            {"name": "device_id", "pos": 4, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_ig_scraper.py "cristiano" followers 100 R9RY801LRPW',
            'python3 bot_ig_scraper.py "https://www.instagram.com/p/DbGhqbKE-Bn/" comments 50 R9RY801LRPW'
        ],
        "api_endpoint": "/api/jalankan-bot-scraper"
    },
    "bot_ig_follow_orang.py": {
        "title": "Bot Follow Orang Instagram",
        "description": "Mengikuti (follow) akun target secara spesifik via username/URL, atau mem-follow orang-orang dari daftar Notifikasi secara otomatis.",
        "params": [
            {"name": "target_url", "pos": 1, "req": False, "type": "String", "default": "", "desc": "Username target atau URL profil langsung (kosongkan untuk follow dari Notifikasi)"},
            {"name": "device_id", "pos": 2, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"},
            {"name": "my_account", "pos": 3, "req": False, "type": "String", "default": "", "desc": "Nama akun Anda untuk swap/ganti akun di awal (opsional)"}
        ],
        "examples": [
            'python3 bot_ig_follow_orang.py "cristiano" R9RY801LRPW',
            'python3 bot_ig_follow_orang.py "https://www.instagram.com/cristiano/" R9RY801LRPW "akun_saya_123"',
            'python3 bot_ig_follow_orang.py "" R9RY801LRPW'
        ],
        "api_endpoint": "/api/jalankan-bot-follow-orang"
    },
    "bot_instagram_logout.py": {
        "title": "Bot Logout Instagram",
        "description": "Melakukan logout akun Instagram dari perangkat.",
        "params": [
            {"name": "device_id", "pos": 1, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"},
            {"name": "mode", "pos": 2, "req": False, "type": "String", "default": "single", "desc": "Mode logout: 'single' (keluar 1 akun saja) atau 'all' (keluar seluruh akun)"}
        ],
        "examples": [
            'python3 bot_instagram_logout.py R9RY801LRPW',
            'python3 bot_instagram_logout.py R9RY801LRPW all',
            'python3 bot_instagram_logout.py R9RY801LRPW single'
        ],
        "api_endpoint": "/api/jalankan-bot-logout"
    },
    "bot_instagram_register.py": {
        "title": "Bot Register Instagram",
        "description": "Melakukan pendaftaran/registrasi akun baru Instagram.",
        "params": [
            {"name": "email_or_phone", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Email atau nomor telepon registrasi"},
            {"name": "nama_lengkap", "pos": 2, "req": True, "type": "String", "default": "", "desc": "Nama lengkap akun"},
            {"name": "username", "pos": 3, "req": True, "type": "String", "default": "", "desc": "Username akun"},
            {"name": "password", "pos": 4, "req": True, "type": "String", "default": "", "desc": "Password akun"},
            {"name": "device_id", "pos": 5, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_instagram_register.py "email@gmail.com" "Nama User" "user_baru" "Pass1234" R9RY801LRPW'
        ],
        "api_endpoint": "/api/jalankan-bot-register"
    },
    "bot_ig_scan_accounts.py": {
        "title": "Bot Scan Akun Instagram",
        "description": "Memindai seluruh akun Instagram yang terhubung pada perangkat.",
        "params": [
            {"name": "device_id", "pos": 1, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_ig_scan_accounts.py R9RY801LRPW'
        ]
    },
    "bot_instagram_login_master.py": {
        "title": "Bot Login Instagram Master",
        "description": "Melakukan login master akun Instagram ke perangkat.",
        "params": [
            {"name": "username", "pos": 1, "req": False, "type": "String", "default": "lukyytris13", "desc": "Username Instagram untuk login"},
            {"name": "password", "pos": 2, "req": False, "type": "String", "default": "Bryant12345678", "desc": "Password Instagram"},
            {"name": "device_id", "pos": 3, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_instagram_login_master.py "user_saya" "pass123" R9RY801LRPW'
        ]
    },
    "bot_instagram_login_another.py": {
        "title": "Bot Login Instagram Another",
        "description": "Melakukan login akun Instagram tambahan ke perangkat.",
        "params": [
            {"name": "username", "pos": 1, "req": False, "type": "String", "default": "lukyytris13", "desc": "Username Instagram untuk login"},
            {"name": "password", "pos": 2, "req": False, "type": "String", "default": "Bryant12345678", "desc": "Password Instagram"},
            {"name": "device_id", "pos": 3, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_instagram_login_another.py "user_saya" "pass123" R9RY801LRPW'
        ]
    },
    "bot_instagram_login_reentry.py": {
        "title": "Bot Login Instagram Reentry",
        "description": "Melakukan login ulang akun Instagram ke perangkat.",
        "params": [
            {"name": "username", "pos": 1, "req": False, "type": "String", "default": "lukyytris13", "desc": "Username Instagram untuk login"},
            {"name": "password", "pos": 2, "req": False, "type": "String", "default": "Bryant12345678", "desc": "Password Instagram"},
            {"name": "device_id", "pos": 3, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_instagram_login_reentry.py "user_saya" "pass123" R9RY801LRPW'
        ]
    },
    "switch_akun_ig.py": {
        "title": "Bot Switch Account Instagram",
        "description": "Beralih (switch) akun aktif Instagram pada perangkat tertentu secara otomatis.",
        "params": [
            {"name": "target_username", "pos": 1, "req": True, "type": "String", "default": "", "desc": "Username akun target untuk beralih"},
            {"name": "device_id", "pos": 2, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 switch_akun_ig.py "lukyytris13" R9RY801LRPW'
        ]
    },
    "bot_ig_acc.py": {
        "title": "Bot Konfirmasi Permintaan Follow",
        "description": "Secara otomatis menyetujui (konfirmasi) permintaan follow yang masuk di notifikasi.",
        "params": [
            {"name": "device_id", "pos": 1, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_ig_acc.py'
        ]
    },
    "bot_ganti_profil.py": {
        "title": "Bot Ganti Profil Massal",
        "description": "Mengganti profil akun Instagram dari file daftar akun.",
        "params": [
            {"name": "device_id", "pos": 1, "req": False, "type": "String", "default": "all", "desc": "ID Perangkat Android ADB"}
        ],
        "examples": [
            'python3 bot_ganti_profil.py R9RY801LRPW'
        ]
    }
}

def analyze_python_file(filepath):
    """Fallback AST & regex analysis for IG files not fully detailed in manual mapping"""
    filename = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        code = f.read()

    # Look for sys.argv patterns
    sys_argv_matches = re.findall(r'sys\.argv\[(\d+)\](?:\s+if\s+len\(sys\.argv\)\s*>\s*\d+\s+else\s+([^\n]+))?', code)
    params = []
    seen_pos = set()

    for pos_str, default_val in sys_argv_matches:
        pos = int(pos_str)
        if pos == 0 or pos in seen_pos:
            continue
        seen_pos.add(pos)
        default_clean = default_val.strip().strip('"\'') if default_val else ""
        params.append({
            "name": f"arg_{pos}",
            "pos": pos,
            "req": True if not default_clean else False,
            "type": "String",
            "default": default_clean,
            "desc": f"Parameter posisi ke-{pos}"
        })

    params.sort(key=lambda x: x["pos"])

    title = filename.replace(".py", "").replace("_", " ").title()
    description = f"Skrip otomatisasi Instagram {filename}"
    examples = [f"python3 {filename} " + " ".join([f'<{p["name"]}>' for p in params])] if params else [f"python3 {filename}"]

    return {
        "title": title,
        "description": description,
        "params": params,
        "examples": examples,
        "api_endpoint": ""
    }

def format_bot_txt(filename, meta):
    """Formatting single bot TXT output strictly neatly"""
    title = meta.get("title", filename)
    desc = meta.get("description", "Tidak ada deskripsi.")
    params = meta.get("params", [])
    examples = meta.get("examples", [])
    api_endpoint = meta.get("api_endpoint", "")

    lines = []
    lines.append("================================================================================")
    lines.append(f" INSTAGRAM BOT PARAMETER SPECIFICATION : {filename}")
    lines.append("================================================================================")
    lines.append(f" Nama Bot    : {title}")
    lines.append(f" File Name   : {filename}")
    lines.append(f" Deskripsi   : {desc}")
    if api_endpoint:
        lines.append(f" API Server  : {api_endpoint}")
    lines.append("--------------------------------------------------------------------------------")
    lines.append("")
    lines.append(" [CLI RUNNING COMMAND SYNTAX]")
    
    if params:
        param_str = " ".join([f'<{p["name"]}>' if p["req"] else f'[{p["name"]}]' for p in params])
        lines.append(f"   python3 {filename} {param_str}")
    else:
        lines.append(f"   python3 {filename}")

    lines.append("")
    lines.append(" [DAFTAR PARAMETER COMMAND]")
    if not params:
        lines.append("   (Tidak memerlukan parameter CLI / berjalan tanpa argument)")
    else:
        for p in params:
            status = "WAJIB" if p["req"] else "OPSIONAL"
            default_str = f" | Default: '{p['default']}'" if p['default'] != "" else ""
            lines.append(f"   * Posisi {p['pos']} : <{p['name']}> ({p['type']}) [{status}]{default_str}")
            lines.append(f"     Deskripsi : {p['desc']}")
            lines.append("")

    lines.append(" [CONTOH PERINTAH RUNNING]")
    for ex in examples:
        lines.append(f"   $ {ex}")

    lines.append("")
    lines.append("================================================================================")
    lines.append("")
    return "\n".join(lines)

def generate_all_parameters():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Bersihkan file Facebook atau non-IG dari folder txt/r/
    for existing_txt in glob.glob(os.path.join(OUTPUT_DIR, "*.txt")):
        txt_name = os.path.basename(existing_txt)
        if "facebook" in txt_name.lower() or "telegram" in txt_name.lower():
            try:
                os.remove(existing_txt)
                print(f"  [-] Removed non-IG file: txt/r/{txt_name}")
            except Exception as e:
                print(f"  [!] Failed to remove {txt_name}: {e}")

    # 2. Filter hanya file bot Instagram
    all_files = sorted(glob.glob(os.path.join(WORKSPACE_DIR, "bot_*.py")) + glob.glob(os.path.join(WORKSPACE_DIR, "bot*.py")))
    bot_files = []

    for filepath in all_files:
        fname = os.path.basename(filepath)
        # Exclude facebook & telegram
        if "facebook" in fname.lower() or "telegram" in fname.lower():
            continue
        bot_files.append(filepath)

    bot_files = sorted(list(set(bot_files)))

    print(f"[*] Ditemukan {len(bot_files)} file bot Instagram Python.")

    all_summary_lines = []
    all_summary_lines.append("================================================================================")
    all_summary_lines.append("      MASTER DAFTAR PARAMETER BOT AUTOMATION INSTAGRAM (CLI & API)")
    all_summary_lines.append("================================================================================")
    all_summary_lines.append(f" Total Bot IG Scanned : {len(bot_files)}")
    all_summary_lines.append(f" Direktori Output     : {OUTPUT_DIR}")
    all_summary_lines.append("================================================================================")
    all_summary_lines.append("")

    for filepath in bot_files:
        filename = os.path.basename(filepath)

        if filename in BOT_KNOWLEDGE:
            meta = BOT_KNOWLEDGE[filename]
        else:
            meta = analyze_python_file(filepath)

        # Generate single txt file
        txt_content = format_bot_txt(filename, meta)
        out_txt_filename = filename.replace(".py", ".txt")
        out_txt_path = os.path.join(OUTPUT_DIR, out_txt_filename)

        with open(out_txt_path, "w", encoding="utf-8") as f:
            f.write(txt_content)

        print(f"  [+] Saved: txt/r/{out_txt_filename}")

        # Add to summary
        all_summary_lines.append(txt_content)

    # Save Master Summary TXT File
    master_txt_path = os.path.join(OUTPUT_DIR, "00_DAFTAR_SEMUA_BOT_PARAM.txt")
    with open(master_txt_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_summary_lines))

    print(f"[*] Master file disesuaikan di: txt/r/00_DAFTAR_SEMUA_BOT_PARAM.txt")
    print(f"[*] SELESAI! Seluruh parameter bot Instagram telah diekstrak ke folder txt/r/")

if __name__ == "__main__":
    generate_all_parameters()
