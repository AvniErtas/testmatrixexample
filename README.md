# Turbine Test Matrix Optimizer

Türbin rig testleri için optimal test matrisi oluşturan Python programı. CFD analiz verilerinden minimum rake pozisyon sayısı ile maksimum swirl kapsama alanı sağlar.

## Özellikler

- CFD analiz verilerini Excel'den otomatik okuma
- Kritik basınç oranı (p_critical) hesaplama
- Vakum açık/kapalı durumlarını otomatik ayırma
- Greedy set cover algoritması ile optimal rake pozisyonları
- Configurable rake accuracy ve güvenlik marjini
- Excel çıktısı (test matrisi, rake özeti, konfigürasyon)

## Kurulum

```bash
pip install -r requirements.txt
```

## 🚀 Hızlı Başlangıç (Tek Tıkla)

### Windows
```bash
start.bat
```
Dosyayı çift tıklayın, her şey otomatik başlar!

### Linux/macOS
```bash
./start.sh
```

### Python ile Manuel
```bash
python run_app.py
```

Otomatik olarak:
- Flask API başlar (port 5000)
- Web sunucusu başlar (port 8080)
- Tarayıcı açılır

## Kullanım

### 1. CFD Verilerinizi Hazırlayın

Excel dosyanızda şu sütunlar olmalı:
- `RPM`: Türbin RPM değerleri (örn: 50, 55, 60, ... 140)
- `PressureRatio`: Basınç oranı değerleri
- `Swirl`: Swirl açısı değerleri [derece]

### 2. Konfigürasyonu Ayarlayın

```python
from turbine_test_matrix import TestConfig, TurbineTestMatrix

config = TestConfig(
    pt_inlet=150.0,           # [kPa] Giriş toplam basıncı
    test_margin=10.0,         # [kPa] Test güvenlik marjini
    ambient=101.325,          # [kPa] Ortam basıncı
    rake_accuracy=10.0,       # [derece] Rake doğruluk (±10°)
    rake_margin_percent=0.10  # Ek güvenlik marjini (10%)
)
```

### 3. Optimizasyonu Çalıştırın

```python
# Optimizer oluştur
optimizer = TurbineTestMatrix(config)

# CFD verilerini yükle
optimizer.load_cfd_data("cfd_data.xlsx")

# Test matrisini oluştur
test_matrix = optimizer.generate_test_matrix()

# Excel'e kaydet
optimizer.export_to_excel("test_matrix_output.xlsx")
```

## Parametreler

### TestConfig Parametreleri

| Parametre | Açıklama | Birim | Örnek Değer |
|-----------|----------|-------|-------------|
| `pt_inlet` | Giriş toplam basıncı | kPa | 150.0 |
| `test_margin` | Test güvenlik marjini | kPa | 10.0 |
| `ambient` | Ortam basıncı (standart) | kPa | 101.325 |
| `rake_accuracy` | Rake açısal doğruluk | derece | 10.0 (±10°) |
| `rake_margin_percent` | Ek güvenlik marjini | % | 0.10 (10%) |
| `rake_min` | Rake minimum açı | derece | -89.0 |
| `rake_max` | Rake maximum açı | derece | 89.0 |

### Kritik Basınç Oranı Hesaplama

```
p_critical = (pt_inlet - test_margin) / ambient
```

- **p_critical < PressureRatio**: Vakum pompası KAPALI
- **p_critical ≥ PressureRatio**: Vakum pompası AÇIK

### Rake Kapsama Alanı Hesaplama

```
effective_accuracy = rake_accuracy + (rake_accuracy × rake_margin_percent)
coverage_min = rake_angle - effective_accuracy
coverage_max = rake_angle + effective_accuracy
```

Örnek:
- Rake angle = 30°, accuracy = ±10°, margin = 10%
- Effective accuracy = 10 + (10 × 0.1) = 11°
- Coverage: [19°, 41°]

## Çıktı Dosyaları

### Excel Çıktısı (3 sheet)

1. **TestMatrix**: Ana test matrisi
   - TestSequence: Test sırası
   - RakeAngle: Rake açısı
   - CoverageMin/Max: Kapsama aralığı
   - VacuumRequired: Vakum durumu
   - RPM, PressureRatio, Swirl: Test noktası parametreleri

2. **RakeSummary**: Rake özet tablosu
   - Her rake pozisyonunun kapsadığı nokta sayısı

3. **Config**: Kullanılan konfigürasyon parametreleri

## Algoritma

Program **Greedy Set Cover** algoritması kullanır:

1. Veriyi vakum durumuna göre ayır (açık/kapalı)
2. Her grup için:
   - Tüm olası rake açılarını tara
   - En fazla noktayı kapsayan rake'i seç
   - Kapsanan noktaları işaretle
   - Tüm noktalar kaplanana kadar tekrarla

Bu yaklaşım optimal veya optimal'e yakın çözüm üretir ve minimum rake pozisyon sayısı sağlar.

## Örnek Çalıştırma

```bash
python turbine_test_matrix.py
```

Demo veri ile test etmek için dosya bulunamazsa otomatik demo veri oluşturulur.

## Çıktı Örneği

```
✓ 285 satır veri yüklendi
✓ P_critical = 1.381
✓ Vakum gerektiren noktalar: 168
✓ Vakum gerektirmeyen noktalar: 117

============================================================
Optimizasyon: Vakum KAPALI
Toplam test noktası: 117
Swirl aralığı: [-60.0°, -12.5°]
============================================================
Rake #1: -35.2° [-46.2° - -24.2°] → 45 nokta | Kalan: 72
Rake #2: -15.8° [-26.8° - -4.8°] → 72 nokta | Kalan: 0
============================================================
✓ Toplam 2 rake pozisyonu bulundu
============================================================

============================================================
Optimizasyon: Vakum AÇIK
Toplam test noktası: 168
Swirl aralığı: [-10.3°, 68.9°]
============================================================
Rake #1: 29.4° [18.4° - 40.4°] → 94 nokta | Kalan: 74
Rake #2: 54.2° [43.2° - 65.2°] → 74 nokta | Kalan: 0
============================================================
✓ Toplam 2 rake pozisyonu bulundu
============================================================

============================================================
TEST MATRİSİ ÖZETİ
============================================================
Toplam rake pozisyonu: 4
  - Vakum kapalı: 2 rake
  - Vakum açık: 2 rake

Toplam test noktası: 285
P_critical: 1.381
============================================================

✓ Test matrisi kaydedildi: turbine_test_matrix_output.xlsx
```

## JavaScript Entegrasyonu İçin

Bu kod temel Python backend'ini sağlar. JavaScript/web arayüzü için:

1. **Python API**: Flask/FastAPI ile REST API oluşturun
2. **Parametreler**: `rake_margin_percent`, `pt_inlet`, vb. kullanıcıdan alın
3. **File Upload**: Excel dosyası yükleme endpoint'i ekleyin
4. **Sonuç İndirme**: Oluşturulan Excel'i indirme endpoint'i

Örnek Flask entegrasyonu için `flask_api.py` oluşturulabilir.

## Lisans

MIT

## İletişim

Sorularınız için issue açabilirsiniz.
