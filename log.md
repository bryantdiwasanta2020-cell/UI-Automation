# Spesifikasi Log RPA — Format JSONL

## Ringkasan

RPA menghasilkan 2 jenis log, masing-masing dalam format **JSONL** (satu baris = satu JSON object independen, append-only):

1. `log_device/` — status terkini tiap device
2. `log_action/` — riwayat step eksekusi per run

---

## 1. Folder `log_device/`

**Nama file:** `{device_id}.jsonl`
**Contoh:** `R9RYA03002Z.jsonl`

**Perilaku:** setiap kali device melakukan aksi atau statusnya berubah, sistem **append satu baris baru** ke file ini. File ini otomatis menjadi riwayat aktivitas device dari waktu ke waktu.

### Struktur per baris

| Field | Tipe | Nilai / Contoh | Keterangan |
|---|---|---|---|
| `sosmed` | string | `"x"`, `"instagram"`, `"tiktok"` | Platform target |
| `action` | string | `"like"` \| `"comment"` | Aksi yang dijalankan |
| `username` | string | `"johndoe123"` | Akun yang dipakai device saat itu |
| `message` | string | `"text"` \| `"media"` | Tipe konten target *(⚠️ belum final, lihat catatan)* |
| `status` | string | `"on_progress"` \| `"complete"` | Status eksekusi *(⚠️ belum final, lihat catatan)* |
| `error` | string \| null | `null` atau pesan error | Error jika ada |
| `mode` | string | `"farming"` \| `"campaign"` | Mode operasi RPA |
| `timestamp` | string | ISO 8601 | Waktu event |

### Contoh isi `log_device/R9RYA03002Z.jsonl`

```jsonl
{"sosmed": "x", "action": "like", "username": "johndoe123", "message": "text", "status": "on_progress", "error": null, "mode": "campaign", "timestamp": "2026-07-16T14:32:10Z"}
{"sosmed": "x", "action": "like", "username": "johndoe123", "message": "text", "status": "complete", "error": null, "mode": "campaign", "timestamp": "2026-07-16T14:32:25Z"}
```

> Untuk mengetahui status device **saat ini**, cukup baca **baris terakhir** dari file ini.

---

## 2. Folder `log_action/`

**Nama file:** `{date}_{sosmed}_{action}_{device_id}.jsonl`
**Contoh:** `2026-07-16_x_like_R9RYA03002Z.jsonl`

**Perilaku:** satu file baru dibuat per run/eksekusi (bukan di-*update*, tapi file baru tiap kombinasi tanggal+sosmed+action+device berbeda). Tiap step RPA langsung di-append sebagai satu baris baru saat step itu terjadi.

Body **tidak perlu** mengulang `device_id`, `sosmed`, `action`, `date` — karena semua info itu sudah tersedia di nama file.

### Struktur per baris

| Field | Tipe | Nilai / Contoh | Keterangan |
|---|---|---|---|
| `step` | string | `"skip"`, `"check_login"`, `"open_app"`, `"check_screen"`, `"login"`, `"comment"` | Nama step dalam alur RPA |
| `status` | string | `"on_progress"` \| `"complete"` | Status step tsb |
| `error` | string \| null | `null` atau pesan error | Error di step tsb jika ada |
| `timestamp` | string | ISO 8601 | Waktu step dieksekusi |

### Contoh isi `log_action/2026-07-16_x_like_R9RYA03002Z.jsonl`

```jsonl
{"step": "skip", "status": "complete", "error": null, "timestamp": "2026-07-16T14:30:00Z"}
{"step": "check_login", "status": "complete", "error": null, "timestamp": "2026-07-16T14:30:05Z"}
{"step": "open_app", "status": "complete", "error": null, "timestamp": "2026-07-16T14:30:10Z"}
{"step": "check_screen", "status": "complete", "error": null, "timestamp": "2026-07-16T14:30:15Z"}
{"step": "login", "status": "complete", "error": "Session expired, re-login required", "timestamp": "2026-07-16T14:30:20Z"}
```

---

## Alur Lengkap (End-to-End)

1. RPA menerima tugas: device `R9RYA03002Z`, sosmed `x`, action `like`, mode `campaign`.
2. Tiap step dieksekusi → langsung **append 1 baris** ke `log_action/2026-07-16_x_like_R9RYA03002Z.jsonl`.
3. Tiap kali status device berubah (mulai, selesai, atau error) → **append 1 baris** ke `log_device/R9RYA03002Z.jsonl`.
4. Untuk cek status device *saat ini* → baca **baris terakhir** dari `log_device/{device_id}.jsonl`.
5. Untuk audit satu run tertentu → buka file `log_action` sesuai nama (tanggal+sosmed+action+device), baca semua baris berurutan dari atas ke bawah.

---

## Poin yang Masih Perlu Diklarifikasi

1. **`message`** (di `log_device`) — apakah benar cuma tipe konten (`"text"`/`"media"`), atau ada makna lain?
2. **`status`** — apakah cuma `"on_progress"` dan `"complete"`, atau perlu ditambah `"failed"`?
3. Nama-nama `step` di `log_action` (`skip`, `check_login`, `open_app`, `check_screen`, `login`/`comment`) — apakah penamaan ini sudah final atau masih bisa berubah?

---
*Dibuat berdasarkan diskusi dan sketsa whiteboard, 28 Juli 2026.*
