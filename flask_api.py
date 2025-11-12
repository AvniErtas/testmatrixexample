"""
Flask Web API for Turbine Test Matrix Optimizer
JavaScript frontend ile entegrasyon için REST API
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
from werkzeug.utils import secure_filename
import tempfile
import json
from turbine_test_matrix import TestConfig, TurbineTestMatrix
from visualizer import TestMatrixVisualizer

app = Flask(__name__)
CORS(app)  # JavaScript'ten erişim için

# Geçici dosyalar için
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max


def allowed_file(filename):
    """Dosya uzantısı kontrolü"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health_check():
    """API sağlık kontrolü"""
    return jsonify({
        'status': 'healthy',
        'message': 'Turbine Test Matrix API is running'
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    CFD Excel dosyasını yükle

    Form data:
    - file: Excel dosyası

    Returns:
    - file_id: Geçici dosya ID'si
    - preview: İlk 10 satır önizleme
    - stats: Veri istatistikleri
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Dosya bulunamadı'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_id = f"cfd_{os.urandom(8).hex()}.xlsx"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        file.save(filepath)

        # Dosyayı oku ve önizleme oluştur
        try:
            df = pd.read_excel(filepath)

            # Sütun kontrolü
            required_cols = ['RPM', 'PressureRatio', 'Swirl']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                os.remove(filepath)
                return jsonify({
                    'error': f'Eksik sütunlar: {", ".join(missing_cols)}',
                    'required_columns': required_cols,
                    'found_columns': list(df.columns)
                }), 400

            # İstatistikler
            stats = {
                'total_points': len(df),
                'rpm_range': [float(df['RPM'].min()), float(df['RPM'].max())],
                'pressure_ratio_range': [float(df['PressureRatio'].min()),
                                         float(df['PressureRatio'].max())],
                'swirl_range': [float(df['Swirl'].min()), float(df['Swirl'].max())],
                'columns': list(df.columns)
            }

            # Önizleme
            preview = df.head(10).to_dict('records')

            return jsonify({
                'file_id': file_id,
                'filename': filename,
                'stats': stats,
                'preview': preview
            })

        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Dosya okuma hatası: {str(e)}'}), 400

    return jsonify({'error': 'Geçersiz dosya formatı'}), 400


@app.route('/api/optimize', methods=['POST'])
def optimize_matrix():
    """
    Test matrisini optimize et

    JSON body:
    {
        "file_id": "cfd_xxx.xlsx",
        "pt_inlet": 150.0,
        "test_margin": 10.0,
        "ambient": 101.325,
        "rake_accuracy": 10.0,
        "rake_margin_percent": 10
    }

    Returns:
    - result_id: Sonuç dosya ID'si
    - summary: Özet istatistikler
    - rake_positions: Rake pozisyonları listesi
    """
    data = request.json

    # Parametreleri al
    file_id = data.get('file_id')
    pt_inlet = float(data.get('pt_inlet', 150.0))
    test_margin = float(data.get('test_margin', 10.0))
    ambient = float(data.get('ambient', 101.325))
    rake_accuracy = float(data.get('rake_accuracy', 10.0))
    rake_margin_percent = float(data.get('rake_margin_percent', 10)) / 100.0

    # Dosya kontrolü
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Dosya bulunamadı'}), 404

    try:
        # Konfigürasyon
        config = TestConfig(
            pt_inlet=pt_inlet,
            test_margin=test_margin,
            ambient=ambient,
            rake_accuracy=rake_accuracy,
            rake_margin_percent=rake_margin_percent
        )

        # Optimizasyon
        optimizer = TurbineTestMatrix(config)
        optimizer.load_cfd_data(filepath)
        test_matrix = optimizer.generate_test_matrix()

        # Sonuç dosyasını kaydet
        result_id = f"result_{os.urandom(8).hex()}.xlsx"
        result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_id)
        optimizer.export_to_excel(result_path)

        # Görselleştirme oluştur
        visualizer = TestMatrixVisualizer(optimizer)
        viz_id = f"viz_{os.urandom(8).hex()}.png"
        viz_path = os.path.join(app.config['UPLOAD_FOLDER'], viz_id)
        visualizer.generate_report(viz_path)

        # Rake test planı oluştur (yeni detaylı görselleştirme)
        test_plan_id = f"testplan_{os.urandom(8).hex()}.png"
        test_plan_path = os.path.join(app.config['UPLOAD_FOLDER'], test_plan_id)
        visualizer.plot_rake_test_plan(test_plan_path)

        # Özet istatistikler
        rake_summary = test_matrix.groupby(['TestSequence', 'RakeAngle',
                                            'VacuumRequired']).size().reset_index(name='PointCount')

        rake_positions = []
        for _, row in rake_summary.iterrows():
            rake_positions.append({
                'sequence': int(row['TestSequence']),
                'angle': float(row['RakeAngle']),
                'vacuum_required': row['VacuumRequired'],
                'points_covered': int(row['PointCount'])
            })

        summary = {
            'total_rakes': len(rake_summary),
            'total_points': len(test_matrix),
            'p_critical': float(optimizer.p_critical),
            'vacuum_off_rakes': int((rake_summary['VacuumRequired'] == 'No').sum()),
            'vacuum_on_rakes': int((rake_summary['VacuumRequired'] == 'Yes').sum()),
        }

        return jsonify({
            'result_id': result_id,
            'visualization_id': viz_id,
            'test_plan_id': test_plan_id,
            'summary': summary,
            'rake_positions': rake_positions,
            'config': {
                'pt_inlet': pt_inlet,
                'test_margin': test_margin,
                'ambient': ambient,
                'rake_accuracy': rake_accuracy,
                'rake_margin_percent': rake_margin_percent * 100,
                'p_critical': float(optimizer.p_critical)
            }
        })

    except Exception as e:
        return jsonify({'error': f'Optimizasyon hatası: {str(e)}'}), 500


@app.route('/api/download/<file_id>', methods=['GET'])
def download_file(file_id):
    """
    Sonuç dosyasını indir

    Args:
    - file_id: Dosya ID'si (result_xxx.xlsx veya viz_xxx.png)
    """
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_id)

    if not os.path.exists(filepath):
        return jsonify({'error': 'Dosya bulunamadı'}), 404

    return send_file(filepath, as_attachment=True)


