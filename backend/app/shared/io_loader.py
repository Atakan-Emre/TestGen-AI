"""
I/O işlemleri için yardımcı fonksiyonlar
"""
import json
import re
from pathlib import Path
from typing import Dict, Any, Union
from .logging import get_logger
from .settings import DEFAULT_VARIABLES_PATH, resolve_json_path
from .types import TemplateLoadError, VariablesLoadError, WriteError


logger = get_logger(__name__)


def load_template(json_file_id: Union[str, int]) -> Dict[str, Any]:
    """
    JSON şablonunu yükle
    
    Args:
        json_file_id: JSON dosya ID'si
        
    Returns:
        JSON template verisi
        
    Raises:
        TemplateLoadError: Template yükleme hatası
    """
    try:
        template_path = resolve_json_path(json_file_id)
        
        logger.info(f"Template yükleniyor: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
        
        logger.info(f"Template başarıyla yüklendi: {len(str(template_data))} karakter")
        return template_data
        
    except FileNotFoundError as e:
        error_msg = f"Template dosyası bulunamadı: {e}"
        logger.error(error_msg)
        raise TemplateLoadError(error_msg)
    except json.JSONDecodeError as e:
        error_msg = f"Template JSON parse hatası: {e}"
        logger.error(error_msg)
        raise TemplateLoadError(error_msg)
    except Exception as e:
        error_msg = f"Template yükleme hatası: {e}"
        logger.error(error_msg)
        raise TemplateLoadError(error_msg)


def load_variables(path: Union[str, Path] = None) -> Dict[str, str]:
    """
    Variables dosyasını yükle ve parse et
    
    Args:
        path: Variables dosya yolu (varsayılan: settings'den)
        
    Returns:
        Değişken adı -> değer mapping'i
        
    Raises:
        VariablesLoadError: Variables yükleme hatası
    """
    try:
        variables_path = Path(path) if path else DEFAULT_VARIABLES_PATH
        
        if not variables_path.exists():
            logger.warning(f"Variables dosyası bulunamadı: {variables_path}")
            return {}
        
        logger.info(f"Variables yükleniyor: {variables_path}")
        
        variables = {}
        
        with open(variables_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Boş satırları ve yorumları atla
                if not line or line.startswith('#'):
                    continue
                
                # Çift boşlukları tek boşluğa çevir
                line = re.sub(r'\s+', ' ', line)
                
                # KEY=VALUE formatını parse et
                if '=' not in line:
                    logger.warning(f"Satır {line_num} geçersiz format: {line}")
                    continue
                
                try:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # {{var}} pattern'lerini destekle
                    if '{{' in value and '}}' in value:
                        variables[key] = value
                    else:
                        # Basit değerleri de destekle
                        variables[key] = value
                        
                except ValueError as e:
                    logger.warning(f"Satır {line_num} parse hatası: {line}, Hata: {e}")
                    continue
        
        logger.info(f"Variables başarıyla yüklendi: {len(variables)} değişken")
        return variables
        
    except Exception as e:
        error_msg = f"Variables yükleme hatası: {e}"
        logger.error(error_msg)
        raise VariablesLoadError(error_msg)


def save_text(path: Path, text: str) -> None:
    """
    Metin dosyası kaydet
    
    Args:
        path: Kayıt yolu
        text: Kaydedilecek metin
        
    Raises:
        WriteError: Yazma hatası
    """
    try:
        # Dizini oluştur
        path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Metin dosyası kaydediliyor: {path}")
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"Metin dosyası başarıyla kaydedildi: {path}")
        
    except Exception as e:
        error_msg = f"Metin dosyası yazma hatası: {e}"
        logger.error(error_msg)
        raise WriteError(error_msg)


def save_json(path: Path, data: Dict[str, Any], pretty: bool = True) -> None:
    """
    JSON dosyası kaydet
    
    Args:
        path: Kayıt yolu
        data: Kaydedilecek veri
        pretty: Pretty print kullanılsın mı
        
    Raises:
        WriteError: Yazma hatası
    """
    try:
        # Dizini oluştur
        path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"JSON dosyası kaydediliyor: {path}")
        
        with open(path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
            else:
                json.dump(data, f, ensure_ascii=False)
        
        logger.info(f"JSON dosyası başarıyla kaydedildi: {path}")
        
    except Exception as e:
        error_msg = f"JSON dosyası yazma hatası: {e}"
        logger.error(error_msg)
        raise WriteError(error_msg)
