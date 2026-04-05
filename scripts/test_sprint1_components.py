#!/usr/bin/env python3
"""
Sprint 1 Bileşenleri Test Script'i
CSV Preprocessor + Heuristic Labeler ile gerçek CSV işleme
"""
import sys
import pandas as pd
from pathlib import Path

# Backend path'i ekle
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.csv_preprocessor import CsvPreprocessor
from app.services.heuristic_labeler import HeuristicLabeler


def test_with_real_csv():
    """Gerçek CSV dosyası ile test"""
    print("=" * 80)
    print("Sprint 1 Bileşenleri Test")
    print("=" * 80)
    print()
    
    # CSV dosya yolu
    csv_file = Path(__file__).parent.parent / "data/input/Csv/5.1.1-alacak-cekleri-giris-bordrosu.csv"
    
    if not csv_file.exists():
        print(f"❌ CSV dosyası bulunamadı: {csv_file}")
        return
    
    print(f"📁 CSV dosyası: {csv_file.name}")
    print()
    
    # 1. CSV Preprocessor
    print("🔧 Step 1: CSV Preprocessor")
    print("-" * 40)
    
    preprocessor = CsvPreprocessor()
    
    try:
        # CSV oku - auto_detect_headers ile
        # Artık preprocessor otomatik olarak header'ları tespit ediyor
        snippets = preprocessor.process_csv_file(
            str(csv_file),
            skip_header_rows=2,  # İlk 2 satır başlık değil
            auto_detect_headers=True
        )
        
        print(f"✅ {len(snippets)} alan işlendi")
        print()
        
        # İstatistikler
        stats = preprocessor.get_statistics(snippets)
        print("📊 İstatistikler:")
        print(f"   - Toplam alan: {stats['total_fields']}")
        print(f"   - Zorunlu alan: {stats['required_fields']}")
        print(f"   - Opsiyonel alan: {stats['optional_fields']}")
        print(f"   - Tekil alan: {stats['unique_fields']}")
        print(f"   - Ortalama max_length: {stats['avg_max_length']:.1f}")
        print()
        print("   Tip dağılımı:")
        for field_type, count in stats['type_distribution'].items():
            print(f"      • {field_type}: {count}")
        print()
        
        # İlk 3 alan örneği
        print("📝 İlk 3 alan örneği:")
        for i, snippet in enumerate(snippets[:3], 1):
            print(f"\n   {i}. {snippet['field_name']}")
            print(f"      Tip: {snippet.get('field_type', 'N/A')}")
            print(f"      Zorunlu: {'Evet' if snippet.get('is_required') else 'Hayır'}")
            print(f"      Max Length: {snippet.get('max_length', 'N/A')}")
            print(f"      Constraints: {', '.join(snippet.get('constraints', []))}")
        
        print("\n" + "=" * 80)
        
        # 2. Heuristic Labeler
        print("\n🏷️  Step 2: Heuristic Labeler")
        print("-" * 40)
        
        labeler = HeuristicLabeler()
        labeled = labeler.batch_label(snippets)
        
        print(f"✅ {len(labeled)} alan etiketlendi")
        print()
        
        # İstatistikler
        label_stats = labeler.get_statistics(labeled)
        print("📊 Etiketleme İstatistikleri:")
        print(f"   - Toplam alan: {label_stats['total_fields']}")
        print(f"   - Toplam edge case: {label_stats['total_edge_cases']}")
        print()
        print("   Variant dağılımı:")
        for variant, count in label_stats['variant_distribution'].items():
            print(f"      • {variant}: {count}")
        print()
        print("   Edge case tipleri:")
        for variant, count in label_stats['edge_case_types'].items():
            print(f"      • {variant}: {count}")
        print()
        
        # İlk alan detaylı örnek
        print("📋 Detaylı Örnek: İlk Alan")
        print("-" * 40)
        first_field = labeled[0]
        print(f"Alan Adı: {first_field['field_name']}")
        print(f"Primary Variant: {first_field['primary_variant']}")
        print(f"Tip: {first_field.get('field_type', 'N/A')}")
        print(f"Zorunlu: {'Evet' if first_field.get('is_required') else 'Hayır'}")
        print()
        print(f"Edge Case'ler ({len(first_field['edge_cases'])} adet):")
        for i, edge_case in enumerate(first_field['edge_cases'], 1):
            print(f"\n   {i}. [{edge_case['variant'].upper()}]")
            print(f"      Aksiyon: {edge_case['action']}")
            print(f"      Beklenen: {edge_case['expected_outcome']}")
        
        print("\n" + "=" * 80)
        
        # 3. Export örneği
        print("\n📄 Export Örneği (İlk 2 Alan)")
        print("-" * 40)
        
        export_text = labeler.export_test_scenarios(labeled[:2], format="text")
        print(export_text)
        
        print("=" * 80)
        print("✅ Test başarıyla tamamlandı!")
        print()
        print("🎯 Sonraki Adımlar:")
        print("   1. Pydantic şemalarını tanımla")
        print("   2. LLM adapter oluştur")
        print("   3. Pipeline entegrasyonu yap")
        print()
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    test_with_real_csv()
