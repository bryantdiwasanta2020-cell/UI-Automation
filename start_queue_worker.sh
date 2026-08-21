#!/bin/bash

# Pastikan script berjalan di folder tempat script berada
cd "$(dirname "$0")"

echo ""
echo "===================================="
echo "  Memulai Queue Worker Bot..."
echo "===================================="
python3 queue_worker.py
