"""
Test case yazma ve kaydetme işlemleri
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from app.shared.io_loader import save_json
from app.shared.settings import get_output_dir
from app.shared.logging import get_logger
from app.shared.types import WriteError


logger = get_logger(__name__)


def save_test_case(test_name: str, data: Dict[str, Any], 
                  out_dir: Optional[Path] = None) -> Path:
    """
    Test case'i kaydet
    
    Args:
        test_name: Test adı
        data: Kaydedilecek test verisi
        out_dir: Çıktı dizini (opsiyonel)
        
    Returns:
        Kaydedilen dosyanın yolu
        
    Raises:
        WriteError: Yazma hatası
    """
    try:
        # Çıktı dizinini belirle
        if out_dir is None:
            out_dir = get_output_dir(test_name, "bsc")
        
        # Güvenli dosya adı oluştur
        safe_filename = _create_safe_filename(test_name)
        
        # Timestamp ekle
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"bsc_test_{timestamp}_{safe_filename}.json"
        
        # Tam dosya yolu
        file_path = out_dir / filename
        
        logger.info(f"Test case kaydediliyor: {file_path}")
        
        # JSON'u kaydet
        save_json(file_path, data, pretty=True)
        
        logger.info(f"Test case başarıyla kaydedildi: {file_path}")
        return file_path
        
    except Exception as e:
        error_msg = f"Test case kaydetme hatası: {e}"
        logger.error(error_msg)
        raise WriteError(error_msg)


def save_dynamic_test_case(test_name: str, data: Dict[str, Any], 
                          generator_type: str = "dynamic",
                          out_dir: Optional[Path] = None) -> Path:
    """
    Dinamik test case'i kaydet
    
    Args:
        test_name: Test adı
        data: Kaydedilecek test verisi
        generator_type: Generator tipi
        out_dir: Çıktı dizini (opsiyonel)
        
    Returns:
        Kaydedilen dosyanın yolu
        
    Raises:
        WriteError: Yazma hatası
    """
    try:
        # Çıktı dizinini belirle
        if out_dir is None:
            out_dir = get_output_dir(test_name, generator_type)
        
        # Güvenli dosya adı oluştur
        safe_filename = _create_safe_filename(test_name)
        
        # Timestamp ekle
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{generator_type}_test_{timestamp}_{safe_filename}.json"
        
        # Tam dosya yolu
        file_path = out_dir / filename
        
        logger.info(f"Dinamik test case kaydediliyor: {file_path}")
        
        # JSON'u kaydet
        save_json(file_path, data, pretty=True)
        
        logger.info(f"Dinamik test case başarıyla kaydedildi: {file_path}")
        return file_path
        
    except Exception as e:
        error_msg = f"Dinamik test case kaydetme hatası: {e}"
        logger.error(error_msg)
        raise WriteError(error_msg)


def _create_safe_filename(test_name: str) -> str:
    """
    Güvenli dosya adı oluştur
    
    Args:
        test_name: Orijinal test adı
        
    Returns:
        Güvenli dosya adı
    """
    # Türkçe karakterleri normalize et
    turkish_chars = {
        'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
        'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
    }
    
    safe_name = test_name
    for tr_char, en_char in turkish_chars.items():
        safe_name = safe_name.replace(tr_char, en_char)
    
    # Özel karakterleri temizle ve underscore ile değiştir
    safe_name = re.sub(r'[^\w\-_]', '_', safe_name)
    
    # Çoklu underscore'leri tek underscore yap
    safe_name = re.sub(r'_+', '_', safe_name)
    
    # Başında ve sonunda underscore varsa kaldır
    safe_name = safe_name.strip('_')
    
    # Boşsa varsayılan ad ver
    if not safe_name:
        safe_name = "test"
    
    # Uzunluk sınırı (50 karakter)
    if len(safe_name) > 50:
        safe_name = safe_name[:50]
    
    return safe_name.lower()


def create_test_case_metadata(test_name: str, scenario_type: str = "BSC",
                            description: str = None) -> Dict[str, Any]:
    """
    Test case metadata'sı oluştur
    
    Args:
        test_name: Test adı
        scenario_type: Senaryo tipi
        description: Açıklama
        
    Returns:
        Metadata dictionary'si
    """
    if description is None:
        description = f"{scenario_type} test senaryosu - {test_name}"
    
    return {
        "scenario_type": scenario_type,
        "description": description,
        "test_name": test_name,
        "created_at": datetime.now().isoformat(),
        "expected_result": "SUCCESS",
        "version": "1.0"
    }


def add_file_path_to_test_case(test_case: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
    """
    Test case'e dosya yolunu ekle
    
    Args:
        test_case: Test case verisi
        file_path: Dosya yolu
        
    Returns:
        Güncellenmiş test case
    """
    test_case["file_path"] = str(file_path)
    test_case["file_name"] = file_path.name
    return test_case
