# Hızlı Başlangıç Kılavuzu

## Proje Özeti

Türbin rig testleri için **optimal test matrisi** oluşturan Python programı.

### Ana Özellikler
- Minimum rake pozisyon sayısı ile maksimum swirl kapsama
- Vakum açık/kapalı durumlarını otomatik ayırma
- Kritik basınç oranı (p_critical) hesaplama
- Web arayüzü ve REST API

---

## 5 Dakikada Çalıştırın

### 1. Kurulum (30 saniye)

```bash
cd test_matrix_creator
pip install -r requirements.txt
```

### 2. Demo ile Test (30 saniye)

```bash
python turbine_test_matrix.py
```

Çıktı dosyaları:
- `turbine_test_matrix_output.xlsx` - Test matrisi
- `demo_cfd_data.xlsx` - Demo CFD verisi

### 3. Kendi Verinizle Kullanım

```python
from turbine_test_matrix import TestConfig, TurbineTestMatrix

# Konfigürasyon
config = TestConfig(
    pt_inlet=150.0,           # [kPa] Giriş basıncı
    test_margin=10.0,         # [kPa] Güvenlik marjini
    ambient=101.325,          # [kPa] Ortam basıncı
    rake_accuracy=10.0,       # [°] ±10° rake doğruluk
    rake_margin_percent=0.10  # 10% ek margin
)

# Optimizasyon
optimizer = TurbineTestMatrix(config)
optimizer.load_cfd_data("your_cfd_data.xlsx")  # Kendi dosyanız
test_matrix = optimizer.generate_test_matrix()
optimizer.export_to_excel("output.xlsx")
```

Excel dosyanızda şu sütunlar olmalı:
- `RPM`: Türbin RPM değeri
- `PressureRatio`: Basınç oranı
- `Swirl`: Swirl açısı [derece]

---

## Web Arayüzü Kullanımı

### 1. Flask API'yi Başlatın

```bash
python flask_api.py
```

API çalışır: `http://localhost:5000`

### 2. Web Arayüzünü Açın

Yeni terminal:
```bash
python -m http.server 8080
```

Tarayıcıda: `http://localhost:8080/index.html`

### 3. Adımlar

1. CFD Excel dosyanızı yükleyin
2. Test parametrelerini ayarlayın (pt_inlet, test_margin, vb.)
3. "Test Matrisi Oluştur" butonuna tıklayın
4. Sonuçları inceleyin ve Excel + görselleri indirin

---

## Görselleştirme

```python
from visualizer import TestMatrixVisualizer

# Optimizer'dan sonra
visualizer = TestMatrixVisualizer(optimizer)

# Kapsama haritası
visualizer.plot_coverage_map('coverage.png')

# Rake verimliliği
visualizer.plot_rake_efficiency('efficiency.png')

# Tam rapor
visualizer.generate_report('report.png')
```

---

## Algoritma Nasıl Çalışır?

1. **Veriyi Ayır**: P_critical'e göre vakum açık/kapalı
2. **Greedy Set Cover**: Her grupta:
   - En fazla noktayı kapsayan rake açısını bul
   - Kapsanan noktaları işaretle
   - Tüm noktalar kaplanana kadar tekrarla
3. **Optimal Çözüm**: Minimum rake sayısı

### Rake Kapsama Hesaplama

```
effective_accuracy = rake_accuracy + (rake_accuracy × margin%)
coverage_range = [rake_angle ± effective_accuracy]
```

Örnek:
- Rake = 30°, accuracy = ±10°, margin = 10%
- Effective = 10 + (10 × 0.1) = 11°
- Coverage = [19°, 41°]

### P_critical Hesaplama

```
p_critical = (pt_inlet - test_margin) / ambient
```

- **PR < p_critical**: Vakum pompası KAPALI
- **PR ≥ p_critical**: Vakum pompası AÇIK

---

## Çıktı Dosyaları

### Excel (3 sheet)

1. **TestMatrix**: Ana test matrisi
   - Tüm test noktaları
   - Rake pozisyonları
   - Vakum durumu

2. **RakeSummary**: Rake özeti
   - Her rake'in kapsadığı nokta sayısı

3. **Config**: Konfigürasyon parametreleri

---

## Örnek Çıktı

```
============================================================
TEST MATRİSİ ÖZETİ
============================================================
Toplam rake pozisyonu: 14
  - Vakum kapalı: 6 rake
  - Vakum açık: 8 rake

Toplam test noktası: 285
P_critical: 1.382
============================================================
```

Bu demek ki:
- 285 test noktasını taramak için sadece **14 rake pozisyonu** yeterli
- 6 rake ile vakum kapalı testler
- 8 rake ile vakum açık testler

Her rake set etme = test durdurma, bu yüzden **minimize etmek kritik**!

---

## API Kullanımı

Detaylı API dökümantasyonu: `API_GUIDE.md`

Temel JavaScript örneği:
```javascript
// 1. Dosya yükle
const formData = new FormData();
formData.append('file', file);
const uploadRes = await fetch('http://localhost:5000/api/upload', {
    method: 'POST',
    body: formData
});
const {file_id} = await uploadRes.json();

// 2. Optimize et
const optimizeRes = await fetch('http://localhost:5000/api/optimize', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        file_id,
        pt_inlet: 150,
        test_margin: 10,
        ambient: 101.325,
        rake_accuracy: 10,
        rake_margin_percent: 10
    })
});
const result = await optimizeRes.json();

// 3. İndir
window.open(`http://localhost:5000/api/download/${result.result_id}`);
```

---

## Sık Sorulan Sorular

### 1. Excel dosyam farklı sütun adlarına sahip?

Sütunları `RPM`, `PressureRatio`, `Swirl` olarak yeniden adlandırın.

### 2. Rake margin nedir?

Rake accuracy'ye ekstra güvenlik payı. %10 = ±10°'ye +1° daha ekler.

### 3. P_critical nasıl belirlenir?

Tasarımcıdan `pt_inlet` ve `test_margin` değerlerini alın. Sistem otomatik hesaplar.

### 4. Çok fazla rake pozisyonu çıkıyor?

- Rake margin'i azaltın
- Rake accuracy'yi arttırın (±15° gibi)
- CFD veri sayısını azaltın (kritik noktaları seçin)

### 5. Web arayüzü yerel ağda erişilebilir mi?

Evet:
```bash
# Flask API
python flask_api.py  # 0.0.0.0:5000 zaten tüm IP'lere açık

# Web server
python -m http.server 8080 --bind 0.0.0.0
```

Ağdaki diğer bilgisayarlardan: `http://YOUR_IP:8080/index.html`

---

## Destek

- Detaylı kullanım: `README.md`
- API dokümantasyonu: `API_GUIDE.md`
- Kaynak kod: `turbine_test_matrix.py`

Başarılar! 🚀
