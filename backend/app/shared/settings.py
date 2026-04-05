"""
Uygulama ayarları ve konfigürasyon
"""
import os
from pathlib import Path
from typing import Dict, Any


# Temel yollar
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = Path(os.getenv("DATA_ROOT", "/app/data"))
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

# Varsayılan yollar
OUTPUT_PATH = OUTPUT_DIR / "test_cases"
DEFAULT_VARIABLES_PATH = INPUT_DIR / "Variables" / "variables.txt"
JSON_TEMPLATES_PATH = INPUT_DIR / "Json"

# Model ayarları
EMB_MODEL_NAME = os.getenv("EMB_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
MATCH_WEIGHTS = {
    "semantic": float(os.getenv("SEMANTIC_WEIGHT", "0.7")),
    "rules": float(os.getenv("RULES_WEIGHT", "0.3"))
}

# RL ayarları
USE_RL = os.getenv("USE_RL", "false").lower() == "true"
RL_MODELS_PATH = BASE_DIR / "models"

# Logging ayarları
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Test ayarları
TEST_SEED = int(os.getenv("TEST_SEED", "42"))


def resolve_json_path(json_file_id: str) -> Path:
    """
    JSON dosya ID'sini gerçek dosya yoluna çevir
    
    Args:
        json_file_id: JSON dosya ID'si (string veya int)
        
    Returns:
        JSON dosyasının tam yolu
    """
    try:
        # ID'yi int'e çevir
        if isinstance(json_file_id, str):
            file_id = int(json_file_id)
        else:
            file_id = json_file_id
            
        # Veritabanından dosya adını al
        from app.database import get_db
        from app.models.json_file import JsonFile
        
        db = next(get_db())
        json_file = db.query(JsonFile).filter(JsonFile.id == file_id).first()
        
        if json_file:
            file_path = JSON_TEMPLATES_PATH / json_file.name
            if file_path.exists():
                return file_path
        
        # Fallback: alfabetik sıralama (eski yöntem)
        json_files = [f for f in JSON_TEMPLATES_PATH.iterdir() if f.suffix == '.json']
        json_files.sort()
        
        if not json_files:
            raise FileNotFoundError(f"JSON şablonu bulunamadı: {JSON_TEMPLATES_PATH}")
        
        # ID'ye göre dosya seç (1-based indexing)
        if 0 < file_id <= len(json_files):
            return json_files[file_id - 1]
        else:
            return json_files[0]  # Varsayılan olarak ilk dosya
            
    except (ValueError, FileNotFoundError) as e:
        from .types import TemplateLoadError
        raise TemplateLoadError(f"JSON dosyası çözümlenemedi: {json_file_id}, Hata: {e}")


def get_output_dir(test_name: str, generator_type: str = "bsc") -> Path:
    """
    Test çıktısı için dizin oluştur
    
    Args:
        test_name: Test adı
        generator_type: Generator tipi (bsc, ngi, ngv, vb.)
        
    Returns:
        Çıktı dizini yolu
    """
    output_dir = OUTPUT_PATH / test_name / generator_type
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


# Konfigürasyon validasyonu
def validate_settings() -> None:
    """Ayarları doğrula"""
    required_dirs = [INPUT_DIR, JSON_TEMPLATES_PATH]
    for dir_path in required_dirs:
        if not dir_path.exists():
            raise FileNotFoundError(f"Gerekli dizin bulunamadı: {dir_path}")
    
    # Match weights toplamı 1.0 olmalı
    total_weight = MATCH_WEIGHTS["semantic"] + MATCH_WEIGHTS["rules"]
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(f"Match weights toplamı 1.0 olmalı, mevcut: {total_weight}")


# Uygulama başlangıcında ayarları doğrula
try:
    validate_settings()
except (FileNotFoundError, ValueError) as e:
    import logging
    logging.warning(f"Ayar doğrulama uyarısı: {e}")
