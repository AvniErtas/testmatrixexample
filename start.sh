#!/bin/bash

echo ""
echo "================================================================"
echo ""
echo "     TURBINE TEST MATRIX OPTIMIZER"
echo ""
echo "================================================================"
echo ""
echo "Başlatılıyor..."
echo ""

# Flask API'yi arka planda başlat
echo "[1/3] Flask API başlatılıyor (port 5000)..."
python flask_api.py &
FLASK_PID=$!
sleep 3

# Web sunucusunu arka planda başlat
echo "[2/3] Web sunucusu başlatılıyor (port 8080)..."
python -m http.server 8080 &
WEB_PID=$!
sleep 2

# Tarayıcıyı aç
echo "[3/3] Tarayıcı açılıyor..."
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:8080/index.html
elif command -v open > /dev/null; then
    open http://localhost:8080/index.html
else
    echo "Tarayıcınızda açın: http://localhost:8080/index.html"
fi

echo ""
echo "================================================================"
echo ""
echo "  ✅ HAZIR! Tarayıcı açıldı."
echo ""
echo "  Web Arayüz: http://localhost:8080/index.html"
echo "  Flask API:  http://localhost:5000"
echo ""
echo "  Durdurmak için CTRL+C basın"
echo ""
echo "================================================================"
echo ""

# Cleanup fonksiyonu
cleanup() {
    echo ""
    echo "Kapatılıyor..."
    kill $FLASK_PID $WEB_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Bekle
wait
