#!/bin/bash

# Pastikan script berjalan di folder tempat script berada
cd "$(dirname "$0")"

echo "Menyalakan Server API Python InstaADB..."
# Menjalankan uvicorn di background
python3 -m uvicorn app:app --reload &
UVICORN_PID=$!

# Menunggu 2 detik agar server uvicorn siap
sleep 2

echo "Membuka Dashboard Web di Browser..."
if command -v xdg-open > /dev/null; then
    xdg-open "http://127.0.0.1:8000/logs.html"
elif command -v open > /dev/null; then
    open "http://127.0.0.1:8000/logs.html"
else
    echo "Harap buka browser manual ke: http://127.0.0.1:8000/logs.html"
fi

# Tunggu proses uvicorn selesai
wait $UVICORN_PID
