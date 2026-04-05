from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request
from typing import List
import os
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.csv_model import CsvFile
from ..schemas.csv_schema import CsvFileResponse

logger = logging.getLogger(__name__)

router = APIRouter()

CSV_INPUT_DIR = "/app/data/input/Csv"  # Docker container içindeki yol

@router.get("/", response_model=List[CsvFileResponse])
async def get_csv_files(request: Request, db: Session = Depends(get_db)):
    """Veritabanındaki tüm CSV dosyalarını listele"""
    try:
        logger.debug(f"CSV dosyaları getiriliyor... URL: {request.url}")
        csv_files = db.query(CsvFile).all()
        logger.debug(f"Bulunan dosya sayısı: {len(csv_files)}")
        return csv_files
    except Exception as e:
        logger.error(f"CSV dosyaları getirilirken hata: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}", response_model=CsvFileResponse)
async def get_csv_file(file_id: int, request: Request, db: Session = Depends(get_db)):
    """Belirli bir CSV dosyasını getir"""
    try:
        logger.debug(f"CSV dosyası getiriliyor... ID: {file_id}")
        csv_file = db.query(CsvFile).filter(CsvFile.id == file_id).first()
        if not csv_file:
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        return csv_file
    except Exception as e:
        logger.error(f"CSV dosyası getirilirken hata: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_csv_file(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Yeni CSV dosyası yükle"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Sadece CSV dosyaları kabul edilir")
        
        # Dosya adı kontrolü
        if db.query(CsvFile).filter(CsvFile.name == file.filename).first():
            raise HTTPException(status_code=400, detail="Bu isimde bir dosya zaten var")
        
        logger.debug(f"Dosya yükleniyor: {file.filename}")
        
        # Klasörü oluştur (yoksa)
        os.makedirs(CSV_INPUT_DIR, exist_ok=True)
        
        # Dosyayı kaydet
        file_path = os.path.join(CSV_INPUT_DIR, file.filename)
        content = await file.read()
        
        try:
            content_str = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Dosya UTF-8 formatında değil")
        
        # Dosyayı diske kaydet
        with open(file_path, 'wb') as f:
            f.write(content)
        
        file_stat = os.stat(file_path)
        
        # Veritabanına kaydet
        db_file = CsvFile(
            name=file.filename,
            content=content_str,
            size=file_stat.st_size,
            created_at=datetime.now()
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        logger.debug(f"Dosya başarıyla yüklendi: {file.filename}")
        return {"message": "Dosya başarıyla yüklendi", "file": db_file}
        
    except HTTPException as he:
        logger.error(f"Dosya yükleme hatası: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Dosya yükleme hatası: {str(e)}", exc_info=True)
        if os.path.exists(file_path):
            os.remove(file_path)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{file_id}")
async def delete_csv_file(request: Request, file_id: int, db: Session = Depends(get_db)):
    """CSV dosyasını sil"""
    try:
        db_file = db.query(CsvFile).filter(CsvFile.id == file_id).first()
        if not db_file:
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        logger.debug(f"Dosya siliniyor: {db_file.name}")
        
        # Dosyayı diskten sil
        file_path = os.path.join(CSV_INPUT_DIR, db_file.name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                logger.error(f"Dosya diskten silinirken hata: {str(e)}")
                # Dosya silinmese bile devam et
        
        # Veritabanından sil
        db.delete(db_file)
        db.commit()
        
        logger.debug(f"Dosya başarıyla silindi: {db_file.name}")
        return {"message": "Dosya başarıyla silindi"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Dosya silme hatası: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_csv_files(request: Request, db: Session = Depends(get_db)):
    """CSV klasöründeki dosyaları veritabanı ile senkronize et"""
    try:
        logger.debug(f"CSV klasörü: {CSV_INPUT_DIR}")
        
        # Klasörü oluştur (yoksa)
        os.makedirs(CSV_INPUT_DIR, exist_ok=True)
        
        # Disk üzerindeki dosyaları listele
        disk_files = []
        if os.path.exists(CSV_INPUT_DIR):
            disk_files = [f for f in os.listdir(CSV_INPUT_DIR) if f.endswith('.csv')]
            logger.debug(f"Diskte bulunan CSV dosyaları: {disk_files}")
        
        # Veritabanındaki dosyaları al
        db_files = {file.name: file for file in db.query(CsvFile).all()}
        logger.debug(f"Veritabanında bulunan CSV dosyaları: {list(db_files.keys())}")
        
        # Yeni dosyaları ekle
        added_files = []
        for filename in disk_files:
            if filename not in db_files:
                file_path = os.path.join(CSV_INPUT_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    file_stat = os.stat(file_path)
                    db_file = CsvFile(
                        name=filename,
                        content=content,
                        size=file_stat.st_size,
                        created_at=datetime.fromtimestamp(file_stat.st_ctime)
                    )
                    db.add(db_file)
                    added_files.append(filename)
                    logger.debug(f"Yeni dosya eklendi: {filename}")
                except Exception as e:
                    logger.error(f"Dosya eklenirken hata: {filename} - {str(e)}")
        
        # Silinmiş dosyaları kaldır
        removed_files = []
        for db_filename in db_files:
            if db_filename not in disk_files:
                db.delete(db_files[db_filename])
                removed_files.append(db_filename)
                logger.debug(f"Silinen dosya kaldırıldı: {db_filename}")
        
        db.commit()
        logger.debug(f"Senkronizasyon tamamlandı. Eklenen: {len(added_files)}, Silinen: {len(removed_files)}")
        return {
            "message": f"{len(disk_files)} CSV dosyası senkronize edildi",
            "added_files": added_files,
            "removed_files": removed_files
        }
        
    except Exception as e:
        logger.error(f"Senkronizasyon hatası: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 