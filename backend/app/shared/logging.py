"""
Logging konfigürasyonu ve yardımcı fonksiyonlar
"""
import logging
import sys
import warnings
from typing import Optional
from .settings import LOG_LEVEL, LOG_FORMAT


def get_logger(name: str = "app", level: Optional[str] = None) -> logging.Logger:
    """
    Konfigüre edilmiş logger oluştur
    
    Args:
        name: Logger adı
        level: Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Konfigüre edilmiş logger
    """
    logger = logging.getLogger(name)
    
    # Logger zaten konfigüre edilmişse tekrar konfigüre etme
    if logger.handlers:
        return logger
    
    # Log seviyesini ayarla
    log_level = level or LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Console handler oluştur
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logger.level)
    
    # Formatter oluştur
    formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Handler'ı logger'a ekle
    logger.addHandler(console_handler)
    
    # Logger'ın parent'a propagate etmesini engelle
    logger.propagate = False
    
    return logger


def setup_warnings() -> None:
    """Warning filtrelerini ayarla"""
    # Transformers ve diğer kütüphanelerden gelen uyarıları filtrele
    warnings.filterwarnings("ignore", category=UserWarning, module="transformers")
    warnings.filterwarnings("ignore", category=UserWarning, module="sentence_transformers")
    warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="numpy")
    
    # Spacy uyarıları
    warnings.filterwarnings("ignore", category=UserWarning, module="spacy")
    
    # Stable baselines uyarıları
    warnings.filterwarnings("ignore", category=UserWarning, module="stable_baselines3")


def log_function_call(func_name: str, args: tuple = None, kwargs: dict = None) -> None:
    """
    Fonksiyon çağrısını logla (debug seviyesinde)
    
    Args:
        func_name: Fonksiyon adı
        args: Fonksiyon argümanları
        kwargs: Fonksiyon keyword argümanları
    """
    logger = get_logger()
    if logger.isEnabledFor(logging.DEBUG):
        args_str = str(args) if args else "()"
        kwargs_str = str(kwargs) if kwargs else "{}"
        logger.debug(f"Çağrılan fonksiyon: {func_name}{args_str}, kwargs={kwargs_str}")


def log_performance(func_name: str, duration: float) -> None:
    """
    Performans bilgisini logla
    
    Args:
        func_name: Fonksiyon adı
        duration: Süre (saniye)
    """
    logger = get_logger()
    logger.info(f"Performans: {func_name} {duration:.3f}s sürdü")


# Uygulama başlangıcında warning filtrelerini ayarla
setup_warnings()
