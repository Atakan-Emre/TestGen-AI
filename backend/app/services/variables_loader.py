import os
import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Literal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class VariablesLoader:
    """Variables profillerini yükleyen ve yöneten servis"""
    
    def __init__(self, variables_dir: str = "/app/data/input/Variables"):
        self.variables_dir = Path(variables_dir)
        self.variables_dir.mkdir(parents=True, exist_ok=True)
        
        # Desteklenen formatlar
        self.supported_formats = {'.txt', '.json', '.yaml', '.yml'}
        
        # Anahtar doğrulama regex'i
        self.key_pattern = re.compile(r'^[A-Za-z0-9_.\-\[\]]+$')
    
    def list_profiles(self) -> List[Dict[str, any]]:
        """Mevcut variables profillerini listeler"""
        try:
            profiles = []
            
            if not self.variables_dir.exists():
                return profiles
                
            for file_path in self.variables_dir.iterdir():
                if file_path.is_file() and file_path.suffix in self.supported_formats:
                    stat = file_path.stat()
                    profiles.append({
                        'name': file_path.stem,  # uzantısız isim
                        'format': self._get_format_from_extension(file_path.suffix),
                        'size_bytes': stat.st_size,
                        'updated_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            return sorted(profiles, key=lambda x: x['name'])
            
        except Exception as e:
            logger.error(f"Profil listesi alınırken hata: {str(e)}")
            return []
    
    def load_profile(self, name: str) -> Dict[str, str]:
        """Belirtilen profili yükler ve düzleştirilmiş sözlük döner"""
        try:
            file_path = self._find_profile_file(name)
            if not file_path:
                raise FileNotFoundError(f"Profil bulunamadı: {name}")
            
            format_type = self._get_format_from_extension(file_path.suffix)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                if format_type == 'txt':
                    return self._parse_txt(f.read())
                elif format_type == 'json':
                    return self._parse_json(f.read())
                elif format_type in ['yaml', 'yml']:
                    return self._parse_yaml(f.read())
                else:
                    raise ValueError(f"Desteklenmeyen format: {format_type}")
                    
        except Exception as e:
            logger.error(f"Profil yüklenirken hata ({name}): {str(e)}")
            raise

    def resolve_profile_path(self, name: str) -> Optional[Path]:
        """Profil adına karşılık gelen gerçek dosya yolunu döner"""
        return self._find_profile_file(name)
    
    def save_profile(self, name: str, content: bytes, format_type: str) -> str:
        """Yeni profil kaydeder"""
        try:
            # Dosya adı güvenlik kontrolü
            if not self._is_valid_filename(name):
                raise ValueError("Geçersiz dosya adı")
            
            # Format kontrolü
            if format_type not in ['txt', 'json', 'yaml']:
                raise ValueError("Desteklenmeyen format")
            
            file_path = self.variables_dir / f"{name}.{format_type}"
            
            # Dosya zaten varsa kontrol et
            if file_path.exists():
                raise FileExistsError(f"Profil zaten mevcut: {name}")
            
            # İçeriği doğrula
            content_str = content.decode('utf-8')
            if format_type == 'txt':
                self._parse_txt(content_str)
            elif format_type == 'json':
                self._parse_json(content_str)
            elif format_type in ['yaml', 'yml']:
                self._parse_yaml(content_str)
            
            # Dosyayı kaydet
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content_str)
            
            logger.info(f"Profil kaydedildi: {name}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Profil kaydedilirken hata ({name}): {str(e)}")
            raise
    
    def delete_profile(self, name: str) -> bool:
        """Profil dosyasını siler"""
        try:
            file_path = self._find_profile_file(name)
            if not file_path:
                return False
            
            file_path.unlink()
            logger.info(f"Profil silindi: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Profil silinirken hata ({name}): {str(e)}")
            return False
    
    def _find_profile_file(self, name: str) -> Optional[Path]:
        """Profil dosyasını bulur (uzantı fark etmez)"""
        for ext in self.supported_formats:
            file_path = self.variables_dir / f"{name}{ext}"
            if file_path.exists():
                return file_path
        return None
    
    def _get_format_from_extension(self, extension: str) -> str:
        """Dosya uzantısından format tipini belirler"""
        ext_map = {
            '.txt': 'txt',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml'
        }
        return ext_map.get(extension, 'txt')
    
    def _is_valid_filename(self, name: str) -> bool:
        """Dosya adının güvenli olup olmadığını kontrol eder"""
        if not name or len(name) > 100:
            return False
        return re.match(r'^[A-Za-z0-9._-]+$', name) is not None
    
    def _parse_txt(self, content: str) -> Dict[str, str]:
        """TXT formatını parse eder (key=value, # yorum)"""
        result = {}
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            
            # Boş satır veya yorum atla
            if not line or line.startswith('#'):
                continue
            
            # key=value formatını parse et
            if '=' not in line:
                logger.warning(f"Satır {line_num} geçersiz format: {line}")
                continue
            
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Anahtar doğrulama
            if not self.key_pattern.match(key):
                logger.warning(f"Satır {line_num} geçersiz anahtar: {key}")
                continue
            
            # Aynı anahtar tekrarında uyarı
            if key in result:
                logger.warning(f"Anahtar tekrarı: {key} (satır {line_num})")
            
            result[key] = value
        
        return result
    
    def _parse_json(self, content: str) -> Dict[str, str]:
        """JSON formatını parse eder ve düzleştirir"""
        try:
            data = json.loads(content)
            return self._flatten_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Geçersiz JSON: {str(e)}")
    
    def _parse_yaml(self, content: str) -> Dict[str, str]:
        """YAML formatını parse eder ve düzleştirir"""
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                raise ValueError("YAML dosyası sözlük içermeli")
            return self._flatten_dict(data)
        except yaml.YAMLError as e:
            raise ValueError(f"Geçersiz YAML: {str(e)}")
    
    def _flatten_dict(self, data: dict, parent_key: str = '', sep: str = '.') -> Dict[str, str]:
        """İç içe sözlüğü düzleştirir (nokta notasyonu ile)"""
        items = []
        
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            
            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key, sep=sep).items())
            else:
                # Tüm değerleri string'e çevir
                items.append((new_key, str(value)))
        
        return dict(items)
