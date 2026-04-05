from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List
import logging
from pathlib import Path

from ..schemas.variables import (
    VariableProfilesResponse, 
    VariablePreviewResponse, 
    VariableDeleteResponse,
    VariableUploadRequest
)
from ..services.variables_loader import VariablesLoader
from src.config.settings import VARIABLES_DIR

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Variables"])

# Variables loader instance
variables_loader = VariablesLoader(str(VARIABLES_DIR))

@router.get("/profiles", response_model=VariableProfilesResponse)
async def list_variables_profiles():
    """Mevcut variables profillerini listeler"""
    try:
        profiles = variables_loader.list_profiles()
        return VariableProfilesResponse(
            success=True,
            data=profiles,
            message=f"{len(profiles)} profil bulundu" if profiles else "Profil bulunamadı"
        )
    except Exception as e:
        logger.error(f"Profil listesi alınırken hata: {str(e)}")
        return VariableProfilesResponse(
            success=False,
            data=[],
            message=f"Profil listesi alınamadı: {str(e)}"
        )

@router.get("/profiles/{name}", response_model=VariablePreviewResponse)
async def get_variables_profile(name: str):
    """Belirtilen variables profilini önizleme için getirir"""
    try:
        variables = variables_loader.load_profile(name)
        return VariablePreviewResponse(
            success=True,
            data=variables,
            message=f"Profil yüklendi: {name}"
        )
    except FileNotFoundError:
        return VariablePreviewResponse(
            success=False,
            data={},
            message=f"Profil bulunamadı: {name}"
        )
    except Exception as e:
        logger.error(f"Profil yüklenirken hata ({name}): {str(e)}")
        return VariablePreviewResponse(
            success=False,
            data={},
            message=f"Profil yüklenemedi: {str(e)}"
        )

@router.post("/profiles/upload")
async def upload_variables_profile(
    file: UploadFile = File(...),
    name: str = Form(...),
    format: str = Form(...)
):
    """Yeni variables profil yükler"""
    try:
        # Format doğrulama
        if format not in ['txt', 'json', 'yaml']:
            raise HTTPException(
                status_code=400, 
                detail="Desteklenmeyen format. Geçerli formatlar: txt, json, yaml"
            )
        
        # Dosya boyutu kontrolü (10MB limit)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=413,
                detail="Dosya çok büyük. Maksimum 10MB desteklenir."
            )
        
        # Profili kaydet
        file_path = variables_loader.save_profile(name, content, format)
        
        return {
            "success": True,
            "message": f"Profil başarıyla yüklendi: {name}",
            "data": {"file_path": file_path}
        }
        
    except FileExistsError:
        raise HTTPException(
            status_code=409,
            detail=f"Profil zaten mevcut: {name}. Mevcut profilleri kontrol etmek için GET /api/variables/profiles kullanın."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Profil yüklenirken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Profil yüklenemedi: {str(e)}")

@router.delete("/profiles/{name}", response_model=VariableDeleteResponse)
async def delete_variables_profile(name: str):
    """Variables profilini siler"""
    try:
        success = variables_loader.delete_profile(name)
        if success:
            return VariableDeleteResponse(
                success=True,
                message=f"Profil silindi: {name}"
            )
        else:
            return VariableDeleteResponse(
                success=False,
                message=f"Profil bulunamadı: {name}"
            )
    except Exception as e:
        logger.error(f"Profil silinirken hata ({name}): {str(e)}")
        return VariableDeleteResponse(
            success=False,
            message=f"Profil silinemedi: {str(e)}"
        )

@router.post("/sync")
async def sync_variables_profiles():
    """Variables profillerini dosya sisteminden senkronize eder"""
    try:
        profiles = variables_loader.list_profiles()
        return {
            "success": True,
            "message": f"Senkronizasyon tamamlandı. {len(profiles)} profil bulundu.",
            "data": {"profiles": profiles}
        }
    except Exception as e:
        logger.error(f"Senkronizasyon hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Senkronizasyon başarısız: {str(e)}")
