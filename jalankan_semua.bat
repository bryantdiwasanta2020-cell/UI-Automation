@echo off
title Riemann AI & InstaADB - Jalankan Semua Service
cd /d "%~dp0"

echo ==================================================
echo  Memulai Semua Service (API, AI Server, ^& Bot Queue)
echo ==================================================
echo.

echo 1. Menyalakan Server API Python (FastAPI)...
start "FastAPI Server" cmd /k "python -m uvicorn app:app --reload"

echo 2. Menyalakan Riemann AI Server (Flask)...
start "Flask AI Server" cmd /k "python server.py"

echo 3. Menyalakan Queue Worker Bot...
start "Queue Worker Bot" cmd /k "python queue_worker.py"

echo.
echo Menunggu 3 detik agar service siap...
timeout /t 3 >nul

echo 4. Membuka Dashboard Web di Browser...
start "" "http://127.0.0.1:8000/logs.html"

echo.
echo ==================================================
echo Semua service telah berjalan di jendela terpisah.
echo Anda dapat menutup setiap jendela secara manual 
echo jika ingin menghentikan service tertentu.
echo ==================================================
echo.
pause
