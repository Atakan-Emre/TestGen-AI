"""
RL modelleri yönetimi (opsiyonel)
"""
from dataclasses import dataclass
from typing import Optional, Any, Dict
from app.shared.settings import USE_RL, RL_MODELS_PATH
from app.shared.logging import get_logger
from app.shared.types import RLModelError


logger = get_logger(__name__)


@dataclass
class RLBundle:
    """RL model paketi"""
    field_matcher: Optional[Any] = None
    value_generator: Optional[Any] = None


def load_models() -> Optional[RLBundle]:
    """
    RL modellerini yükle
    
    Returns:
        RL model paketi veya None (RL kullanılmıyorsa)
        
    Raises:
        RLModelError: Model yükleme hatası
    """
    if not USE_RL:
        logger.info("RL modelleri devre dışı")
        return None
    
    try:
        logger.info("RL modelleri yükleniyor...")
        
        # Model dosyalarını kontrol et
        field_matcher_path = RL_MODELS_PATH / "field_matcher.zip"
        value_generator_path = RL_MODELS_PATH / "test_generator.zip"
        
        field_matcher = None
        value_generator = None
        
        # Field matcher modeli
        if field_matcher_path.exists():
            try:
                from stable_baselines3 import DQN
                field_matcher = DQN.load(str(field_matcher_path))
                logger.info("Field matcher modeli yüklendi")
            except ImportError:
                logger.warning("stable_baselines3 bulunamadı, field matcher yüklenemedi")
            except Exception as e:
                logger.warning(f"Field matcher yükleme hatası: {e}")
        else:
            logger.warning(f"Field matcher modeli bulunamadı: {field_matcher_path}")
        
        # Value generator modeli
        if value_generator_path.exists():
            try:
                from stable_baselines3 import PPO
                value_generator = PPO.load(str(value_generator_path))
                logger.info("Value generator modeli yüklendi")
            except ImportError:
                logger.warning("stable_baselines3 bulunamadı, value generator yüklenemedi")
            except Exception as e:
                logger.warning(f"Value generator yükleme hatası: {e}")
        else:
            logger.warning(f"Value generator modeli bulunamadı: {value_generator_path}")
        
        # Hiçbir model yüklenemezse None döndür
        if field_matcher is None and value_generator is None:
            logger.warning("Hiçbir RL modeli yüklenemedi")
            return None
        
        bundle = RLBundle(
            field_matcher=field_matcher,
            value_generator=value_generator
        )
        
        logger.info("RL modelleri başarıyla yüklendi")
        return bundle
        
    except ImportError as e:
        error_msg = f"RL kütüphaneleri bulunamadı: {e}"
        logger.warning(error_msg)
        return None
    except Exception as e:
        error_msg = f"RL model yükleme hatası: {e}"
        logger.error(error_msg)
        raise RLModelError(error_msg)


def predict_field_match(rl_model: Any, constraints: Any, schema_info: Any) -> Optional[str]:
    """
    RL model ile alan eşleştirmesi yap
    
    Args:
        rl_model: RL model
        constraints: Kısıtlamalar
        schema_info: Şema bilgisi
        
    Returns:
        Tahmin edilen alan path'i veya None
    """
    if rl_model is None:
        return None
    
    try:
        # RL model kullanımı (implementasyon detaylarına bağlı)
        # Bu kısım modelin nasıl eğitildiğine göre değişebilir
        logger.debug("RL model ile alan eşleştirmesi yapılıyor")
        
        # Placeholder implementasyon
        # Gerçek implementasyon modelin state/action space'ine göre olmalı
        return None
        
    except Exception as e:
        logger.warning(f"RL model tahmin hatası: {e}")
        return None


def generate_value_with_rl(rl_model: Any, field_type: str, constraints: Any) -> Optional[Any]:
    """
    RL model ile değer üret
    
    Args:
        rl_model: RL model
        field_type: Alan tipi
        constraints: Kısıtlamalar
        
    Returns:
        Üretilen değer veya None
    """
    if rl_model is None:
        return None
    
    try:
        # RL model kullanımı (implementasyon detaylarına bağlı)
        logger.debug("RL model ile değer üretimi yapılıyor")
        
        # Placeholder implementasyon
        # Gerçek implementasyon modelin state/action space'ine göre olmalı
        return None
        
    except Exception as e:
        logger.warning(f"RL model değer üretim hatası: {e}")
        return None


def is_rl_available() -> bool:
    """
    RL modellerinin kullanılabilir olup olmadığını kontrol et
    
    Returns:
        RL kullanılabilir mi?
    """
    if not USE_RL:
        return False
    
    try:
        import stable_baselines3
        return True
    except ImportError:
        return False


def get_rl_model_info() -> Dict[str, Any]:
    """
    RL model bilgilerini al
    
    Returns:
        Model bilgi dictionary'si
    """
    info = {
        "rl_enabled": USE_RL,
        "models_available": False,
        "field_matcher_available": False,
        "value_generator_available": False,
        "models_path": str(RL_MODELS_PATH) if RL_MODELS_PATH else None
    }
    
    if USE_RL and RL_MODELS_PATH.exists():
        info["models_available"] = True
        
        field_matcher_path = RL_MODELS_PATH / "field_matcher.zip"
        value_generator_path = RL_MODELS_PATH / "test_generator.zip"
        
        info["field_matcher_available"] = field_matcher_path.exists()
        info["value_generator_available"] = value_generator_path.exists()
    
    return info
