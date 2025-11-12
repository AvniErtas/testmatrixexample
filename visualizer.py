"""
Test Matrisi Görselleştirme Modülü
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Optional
import numpy as np


class TestMatrixVisualizer:
    """Test matrisi görselleştirme sınıfı"""

    def __init__(self, optimizer):
        """
        Args:
            optimizer: TurbineTestMatrix instance
        """
        self.optimizer = optimizer
        self.config = optimizer.config

    def plot_coverage_map(self, save_path: Optional[str] = None):
        """
        Rake kapsama haritasını görselleştirir.

        Args:
            save_path: Kaydedilecek dosya yolu (None ise göster)
        """
        if self.optimizer.test_points is None:
            raise ValueError("Önce generate_test_matrix() çalıştırın!")

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Veri hazırlık
        data = self.optimizer.data
        test_points = self.optimizer.test_points

        # Vakum kapalı
        self._plot_single_coverage(ax1, data[~data['VacuumRequired']],
                                   test_points[test_points['VacuumRequired'] == 'No'],
                                   'Vakum KAPALI', 'blue')

        # Vakum açık
        self._plot_single_coverage(ax2, data[data['VacuumRequired']],
                                   test_points[test_points['VacuumRequired'] == 'Yes'],
                                   'Vakum AÇIK', 'red')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ Görselleştirme kaydedildi: {save_path}")
        else:
            plt.show()

        plt.close()

    def _plot_single_coverage(self, ax, data_subset, test_subset, title, color):
        """Tek durum için kapsama haritası çizer"""

        # Scatter plot - tüm noktalar
        ax.scatter(data_subset['PressureRatio'], data_subset['Swirl'],
                  c='lightgray', s=30, alpha=0.5, label='CFD Noktaları')

        # Rake pozisyonları
        unique_rakes = test_subset.groupby('RakeAngle').first().reset_index()

        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_rakes)))

        for idx, rake_row in unique_rakes.iterrows():
            rake_angle = rake_row['RakeAngle']
            coverage_min = rake_row['CoverageMin']
            coverage_max = rake_row['CoverageMax']

            # Kapsama bandı
            ax.axhspan(coverage_min, coverage_max, alpha=0.15, color=colors[idx])

            # Rake çizgisi
            ax.axhline(y=rake_angle, color=colors[idx], linestyle='--',
                      linewidth=2, label=f"Rake {idx+1}: {rake_angle:.1f}°")

        ax.set_xlabel('Basınç Oranı (Pressure Ratio)', fontsize=11)
        ax.set_ylabel('Swirl Açısı [derece]', fontsize=11)
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=8)

        # P_critical çizgisi
        if title == 'Vakum KAPALI':
            ax.axvline(x=self.optimizer.p_critical, color='black',
                      linestyle=':', linewidth=2, label=f'P_critical={self.optimizer.p_critical:.3f}')

    def plot_rake_efficiency(self, save_path: Optional[str] = None):
        """
        Her rake'in kapsama verimliliğini görselleştirir.

        Args:
            save_path: Kaydedilecek dosya yolu
        """
        if self.optimizer.test_points is None:
            raise ValueError("Önce generate_test_matrix() çalıştırın!")

        test_points = self.optimizer.test_points

        # Rake başına nokta sayısı
        rake_summary = test_points.groupby(['TestSequence', 'RakeAngle',
                                            'VacuumRequired']).size().reset_index(name='PointCount')

        fig, ax = plt.subplots(figsize=(12, 6))

        # Renkler
        colors = ['blue' if v == 'No' else 'red' for v in rake_summary['VacuumRequired']]

        bars = ax.bar(range(len(rake_summary)), rake_summary['PointCount'], color=colors, alpha=0.7)

        # X ekseni etiketleri
        labels = [f"R{row['TestSequence']}\n{row['RakeAngle']:.1f}°"
                 for _, row in rake_summary.iterrows()]
        ax.set_xticks(range(len(rake_summary)))
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)

        ax.set_xlabel('Rake Pozisyonu', fontsize=11)
        ax.set_ylabel('Kapsanan Nokta Sayısı', fontsize=11)
        ax.set_title('Rake Kapsama Verimliliği', fontsize=13, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        # Legend
        blue_patch = mpatches.Patch(color='blue', alpha=0.7, label='Vakum KAPALI')
        red_patch = mpatches.Patch(color='red', alpha=0.7, label='Vakum AÇIK')
        ax.legend(handles=[blue_patch, red_patch], loc='upper right')

        # Değerleri bar üzerinde göster
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=8)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ Verimlilik grafiği kaydedildi: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_rake_test_plan(self, save_path: Optional[str] = None):
        """
        Her rake pozisyonu için detaylı test planı gösterir.
        Her RPM'de hangi basınç oranlarını tarayacağınızı ayrık ayrık listeler.

        Args:
            save_path: Kaydedilecek dosya yolu
        """
        if self.optimizer.test_points is None:
            raise ValueError("Önce generate_test_matrix() çalıştırın!")

        test_points = self.optimizer.test_points

        # Unique rake pozisyonları
        unique_rakes = test_points.groupby(['TestSequence', 'RakeAngle',
                                            'VacuumRequired']).first().reset_index()

        num_rakes = len(unique_rakes)

        # Her rake için bir sayfa
        fig = plt.figure(figsize=(16, 6 * num_rakes))

        for idx, rake_row in enumerate(unique_rakes.itertuples(), 1):
            rake_angle = rake_row.RakeAngle
            test_seq = rake_row.TestSequence
            vacuum = rake_row.VacuumRequired
            coverage_min = rake_row.CoverageMin
            coverage_max = rake_row.CoverageMax

            # Bu rake'e ait test noktaları
            rake_points = test_points[test_points['TestSequence'] == test_seq].copy()

            # RPM'lere göre grupla
            rpm_groups = rake_points.groupby('RPM')
            unique_rpms = sorted(rake_points['RPM'].unique())
            num_rpms = len(unique_rpms)

            # Subplot oluştur
            ax = plt.subplot(num_rakes, 1, idx)

            # Başlık
            vac_status = "🔴 VAKUM AÇIK" if vacuum == "Yes" else "🟢 VAKUM KAPALI"
            ax.text(0.5, 1.02, f"RAKE #{test_seq}: {rake_angle:.1f}° | {vac_status} | Coverage: [{coverage_min:.1f}° - {coverage_max:.1f}°]",
                   transform=ax.transAxes, fontsize=14, fontweight='bold',
                   ha='center', va='bottom')

            # Y ekseni: RPM değerleri
            y_positions = np.arange(num_rpms)
            ax.set_yticks(y_positions)
            ax.set_yticklabels([f"RPM: {rpm:.0f}" for rpm in unique_rpms], fontsize=11, fontweight='bold')

            # Her RPM için basınç oranlarını göster
            for rpm_idx, rpm_val in enumerate(unique_rpms):
                rpm_data = rpm_groups.get_group(rpm_val).sort_values('PressureRatio')
                prs = rpm_data['PressureRatio'].values
                swirls = rpm_data['Swirl'].values

                # Basınç oranları metni
                pr_text = "  →  PR: "
                for i, (pr, swirl) in enumerate(zip(prs, swirls)):
                    pr_text += f"{pr:.2f}"
                    if i < len(prs) - 1:
                        pr_text += ", "

                # Swirl aralığı
                swirl_range = f"  (Swirl: {swirls.min():.1f}° → {swirls.max():.1f}°)"

                # Metin ekle
                full_text = pr_text + swirl_range
                ax.text(0.02, rpm_idx, full_text,
                       va='center', ha='left', fontsize=10,
                       bbox=dict(boxstyle='round,pad=0.5',
                                facecolor='lightblue' if rpm_idx % 2 == 0 else 'lightyellow',
                                alpha=0.7, edgecolor='gray', linewidth=1.5))

                # Nokta sayısı göster
                count_text = f"[{len(prs)} nokta]"
                ax.text(0.98, rpm_idx, count_text,
                       va='center', ha='right', fontsize=9,
                       fontweight='bold', color='darkred')

            # Eksen ayarları
            ax.set_ylim(-0.5, num_rpms - 0.5)
            ax.set_xlim(0, 1)
            ax.set_xlabel('')
            ax.set_xticks([])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            # Test talimatı ekle
            total_points = len(rake_points)
            instruction = f"📋 TOPLAM {total_points} TEST NOKTASI | Test sırası: RPM sabit → Vana kısarak PR tara → RPM artır → Tekrarla"
            ax.text(0.5, -0.15, instruction,
                   transform=ax.transAxes, fontsize=9, style='italic',
                   ha='center', va='top',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.8))

        # Genel başlık
        fig.suptitle('🔧 RAKE TEST PLANI - Her RPM\'de Taranacak Basınç Oranları',
                    fontsize=18, fontweight='bold', y=0.995)

        plt.tight_layout(rect=[0, 0, 1, 0.99])

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ Rake test planı kaydedildi: {save_path}")
        else:
            plt.show()

        plt.close()

    def generate_report(self, save_path: str = 'test_matrix_report.png'):
        """
        Kombine görselleştirme raporu oluşturur.

        Args:
            save_path: Rapor kayıt yolu
        """
        if self.optimizer.test_points is None:
            raise ValueError("Önce generate_test_matrix() çalıştırın!")

        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

        # 1. Vakum kapalı kapsama
        ax1 = fig.add_subplot(gs[0, :])
        data = self.optimizer.data
        test_points = self.optimizer.test_points
        self._plot_single_coverage(ax1, data[~data['VacuumRequired']],
                                   test_points[test_points['VacuumRequired'] == 'No'],
                                   'Vakum KAPALI - Kapsama Haritası', 'blue')

        # 2. Vakum açık kapsama
        ax2 = fig.add_subplot(gs[1, :])
        self._plot_single_coverage(ax2, data[data['VacuumRequired']],
                                   test_points[test_points['VacuumRequired'] == 'Yes'],
                                   'Vakum AÇIK - Kapsama Haritası', 'red')

        # 3. Rake verimlilik
        ax3 = fig.add_subplot(gs[2, :])
        rake_summary = test_points.groupby(['TestSequence', 'RakeAngle',
                                            'VacuumRequired']).size().reset_index(name='PointCount')
        colors = ['blue' if v == 'No' else 'red' for v in rake_summary['VacuumRequired']]
        bars = ax3.bar(range(len(rake_summary)), rake_summary['PointCount'], color=colors, alpha=0.7)

        labels = [f"R{row['TestSequence']}\n{row['RakeAngle']:.1f}°"
                 for _, row in rake_summary.iterrows()]
        ax3.set_xticks(range(len(rake_summary)))
        ax3.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
        ax3.set_xlabel('Rake Pozisyonu', fontsize=10)
        ax3.set_ylabel('Kapsanan Nokta Sayısı', fontsize=10)
        ax3.set_title('Rake Kapsama Verimliliği', fontsize=11, fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)

        # Değerleri ekle
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom', fontsize=7)

        # Genel başlık
        fig.suptitle('Türbin Test Matrisi - Analiz Raporu',
                    fontsize=16, fontweight='bold', y=0.995)

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Kombine rapor kaydedildi: {save_path}")
        plt.close()


def main():
    """Örnek kullanım"""
    from turbine_test_matrix import TestConfig, TurbineTestMatrix, create_demo_data

    # Konfigürasyon
    config = TestConfig(
        pt_inlet=150.0,
        test_margin=10.0,
        ambient=101.325,
        rake_accuracy=10.0,
        rake_margin_percent=0.10
    )

    # Optimizer
    optimizer = TurbineTestMatrix(config)

    # Demo veri
    demo_data = create_demo_data()
    demo_data.to_excel("demo_cfd_data.xlsx", index=False)
    optimizer.load_cfd_data("demo_cfd_data.xlsx")

    # Test matrisi
    optimizer.generate_test_matrix()

    # Görselleştirme
    visualizer = TestMatrixVisualizer(optimizer)

    print("\nGörselleştirmeler oluşturuluyor...")
    visualizer.plot_coverage_map('coverage_map.png')
    visualizer.plot_rake_efficiency('rake_efficiency.png')
    visualizer.generate_report('full_report.png')

    print("\n✓ Tüm görselleştirmeler tamamlandı!")


if __name__ == "__main__":
    main()
