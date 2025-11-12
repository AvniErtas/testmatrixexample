# Flask API Kullanım Kılavuzu

## Kurulum

```bash
pip install -r requirements.txt
```

## API Başlatma

```bash
python flask_api.py
```

API çalışacak: `http://localhost:5000`

## Endpoint'ler

### 1. Sağlık Kontrolü

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "Turbine Test Matrix API is running"
}
```

### 2. CFD Dosyası Yükle

```http
POST /api/upload
Content-Type: multipart/form-data
```

**Parameters:**
- `file`: Excel dosyası (.xlsx, .xls)

**Response:**
```json
{
  "file_id": "cfd_abc123.xlsx",
  "filename": "my_data.xlsx",
  "stats": {
    "total_points": 285,
    "rpm_range": [50, 140],
    "pressure_ratio_range": [1.2, 2.5],
    "swirl_range": [-60, 89],
    "columns": ["RPM", "PressureRatio", "Swirl"]
  },
  "preview": [...]
}
```

### 3. Test Matrisi Optimizasyonu

```http
POST /api/optimize
Content-Type: application/json
```

**Request Body:**
```json
{
  "file_id": "cfd_abc123.xlsx",
  "pt_inlet": 150.0,
  "test_margin": 10.0,
  "ambient": 101.325,
  "rake_accuracy": 10.0,
  "rake_margin_percent": 10
}
```

**Response:**
```json
{
  "result_id": "result_xyz789.xlsx",
  "visualization_id": "viz_xyz789.png",
  "summary": {
    "total_rakes": 14,
    "total_points": 285,
    "p_critical": 1.382,
    "vacuum_off_rakes": 6,
    "vacuum_on_rakes": 8
  },
  "rake_positions": [
    {
      "sequence": 1,
      "angle": -16.9,
      "vacuum_required": "No",
      "points_covered": 9
    },
    ...
  ],
  "config": {
    "pt_inlet": 150.0,
    "test_margin": 10.0,
    "ambient": 101.325,
    "rake_accuracy": 10.0,
    "rake_margin_percent": 10,
    "p_critical": 1.382
  }
}
```

### 4. P_critical Hesaplama

```http
POST /api/calculate-pcritical
Content-Type: application/json
```

**Request Body:**
```json
{
  "pt_inlet": 150.0,
  "test_margin": 10.0,
  "ambient": 101.325
}
```

**Response:**
```json
{
  "p_critical": 1.382,
  "pt_inlet": 150.0,
  "test_margin": 10.0,
  "ambient": 101.325
}
```

### 5. Dosya İndirme

```http
GET /api/download/<file_id>
```

**Example:**
```
GET /api/download/result_xyz789.xlsx
GET /api/download/viz_xyz789.png
```

**Response:** Dosya indirme

### 6. Sonuç Önizleme

```http
GET /api/preview/<result_id>?limit=20
```

**Response:**
```json
{
  "preview": [
    {
      "TestSequence": 1,
      "RakeAngle": -16.9,
      "CoverageMin": -27.9,
      "CoverageMax": -5.9,
      "VacuumRequired": "No",
      "RPM": 50,
      "PressureRatio": 1.2,
      "Swirl": -15.5
    },
    ...
  ],
  "total_rows": 285
}
```

## JavaScript Örnek Kullanım

### Dosya Yükleme

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:5000/api/upload', {
    method: 'POST',
    body: formData
});

const data = await response.json();
console.log('File ID:', data.file_id);
```

### Optimizasyon

```javascript
const response = await fetch('http://localhost:5000/api/optimize', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        file_id: fileId,
        pt_inlet: 150.0,
        test_margin: 10.0,
        ambient: 101.325,
        rake_accuracy: 10.0,
        rake_margin_percent: 10
    })
});

const result = await response.json();
console.log('Result ID:', result.result_id);
console.log('Total Rakes:', result.summary.total_rakes);
```

### Dosya İndirme

```javascript
// Excel indirme
window.open(`http://localhost:5000/api/download/${resultId}`, '_blank');

// Görselleştirme indirme
window.open(`http://localhost:5000/api/download/${vizId}`, '_blank');
```

## Web Arayüzü

`index.html` dosyasını bir web sunucusunda çalıştırın:

```bash
# Python HTTP sunucusu
python -m http.server 8080
```

Tarayıcıda açın: `http://localhost:8080/index.html`

## CORS

API, tüm kaynaklardan erişime izin verir (CORS enabled). Production'da bunu sınırlandırın:

```python
# flask_api.py
from flask_cors import CORS

# Sadece belirli origin'e izin ver
CORS(app, origins=['http://your-domain.com'])
```

## Güvenlik Notları

1. **Dosya Boyutu:** Max 16MB (değiştirilebilir)
2. **Dosya Tipi:** Sadece .xlsx, .xls
3. **Geçici Dosyalar:** 1 saat sonra otomatik silinir
4. **Production:** HTTPS kullanın, API key ekleyin

## Hata Yönetimi

Tüm hata durumlarında uygun HTTP status code ve JSON response döner:

```json
{
  "error": "Hata mesajı buraya"
}
```

**Status Codes:**
- 200: Başarılı
- 400: Bad request (geçersiz parametreler)
- 404: Dosya bulunamadı
- 500: Sunucu hatası

## Test

```bash
# API test (curl ile)
curl http://localhost:5000/api/health

# Dosya yükleme testi
curl -X POST -F "file=@demo_cfd_data.xlsx" http://localhost:5000/api/upload
```

## Production Deployment

### Gunicorn ile

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 flask_api:app
```

### Docker ile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "flask_api:app"]
```

## Destek

Sorularınız için issue açabilirsiniz.
