#!/bin/bash

# Pastikan script berjalan di folder tempat script berada
cd "$(dirname "$0")"

echo ""
echo "===================================="
echo "  Memulai Riemann AI Server..."
echo "===================================="
python3 server.py
