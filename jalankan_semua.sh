#!/bin/bash

# Pastikan script berjalan di folder tempat script berada
cd "$(dirname "$0")"

echo "=================================================="
echo " Memulai Semua Service (API, AI Server, & Bot Queue) "
echo "=================================================="

# Daftar PID proses untuk dihentikan saat keluar
pids=()

# Fungsi pembersihan untuk mematikan semua background process saat script dihentikan (Ctrl+C)
cleanup() {
    echo -e "\n\nMenghentikan semua service..."
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
        fi
    done
    echo "Semua service telah dihentikan secara bersih."
    exit 0
}

# Tangkap sinyal interrupt (Ctrl+C) dan terminate
trap cleanup SIGINT SIGTERM

# 1. Menjalankan Server API Python InstaADB (FastAPI)
echo "1. Menyalakan Server API Python (FastAPI)..."
python3 -m uvicorn app:app --reload > uvicorn.log 2>&1 &
API_PID=$!
pids+=($API_PID)

# 2. Menjalankan Riemann AI Server (Flask)
echo "2. Menyalakan Riemann AI Server (Flask)..."
python3 server.py > ai_server.log 2>&1 &
SERVER_PID=$!
pids+=($SERVER_PID)

# 3. Menjalankan Queue Worker Bot
echo "3. Menyalakan Queue Worker Bot..."
python3 queue_worker.py > queue_worker.log 2>&1 &
WORKER_PID=$!
pids+=($WORKER_PID)

# Menunggu 3 detik agar service siap
sleep 3

# 4. Membuka Dashboard di Browser
echo "4. Membuka Dashboard Web..."
URL="http://127.0.0.1:8000/logs.html"
if command -v xdg-open > /dev/null; then
    xdg-open "$URL"
elif command -v open > /dev/null; then
    open "$URL"
else
    echo "Harap buka browser manual ke: $URL"
fi

echo "--------------------------------------------------"
echo "Semua service sedang berjalan di background:"
echo " - FastAPI API Server (Log disimpan di uvicorn.log)"
echo " - Flask AI Server    (Log disimpan di ai_server.log)"
echo " - Queue Worker Bot   (Log disimpan di queue_worker.log)"
echo ""
echo "Tekan Ctrl+C untuk menghentikan semua service secara bersamaan."
echo "--------------------------------------------------"

# Tunggu semua proses background selesai
wait
