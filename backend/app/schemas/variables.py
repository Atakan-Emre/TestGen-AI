from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime

class VariableProfileInfo(BaseModel):
    """Variables profil bilgisi"""
    name: str = Field(..., description="Profil adı (uzantısız)")
    format: Literal["txt", "json", "yaml"] = Field(..., description="Dosya formatı")
    size_bytes: int = Field(..., description="Dosya boyutu (byte)")
    updated_at: str = Field(..., description="Son güncelleme tarihi (ISO format)")

class VariableProfilesResponse(BaseModel):
    """Variables profilleri listesi yanıtı"""
    success: bool = Field(True, description="İşlem başarılı mı")
    data: List[VariableProfileInfo] = Field(..., description="Profil listesi")
    message: Optional[str] = Field(None, description="Hata mesajı veya bilgi")

class VariablePreviewResponse(BaseModel):
    """Variables profil önizleme yanıtı"""
    success: bool = Field(True, description="İşlem başarılı mı")
    data: Dict[str, str] = Field(..., description="Düzleştirilmiş değişkenler")
    message: Optional[str] = Field(None, description="Hata mesajı veya bilgi")

class VariableUploadRequest(BaseModel):
    """Variables profil yükleme isteği"""
    name: str = Field(..., description="Profil adı", min_length=1, max_length=100)
    format: Literal["txt", "json", "yaml"] = Field(..., description="Dosya formatı")

class VariableDeleteResponse(BaseModel):
    """Variables profil silme yanıtı"""
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field(..., description="Sonuç mesajı")
    data: Optional[Dict] = Field(None, description="Ek veri")