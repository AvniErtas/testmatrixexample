# EXE Oluşturma Kılavuzu

## Windows için EXE Oluşturma

### Gereksinimler

```bash
pip install pyinstaller
```

### Build Komutu

```bash
pyinstaller build_exe.spec
```

### Çıktı

`dist/TurbineTestMatrix.exe` dosyası oluşturulacak.

## Kullanım

1. `TurbineTestMatrix.exe` dosyasını çift tıklayın
2. Otomatik olarak:
   - Flask API başlatılır (port 5000)
   - Web sunucusu başlatılır (port 8080)
   - Tarayıcı açılır (http://localhost:8080/index.html)
3. Uygulamayı kullanın!
4. Kapatmak için console penceresini kapatın

## Alternatif: Basit Batch Script (Windows)

Eğer EXE oluşturmak istemiyorsanız, `start.bat` dosyası oluşturun:

```batch
@echo off
echo Turbine Test Matrix Optimizer baslatiiliyor...

start "Flask API" cmd /k python flask_api.py
timeout /t 3 /nobreak >nul

start "Web Server" cmd /k python -m http.server 8080
timeout /t 2 /nobreak >nul

start http://localhost:8080/index.html

echo.
echo Hazir! Tarayici acildi.
echo Kapatmak icin tum console pencerelerini kapatin.
pause
```

## macOS/Linux için Shell Script

`start.sh` dosyası oluşturun:

```bash
#!/bin/bash
echo "Turbine Test Matrix Optimizer başlatılıyor..."

# Flask API'yi arka planda başlat
python flask_api.py &
FLASK_PID=$!
sleep 3

# Web sunucusunu arka planda başlat
python -m http.server 8080 &
WEB_PID=$!
sleep 2

# Tarayıcıyı aç
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:8080/index.html
elif command -v open > /dev/null; then
    open http://localhost:8080/index.html
fi

echo "Hazır! Tarayıcı açıldı."
echo "Durdurmak için CTRL+C basın"

# Cleanup
trap "kill $FLASK_PID $WEB_PID 2>/dev/null" EXIT

wait
```

Çalıştırılabilir yapın:
```bash
chmod +x start.sh
./start.sh
```

## Termux (Android) için

```bash
#!/bin/bash
python flask_api.py &
sleep 3
python -m http.server 8080 &
sleep 2
termux-open-url http://localhost:8080/index.html
wait
```

## Docker İçin

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 5000 8080

CMD python flask_api.py & python -m http.server 8080
```

Build ve çalıştır:
```bash
docker build -t turbine-matrix .
docker run -p 5000:5000 -p 8080:8080 turbine-matrix
```

## Notlar

- **Windows:** PyInstaller ile EXE veya batch script kullanın
- **macOS/Linux:** Shell script kullanın
- **Android (Termux):** Termux script kullanın
- **Docker:** Container olarak çalıştırın

Her durumda Flask API (5000) ve Web Server (8080) portları kullanılır.
