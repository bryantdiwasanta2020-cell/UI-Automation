@echo off
echo Menyalakan Server API Python InstaADB...
start cmd /k "python -m uvicorn app:app --reload"

echo Membuka Dashboard Web di Browser...
start "" "http://127.0.0.1:8000/logs.html"

exit