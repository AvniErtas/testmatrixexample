"""
Turbine Test Matrix Optimizer - Standalone Launcher
Tek tıkla Flask API ve web tarayıcısını başlatır
"""

import subprocess
import threading
import time
import webbrowser
import os
import sys

def get_resource_path(relative_path):
    """PyInstaller ile paketlenmiş dosyaların yolunu bulur"""
    try:
        # PyInstaller temp folder
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def start_flask_api():
    """Flask API'yi başlatır"""
    print("🚀 Flask API başlatılıyor...")
    # flask_api.py'yi import et ve çalıştır
    import flask_api
    flask_api.app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)

def start_web_server():
    """HTTP sunucusunu başlatır"""
    print("🌐 Web sunucusu başlatılıyor...")
    os.chdir(get_resource_path('.'))
    subprocess.run([sys.executable, '-m', 'http.server', '8080'],
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)

def open_browser():
    """Tarayıcıyı açar"""
    time.sleep(3)  # API ve web server'ın başlaması için bekle
    print("🌍 Tarayıcı açılıyor...")
    webbrowser.open('http://localhost:8080/index.html')

def main():
    """Ana fonksiyon"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        TURBINE TEST MATRIX OPTIMIZER                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Başlatılıyor...
    """)

    # Flask API'yi ayrı thread'de başlat
    api_thread = threading.Thread(target=start_flask_api, daemon=True)
    api_thread.start()

    # Web server'ı ayrı thread'de başlat
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()

    # Tarayıcıyı aç
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    print("""
✅ Hazır!

📡 Servisler:
   - Flask API: http://localhost:5000
   - Web Arayüz: http://localhost:8080/index.html

⚠️  Bu pencereyi kapatmayın! Uygulama çalışmaya devam ediyor...
⌨️  Durdurmak için CTRL+C basın
    """)

    try:
        # Ana thread'i beklet
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Uygulama kapatılıyor...")
        sys.exit(0)

if __name__ == "__main__":
    main()
