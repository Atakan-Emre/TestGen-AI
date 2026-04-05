import pandas as pd
from datetime import datetime

def test_senaryolari_olustur(dosya_yolu="table_1.csv"):
    try:
        # CSV dosyasını oku
        df = pd.read_csv(dosya_yolu, encoding='utf-8', sep=',', header=1)
        df = df.set_index(df.columns[0])
        
        # Test senaryolarını tutacak liste
        test_senaryolari = []
        
        print("Test senaryoları oluşturuluyor...")
        
        # Her bir alan için test senaryoları oluştur
        for alan_adi, row in df.iterrows():
            try:
                ing_adi = row.get('Alan adı (İng)', '')
                tip = str(row.get('Tip', ''))
                boyut = str(row.get('Boyut', ''))
                zorunluluk = str(row.get('Zorunlu mu?', '')).lower()
                
                # Boyut kontrolü - nan değerleri atla
                if boyut.strip() and 'nan' not in boyut.lower():
                    if 'max' in boyut.lower():
                        boyut = boyut.lower().replace('max', '').strip()
                    test_senaryolari.append(f"{alan_adi} ({ing_adi}) alanı maksimum {boyut} karakterli olmalıdır.")
                
                # Veri tipi kontrolleri
                if 'date' in tip.lower():
                    test_senaryolari.append(f"{alan_adi} ({ing_adi}) alanı geçerli bir tarih formatında olmalıdır.")
                elif 'numeric' in tip.lower():
                    test_senaryolari.append(f"{alan_adi} ({ing_adi}) alanına sadece sayısal değer girilebilir.")
                elif 'string' in tip.lower() or 'alfenumerik' in tip.lower():
                    test_senaryolari.append(f"{alan_adi} ({ing_adi}) alanına sadece metin girişi yapılabilir.")
                
                # Zorunluluk kontrolü
                if 'zorunlu' in zorunluluk:
                    test_senaryolari.append(f"{alan_adi} ({ing_adi}) alanı doldurulması zorunludur.")
                else:
                    test_senaryolari.append(f"{alan_adi} ({ing_adi}) alanı opsiyoneldir.")
                
            except Exception as e:
                print(f"Alan işleme hatası ({alan_adi}): {str(e)}")
        
        # Test senaryolarını dosyaya yaz
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        test_dosyasi = f'test_senaryolari_{timestamp}.txt'
        
        with open(test_dosyasi, 'w', encoding='utf-8') as f:
            for senaryo in test_senaryolari:
                f.write(f"{senaryo}\n")
        
        print(f"\nTest senaryoları '{test_dosyasi}' dosyasına kaydedildi.")
        return test_senaryolari

    except Exception as e:
        print(f"CSV okuma hatası: {str(e)}")
        return None

if __name__ == "__main__":
    try:
        test_senaryolari = test_senaryolari_olustur()
        if test_senaryolari:
            print(f"\nToplam oluşturulan test senaryosu sayısı: {len(test_senaryolari)}")
            
            # Örnek senaryoları göster
            print("\nÖrnek Test Senaryoları:")
            for i, senaryo in enumerate(test_senaryolari[:5], 1):
                print(f"{i}. {senaryo}")
            
    except Exception as e:
        print(f"Hata: {str(e)}")