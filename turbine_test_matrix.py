"""
Turbine Test Matrix Optimizer
Bu modül türbin rig test matrisi oluşturmak için kullanılır.
CFD analiz verilerinden optimal rake pozisyonlarını belirler.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')


@dataclass
class TestConfig:
    """Test konfigürasyon parametreleri"""
    pt_inlet: float  # Giriş toplam basıncı [kPa]
    test_margin: float  # Test güvenlik marjini [kPa]
    ambient: float  # Ortam basıncı [kPa], default 101.325 kPa
    rake_accuracy: float  # Rake açısal doğruluk [derece], default ±10°
    rake_margin_percent: float  # Ek güvenlik marjini [%], default 0.1 (10%)
    rake_min: float = -89.0  # Rake minimum açı [derece]
    rake_max: float = 89.0  # Rake maximum açı [derece]

    def calculate_p_critical(self) -> float:
        """
        Kritik basınç oranını hesaplar.
        Bu değerin ÜZERİNDE vakum pompası devreye girer.

        Returns:
            float: Kritik basınç oranı (p_critical)
        """
        p_critical = (self.pt_inlet - self.test_margin) / self.ambient
        return p_critical


class TurbineTestMatrix:
    """Türbin test matrisi optimizasyon sınıfı"""

    def __init__(self, config: TestConfig):
        """
        Args:
            config: Test konfigürasyon parametreleri
        """
        self.config = config
        self.p_critical = config.calculate_p_critical()
        self.data: Optional[pd.DataFrame] = None
        self.test_points: Optional[pd.DataFrame] = None

    def load_cfd_data(self, excel_path: str, sheet_name: str = 'Sheet1') -> pd.DataFrame:
        """
        CFD analiz verilerini Excel'den yükler.

        Args:
            excel_path: Excel dosya yolu
            sheet_name: Excel sheet adı

        Returns:
            pd.DataFrame: Yüklenen veri

        Expected columns: 'RPM', 'PressureRatio', 'Swirl'
        """
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)

            # Sütun kontrolü
            required_cols = ['RPM', 'PressureRatio', 'Swirl']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                raise ValueError(f"Eksik sütunlar: {missing_cols}")

            # Veri temizleme
            df = df.dropna(subset=required_cols)

            # Vakum durumu sütunu ekle
            df['VacuumRequired'] = df['PressureRatio'] > self.p_critical

            self.data = df
            print(f"✓ {len(df)} satır veri yüklendi")
            print(f"✓ P_critical = {self.p_critical:.3f}")
            print(f"✓ Vakum gerektiren noktalar: {df['VacuumRequired'].sum()}")
            print(f"✓ Vakum gerektirmeyen noktalar: {(~df['VacuumRequired']).sum()}")

            return df

        except Exception as e:
            raise Exception(f"Veri yükleme hatası: {str(e)}")

    def calculate_rake_coverage(self, rake_angle: float) -> Tuple[float, float]:
        """
        Verilen rake açısının kapsama aralığını hesaplar.

        Args:
            rake_angle: Rake set açısı [derece]

        Returns:
            Tuple[float, float]: (min_coverage, max_coverage) [derece]
        """
        # Temel accuracy
        base_accuracy = self.config.rake_accuracy

        # Margin ekle
        margin = base_accuracy * self.config.rake_margin_percent
        effective_accuracy = base_accuracy + margin

        # Kapsama aralığı
        min_coverage = max(rake_angle - effective_accuracy, self.config.rake_min)
        max_coverage = min(rake_angle + effective_accuracy, self.config.rake_max)

        return min_coverage, max_coverage

    def get_covered_points(self, rake_angle: float,
                          data_subset: pd.DataFrame) -> pd.DataFrame:
        """
        Verilen rake açısının kapsadığı test noktalarını döndürür.

        Args:
            rake_angle: Rake set açısı [derece]
            data_subset: Kontrol edilecek veri alt kümesi

        Returns:
            pd.DataFrame: Kapsanan test noktaları
        """
        min_cov, max_cov = self.calculate_rake_coverage(rake_angle)

        covered = data_subset[
            (data_subset['Swirl'] >= min_cov) &
            (data_subset['Swirl'] <= max_cov)
        ]

        return covered

    def optimize_rake_positions(self, vacuum_state: bool) -> List[Dict]:
        """
        Greedy set cover algoritması ile optimal rake pozisyonlarını bulur.

        Args:
            vacuum_state: True=vakum açık, False=vakum kapalı

        Returns:
            List[Dict]: Optimal rake pozisyonları ve kapsadıkları noktalar
        """
        if self.data is None:
            raise ValueError("Önce load_cfd_data() ile veri yükleyin!")

        # İlgili veri alt kümesini al
        subset = self.data[self.data['VacuumRequired'] == vacuum_state].copy()

        if len(subset) == 0:
            return []

        uncovered = subset.copy()
        rake_positions = []

        # Swirl değer aralığı
        swirl_min = subset['Swirl'].min()
        swirl_max = subset['Swirl'].max()

        print(f"\n{'='*60}")
        print(f"Optimizasyon: Vakum {'AÇIK' if vacuum_state else 'KAPALI'}")
        print(f"Toplam test noktası: {len(subset)}")
        print(f"Swirl aralığı: [{swirl_min:.1f}°, {swirl_max:.1f}°]")
        print(f"{'='*60}")

        iteration = 0
        max_iterations = 200  # Sonsuz döngü koruması

        while len(uncovered) > 0 and iteration < max_iterations:
            iteration += 1

            # Olası rake açıları (daha yoğun örnekleme)
            # Kapsanmamış noktaların etrafında yoğunlaşır
            candidate_angles = np.linspace(
                max(swirl_min - self.config.rake_accuracy, self.config.rake_min),
                min(swirl_max + self.config.rake_accuracy, self.config.rake_max),
                num=180  # 1 derece çözünürlük
            )

            # Ayrıca kapsanmamış noktaların tam üzerinde de dene
            uncovered_swirls = uncovered['Swirl'].unique()
            candidate_angles = np.concatenate([candidate_angles, uncovered_swirls])
            candidate_angles = np.unique(candidate_angles)

            best_rake = None
            best_coverage_count = 0
            best_covered_df = None

            # Her aday açı için kapsama sayısını hesapla
            for angle in candidate_angles:
                covered_df = self.get_covered_points(angle, uncovered)
                coverage_count = len(covered_df)

                if coverage_count > best_coverage_count:
                    best_coverage_count = coverage_count
                    best_rake = angle
                    best_covered_df = covered_df

            # Eğer hiçbir şey kapsamıyorsa (olmaması gereken durum)
            if best_rake is None or best_coverage_count == 0:
                print(f"⚠ Uyarı: Kapsanamayan noktalar kaldı: {len(uncovered)}")
                break

            # En iyi rake'i kaydet
            min_cov, max_cov = self.calculate_rake_coverage(best_rake)

            rake_info = {
                'rake_angle': round(best_rake, 2),
                'coverage_min': round(min_cov, 2),
                'coverage_max': round(max_cov, 2),
                'points_covered': best_coverage_count,
                'vacuum_required': vacuum_state,
                'covered_data': best_covered_df
            }

            rake_positions.append(rake_info)

            # Kapsanan noktaları çıkar
            uncovered = uncovered[~uncovered.index.isin(best_covered_df.index)]

            print(f"Rake #{len(rake_positions)}: {best_rake:.1f}° "
                  f"[{min_cov:.1f}° - {max_cov:.1f}°] → "
                  f"{best_coverage_count} nokta | "
                  f"Kalan: {len(uncovered)}")

        print(f"{'='*60}")
        print(f"✓ Toplam {len(rake_positions)} rake pozisyonu bulundu")
        print(f"{'='*60}\n")

        return rake_positions

    def generate_test_matrix(self) -> pd.DataFrame:
        """
        Tam test matrisini oluşturur (vakum açık ve kapalı durumlar).

        Returns:
            pd.DataFrame: Test matrisi
        """
        # Vakum kapalı optimizasyonu
        rake_no_vacuum = self.optimize_rake_positions(vacuum_state=False)

        # Vakum açık optimizasyonu
        rake_with_vacuum = self.optimize_rake_positions(vacuum_state=True)

        # Sonuçları birleştir
        all_rakes = rake_no_vacuum + rake_with_vacuum

        # DataFrame oluştur
        matrix_data = []

        for idx, rake in enumerate(all_rakes, start=1):
            covered_df = rake['covered_data']

            for _, point in covered_df.iterrows():
                matrix_data.append({
                    'TestSequence': idx,
                    'RakeAngle': rake['rake_angle'],
                    'CoverageMin': rake['coverage_min'],
                    'CoverageMax': rake['coverage_max'],
                    'VacuumRequired': 'Yes' if rake['vacuum_required'] else 'No',
                    'RPM': point['RPM'],
                    'PressureRatio': round(point['PressureRatio'], 4),
                    'Swirl': round(point['Swirl'], 2),
                })

        self.test_points = pd.DataFrame(matrix_data)

        # Özet rapor
        print("\n" + "="*60)
        print("TEST MATRİSİ ÖZETİ")
        print("="*60)
        print(f"Toplam rake pozisyonu: {len(all_rakes)}")
        print(f"  - Vakum kapalı: {len(rake_no_vacuum)} rake")
        print(f"  - Vakum açık: {len(rake_with_vacuum)} rake")
        print(f"\nToplam test noktası: {len(self.test_points)}")
        print(f"P_critical: {self.p_critical:.3f}")
        print("="*60 + "\n")

        return self.test_points

    def export_to_excel(self, output_path: str):
        """
        Test matrisini Excel'e kaydeder.

        Args:
            output_path: Çıktı Excel dosya yolu
        """
        if self.test_points is None:
            raise ValueError("Önce generate_test_matrix() çalıştırın!")

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Ana test matrisi
            self.test_points.to_excel(writer, sheet_name='TestMatrix', index=False)

            # Rake özet
            rake_summary = self.test_points.groupby(['TestSequence', 'RakeAngle',
                                                     'VacuumRequired']).size().reset_index(name='PointCount')
            rake_summary.to_excel(writer, sheet_name='RakeSummary', index=False)

            # Konfigürasyon
            config_data = {
                'Parameter': ['pt_inlet [kPa]', 'test_margin [kPa]',
                             'ambient [kPa]', 'P_critical',
                             'rake_accuracy [deg]', 'rake_margin [%]',
                             'rake_min [deg]', 'rake_max [deg]'],
                'Value': [self.config.pt_inlet, self.config.test_margin,
                         self.config.ambient, round(self.p_critical, 4),
                         self.config.rake_accuracy,
                         self.config.rake_margin_percent * 100,
                         self.config.rake_min, self.config.rake_max]
            }
            pd.DataFrame(config_data).to_excel(writer, sheet_name='Config', index=False)

        print(f"✓ Test matrisi kaydedildi: {output_path}")


def main():
    """Örnek kullanım"""

    # Konfigürasyon
    config = TestConfig(
        pt_inlet=150.0,      # [kPa] - Tasarımcıdan alınacak
        test_margin=10.0,    # [kPa] - Güvenlik marjini
        ambient=101.325,     # [kPa] - Standart atmosfer basıncı
        rake_accuracy=10.0,  # [derece] - ±10° rake doğruluğu
        rake_margin_percent=0.10  # 10% ek güvenlik marjini
    )

    # Optimizer oluştur
    optimizer = TurbineTestMatrix(config)

    # CFD verilerini yükle
    # NOT: Excel dosyanızın yolunu buraya girin
    cfd_data_path = "cfd_data.xlsx"  # BURAYA DOSYA YOLUNU GİRİN

    try:
        optimizer.load_cfd_data(cfd_data_path)

        # Test matrisini oluştur
        test_matrix = optimizer.generate_test_matrix()

        # Excel'e kaydet
        optimizer.export_to_excel("turbine_test_matrix_output.xlsx")

        # Ekranda göster (ilk 20 satır)
        print("\nİlk 20 test noktası:")
        print(test_matrix.head(20).to_string(index=False))

    except Exception as e:
        if "No such file or directory" in str(e):
            print(f"\n⚠ HATA: '{cfd_data_path}' dosyası bulunamadı!")
            print("Lütfen Excel dosyanızın yolunu güncelleyin.\n")

            # Demo veri oluştur
            print("Demo veri ile örnek çalıştırılıyor...\n")
            demo_data = create_demo_data()
            demo_data.to_excel("demo_cfd_data.xlsx", index=False)

            optimizer.load_cfd_data("demo_cfd_data.xlsx")
            test_matrix = optimizer.generate_test_matrix()
            optimizer.export_to_excel("turbine_test_matrix_output.xlsx")
        else:
            raise


def create_demo_data() -> pd.DataFrame:
    """Demo CFD verisi oluşturur"""
    np.random.seed(42)

    rpm_values = np.arange(50, 145, 5)  # %50 - %140, %5 artış
    pr_values = np.linspace(1.2, 2.5, 15)  # Basınç oranı

    data = []
    for rpm in rpm_values:
        for pr in pr_values:
            # Swirl değeri RPM ve PR'ye göre değişiyor (örnek)
            swirl = -60 + (rpm - 50) * 1.2 + (pr - 1.2) * 25 + np.random.normal(0, 5)
            swirl = np.clip(swirl, -89, 89)

            data.append({
                'RPM': rpm,
                'PressureRatio': round(pr, 3),
                'Swirl': round(swirl, 2)
            })

    return pd.DataFrame(data)


if __name__ == "__main__":
    main()
