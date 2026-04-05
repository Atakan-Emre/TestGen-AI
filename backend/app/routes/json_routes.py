import os
import json
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.json_file import JsonFile, JsonFileResponse

router = APIRouter()
logger = logging.getLogger(__name__)

JSON_INPUT_DIR = "/app/data/input/Json"  # Docker container içindeki yol

@router.get("/", response_model=List[JsonFileResponse])
async def get_json_files(request: Request, db: Session = Depends(get_db)):
    """Veritabanındaki tüm JSON dosyalarını listele"""
    try:
        logger.debug(f"JSON dosyaları getiriliyor... URL: {request.url}")
        json_files = db.query(JsonFile).all()
        logger.debug(f"Bulunan dosya sayısı: {len(json_files)}")
        return json_files
    except Exception as e:
        logger.error(f"JSON dosyaları getirilirken hata: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_json_files(request: Request, db: Session = Depends(get_db)):
    """JSON klasöründeki dosyaları veritabanı ile senkronize et"""
    try:
        logger.debug(f"JSON klasörü: {JSON_INPUT_DIR}")
        logger.debug(f"Klasör mevcut mu: {os.path.exists(JSON_INPUT_DIR)}")
        
        # Klasörü oluştur (yoksa)
        os.makedirs(JSON_INPUT_DIR, exist_ok=True)
        
        # Klasördeki JSON dosyalarını tara
        json_files = []
        if os.path.exists(JSON_INPUT_DIR):
            for filename in os.listdir(JSON_INPUT_DIR):
                if filename.endswith('.json'):
                    file_path = os.path.join(JSON_INPUT_DIR, filename)
                    logger.debug(f"Dosya işleniyor: {filename}")
                    
                    file_stat = os.stat(file_path)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                    
                    # Veritabanında dosya var mı kontrol et
                    db_file = db.query(JsonFile).filter(JsonFile.name == filename).first()
                    
                    if not db_file:
                        logger.debug(f"Yeni dosya ekleniyor: {filename}")
                        # Yeni dosya oluştur
                        db_file = JsonFile(
                            name=filename,
                            content=content,  # JSON olarak kaydet
                            size=file_stat.st_size,
                            created_at=datetime.fromtimestamp(file_stat.st_ctime)
                        )
                        db.add(db_file)
                    else:
                        logger.debug(f"Mevcut dosya güncelleniyor: {filename}")
                        # Mevcut dosyayı güncelle
                        db_file.content = content  # JSON olarak güncelle
                        db_file.size = file_stat.st_size
                        db_file.updated_at = datetime.now()
                    
                    json_files.append(db_file)
        
        db.commit()
        logger.debug(f"Toplam {len(json_files)} dosya senkronize edildi")
        return {"message": f"{len(json_files)} JSON dosyası senkronize edildi"}
        
    except Exception as e:
        logger.error(f"Senkronizasyon hatası: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_json_file(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Yeni JSON dosyası yükle"""
    try:
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Sadece JSON dosyaları kabul edilir")
        
        logger.debug(f"Dosya yükleniyor: {file.filename}")
        
        # Klasörü oluştur (yoksa)
        os.makedirs(JSON_INPUT_DIR, exist_ok=True)
        
        # Dosyayı kaydet
        file_path = os.path.join(JSON_INPUT_DIR, file.filename)
        content = await file.read()
        
        # JSON formatını kontrol et
        try:
            json_content = json.loads(content.decode())
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Geçersiz JSON formatı")
        
        # Dosyayı diske kaydet
        with open(file_path, 'wb') as f:
            f.write(content)
        
        file_stat = os.stat(file_path)
        
        # Veritabanına kaydet
        db_file = JsonFile(
            name=file.filename,
            content=json_content,  # JSON olarak kaydet
            size=file_stat.st_size,
            created_at=datetime.now()
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        logger.debug(f"Dosya başarıyla yüklendi: {file.filename}")
        return {"message": "Dosya başarıyla yüklendi", "file": db_file}
        
    except Exception as e:
        logger.error(f"Dosya yükleme hatası: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{file_id}")
async def delete_json_file(request: Request, file_id: int, db: Session = Depends(get_db)):
    """JSON dosyasını sil"""
    try:
        db_file = db.query(JsonFile).filter(JsonFile.id == file_id).first()
        if not db_file:
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        logger.debug(f"Dosya siliniyor: {db_file.name}")
        
        # Dosyayı diskten sil
        file_path = os.path.join(JSON_INPUT_DIR, db_file.name)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Veritabanından sil
        db.delete(db_file)
        db.commit()
        
        logger.debug(f"Dosya başarıyla silindi: {db_file.name}")
        return {"message": "Dosya başarıyla silindi"}
        
    except Exception as e:
        logger.error(f"Dosya silme hatası: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}", response_model=JsonFileResponse)
async def get_json_file(file_id: int, request: Request, db: Session = Depends(get_db)):
    """Belirli bir JSON dosyasını getir"""
    try:
        logger.debug(f"JSON dosyası getiriliyor... ID: {file_id}")
        json_file = db.query(JsonFile).filter(JsonFile.id == file_id).first()
        if not json_file:
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        return json_file
    except Exception as e:
        logger.error(f"JSON dosyası getirilirken hata: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 