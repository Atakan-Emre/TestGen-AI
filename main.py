from src.generators.bsc_generator import BSCGenerator
from src.generators.opt_generator import OPTGenerator
from src.generators.ngi_generator import NGIGenerator
from src.generators.ngv_generator import NGVGenerator
from src.generators.bert_ner_generator import BertNerGenerator
from src.config.settings import INPUT_PATH, OUTPUT_PATH
import os
import json

def print_menu():
    """Ana menüyü göster"""
    print("\n=== TestGen AI CLI ===")
    print("1. Genel Test Senaryoları Oluştur (BERT-NER)")
    print("2. BSC (Zorunlu Alan) Test Senaryosu Oluştur")
    print("3. OPT (Opsiyonel Alan) Test Senaryosu Oluştur")
    print("4. NGI (Negatif/Geçersiz) Test Senaryosu Oluştur")
    print("5. NGV (Negatif/Tekil) Test Senaryosu Oluştur")
    print("6. Çıkış")
    print("========================")

def create_bert_test():
    """BERT-NER test senaryoları oluştur"""
    try:
        generator = BertNerGenerator()
        input_file = os.path.join(INPUT_PATH, "table_1.csv")
        test_scenarios = generator.generate_test_scenarios(input_file)
        
        if test_scenarios:
            print(f"\nToplam {len(test_scenarios)} adet test senaryosu oluşturuldu")
            print("\nÖrnek Test Senaryoları:")
            for i, senaryo in enumerate(test_scenarios[:5], 1):
                print(f"{i}. {senaryo}")
        return test_scenarios
    except Exception as e:
        print(f"BERT-NER test oluşturma hatası: {str(e)}")
        return None

def get_latest_test_scenario_file():
    """En son oluşturulan test senaryo dosyasını bul"""
    try:
        scenario_dir = os.path.join(OUTPUT_PATH, "test_scenarios")
        files = [f for f in os.listdir(scenario_dir) if f.startswith("test_senaryolari_")]
        if not files:
            raise FileNotFoundError("Test senaryo dosyası bulunamadı!")
            
        # Dosyaları tarihe göre sırala ve en sonuncuyu al
        latest_file = max(files)
        return os.path.join(scenario_dir, latest_file)
        
    except Exception as e:
        print(f"Test senaryo dosyası bulma hatası: {str(e)}")
        return None

def create_bsc_test():
    """BSC test senaryosu oluştur"""
    try:
        generator = BSCGenerator()
        input_file = get_latest_test_scenario_file()
        if not input_file:
            return None
            
        test_case = generator.generate_bsc_test(input_file)
        print("\nBSC test senaryosu başarıyla oluşturuldu!")
        return test_case
    except Exception as e:
        print(f"BSC test oluşturma hatası: {str(e)}")
        return None

def create_opt_test():
    """OPT test senaryosu oluştur"""
    try:
        generator = OPTGenerator()
        input_file = get_latest_test_scenario_file()
        if not input_file:
            return None
            
        test_cases = generator.generate_opt_tests(input_file)
        print("\nOPT test senaryoları başarıyla oluşturuldu!")
        return test_cases
    except Exception as e:
        print(f"OPT test oluşturma hatası: {str(e)}")
        return None

def create_ngi_test():
    """NGI test senaryosu oluştur"""
    try:
        generator = NGIGenerator()
        input_file = get_latest_test_scenario_file()
        if not input_file:
            return None
            
        test_cases = generator.generate_ngi_tests(input_file)
        print("\nNGI test senaryoları başarıyla oluşturuldu!")
        return test_cases
    except Exception as e:
        print(f"NGI test oluşturma hatası: {str(e)}")
        return None

def create_ngv_test():
    """NGV test senaryosu oluştur"""
    try:
        generator = NGVGenerator()
        input_file = get_latest_test_scenario_file()
        if not input_file:
            return None
            
        test_cases = generator.generate_ngv_tests(input_file)
        print("\nNGV test senaryoları başarıyla oluşturuldu!")
        return test_cases
    except Exception as e:
        print(f"NGV test oluşturma hatası: {str(e)}")
        return None

def main():
    while True:
        try:
            print_menu()
            choice = input("Seçiminiz (1-6): ")

            if choice == "1":
                test_scenarios = create_bert_test()
                if test_scenarios:
                    print("\nTest senaryoları başarıyla oluşturuldu ve kaydedildi.")
                input("\nDevam etmek için Enter'a basın...")

            elif choice == "2":
                test_case = create_bsc_test()
                if test_case:
                    print("\nOluşturulan BSC test case:")
                    print(json.dumps(test_case, indent=2, ensure_ascii=False))
                input("\nDevam etmek için Enter'a basın...")

            elif choice == "3":
                test_cases = create_opt_test()
                if test_cases:
                    print(f"\nToplam {len(test_cases)} adet OPT test senaryosu oluşturuldu")
                    print("Test senaryoları 'data/output/test_cases/opt' klasörüne kaydedildi")
                input("\nDevam etmek için Enter'a basın...")

            elif choice == "4":
                test_cases = create_ngi_test()
                if test_cases:
                    print(f"\nToplam {len(test_cases)} adet NGI test senaryosu oluşturuldu")
                    print("Test senaryoları 'data/output/test_cases/ngi' klasörüne kaydedildi")
                input("\nDevam etmek için Enter'a basın...")

            elif choice == "5":
                test_cases = create_ngv_test()
                if test_cases:
                    print(f"\nToplam {len(test_cases)} adet NGV test senaryosu oluşturuldu")
                    print("Test senaryoları 'data/output/test_cases/ngv' klasörüne kaydedildi")
                input("\nDevam etmek için Enter'a basın...")

            elif choice == "6":
                print("\nProgram sonlandırılıyor...")
                break

            else:
                print("\nGeçersiz seçim! Lütfen 1-6 arasında bir sayı girin.")

        except Exception as e:
            print(f"\nBeklenmeyen hata: {str(e)}")
            input("\nDevam etmek için Enter'a basın...")

if __name__ == "__main__":
    main() 