@app.route('/api/preview/<result_id>', methods=['GET'])
def preview_results(result_id):
    """
    Sonuç önizlemesi

    Args:
    - result_id: Sonuç dosya ID'si

    Query params:
    - limit: Önizleme satır sayısı (default: 20)
    """
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], result_id)

    if not os.path.exists(filepath):
        return jsonify({'error': 'Dosya bulunamadı'}), 404

    limit = int(request.args.get('limit', 20))

    try:
        # TestMatrix sheet'ini oku
        df = pd.read_excel(filepath, sheet_name='TestMatrix')
        preview = df.head(limit).to_dict('records')

        return jsonify({
            'preview': preview,
            'total_rows': len(df)
        })

    except Exception as e:
        return jsonify({'error': f'Önizleme hatası: {str(e)}'}), 500


@app.route('/api/calculate-pcritical', methods=['POST'])
def calculate_pcritical():
    """
    P_critical hesapla (frontend validasyon için)

    JSON body:
    {
        "pt_inlet": 150.0,
        "test_margin": 10.0,
        "ambient": 101.325
    }
    """
    data = request.json

    pt_inlet = float(data.get('pt_inlet', 150.0))
    test_margin = float(data.get('test_margin', 10.0))
    ambient = float(data.get('ambient', 101.325))

    p_critical = (pt_inlet - test_margin) / ambient

    return jsonify({
        'p_critical': round(p_critical, 4),
        'pt_inlet': pt_inlet,
        'test_margin': test_margin,
        'ambient': ambient
    })


@app.route('/')
def index():
    """Ana sayfa - API dökümantasyonu"""
    return jsonify({
        'name': 'Turbine Test Matrix Optimizer API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/health': 'Sağlık kontrolü',
            'POST /api/upload': 'CFD verisi yükle',
            'POST /api/optimize': 'Test matrisi optimize et',
            'GET /api/download/<file_id>': 'Sonuç dosyasını indir',
            'GET /api/preview/<result_id>': 'Sonuç önizlemesi',
            'POST /api/calculate-pcritical': 'P_critical hesapla'
        },
        'documentation': 'README.md dosyasına bakın'
    })


def cleanup_old_files():
    """1 saatten eski geçici dosyaları sil"""
    import time
    now = time.time()

    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.startswith(('cfd_', 'result_', 'viz_')):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(filepath):
                if now - os.path.getmtime(filepath) > 3600:  # 1 saat
                    try:
                        os.remove(filepath)
                    except:
                        pass


# Uygulama başlangıcında temizlik
cleanup_old_files()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Turbine Test Matrix Optimizer API")
    print("="*60)
    print("API adresi: http://localhost:5000")
    print("Dokümantasyon: http://localhost:5000")
    print("\nEndpoint'ler:")
    print("  - POST /api/upload          : CFD dosyası yükle")
    print("  - POST /api/optimize        : Test matrisi oluştur")
    print("  - GET  /api/download/<id>   : Sonuç indir")
    print("  - POST /api/calculate-pcritical : P_critical hesapla")
    print("="*60 + "\n")

    app.run(debug=True, host='127.0.0.1', port=5000)
