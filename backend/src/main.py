from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from pathlib import Path
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import shutil
import pandas as pd
import numpy as np
from src.generators.bert_ner_generator import BertNerGenerator
from datetime import datetime
from urllib.parse import unquote
from typing import List, Dict, Any
import json
import traceback
from pydantic import BaseModel

# Detaylı logging ayarları
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()


def _resolve_cors_origins() -> list[str]:
    configured = os.getenv("CORS_ORIGINS", "").strip()
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]

# CORS ayarları
cors_origins = _resolve_cors_origins()
allow_all_origins = "*" in cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else cors_origins,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global hata yakalayıcı
@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        logger.debug(f"Gelen istek: {request.method} {request.url}")
        response = await call_next(request)
        logger.debug(f"Yanıt durumu: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"İstek işlenirken hata: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

# Database bağlantı fonksiyonu
def get_db_connection():
    return psycopg2.connect(
        host="db",
        database="testdb",
        user="postgres",
        password="postgres",
        cursor_factory=RealDictCursor
    )

# Data klasör yolları
DATA_DIR = Path("/app/data")
CSV_DIR = DATA_DIR / "input" / "Csv"
JSON_DIR = DATA_DIR / "input" / "Json"
SCENARIOS_DIR = DATA_DIR / "output" / "test_scenarios"

# Generator instance'ı oluştur
bert_generator = BertNerGenerator()

# Senaryo oluşturma için model
class ScenarioCreate(BaseModel):
    name: str
    csv_file_id: int
    csv_file_name: str
    generator_type: str = "bert_ner"

@app.get("/scenarios")
async def get_scenarios():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Test senaryolarını getir
        cur.execute("""
            SELECT id, name, description, created_at, updated_at, status
            FROM test_scenarios
            ORDER BY created_at DESC
        """)
        scenarios = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {"scenarios": scenarios}
    except Exception as e:
        logger.error(f"Senaryolar listelenirken hata: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Senaryolar listelenirken hata oluştu: {str(e)}"}
        )

@app.get("/debug/paths")
async def debug_paths():
    """Dosya yollarını debug etmek için endpoint"""
    return {
        "DATA_DIR exists": DATA_DIR.exists(),
        "CSV_DIR exists": CSV_DIR.exists(),
        "JSON_DIR exists": JSON_DIR.exists(),
        "DATA_DIR content": [str(p) for p in DATA_DIR.glob("**/*") if p.is_file()],
        "Current working directory": os.getcwd(),
        "Directory listing": os.listdir("/app")
    }

@app.get("/api/files/{type}")
async def get_files(type: str):
    try:
        if type.lower() not in ['csv', 'json']:
            raise HTTPException(status_code=400, detail="Geçersiz dosya tipi")
            
        # Dosya tipine göre dizin yolunu belirle
        folder_path = DATA_DIR / "input" / type.upper()
        
        if not folder_path.exists():
            os.makedirs(folder_path, exist_ok=True)
            return {"files": []}
            
        files = []
        for file in folder_path.glob(f"*.{type.lower()}"):
            stats = file.stat()
            files.append({
                "id": file.name,
                "name": file.name,
                "size": stats.st_size,
                "created_at": datetime.fromtimestamp(stats.st_ctime).isoformat()
            })
                
        return {"files": files}
        
    except Exception as e:
        logger.error(f"Dosya listesi alınırken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/{type}/upload")
async def upload_file(type: str, file: UploadFile = File(...)):
    try:
        if type.lower() not in ['csv', 'json']:
            raise HTTPException(status_code=400, detail="Geçersiz dosya tipi")
            
        folder_path = DATA_DIR / "input" / type.upper()
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = folder_path / file.filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"message": "Dosya başarıyla yüklendi"}
        
    except Exception as e:
        logger.error(f"Dosya yükleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files/{type}/{filename}")
async def delete_file(type: str, filename: str):
    try:
        if type.lower() not in ['csv', 'json']:
            raise HTTPException(status_code=400, detail="Geçersiz dosya tipi")
            
        file_path = DATA_DIR / "input" / type.upper() / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
            
        os.remove(file_path)
        return {"message": "Dosya başarıyla silindi"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Dosya silme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{type}")
async def get_files(type: str):
    try:
        if type not in ['csv', 'json']:
            return JSONResponse(
                status_code=400,
                content={"error": "Geçersiz dosya tipi"}
            )

        target_dir = CSV_DIR if type == 'csv' else JSON_DIR
        files = [f.name for f in target_dir.glob(f"*.{type}")]
        logger.info(f"Bulunan {type.upper()} dosyaları: {files}")
        return {"files": files}
    except Exception as e:
        logger.error(f"Dosyalar listelenirken hata: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Dosyalar listelenemedi: {str(e)}"}
        )

@app.get("/files/{type}/{filename}/content")
async def get_file_content(type: str, filename: str):
    try:
        if type not in ['csv', 'json']:
            return JSONResponse(
                status_code=400,
                content={"error": "Geçersiz dosya tipi"}
            )

        target_dir = CSV_DIR if type == 'csv' else JSON_DIR
        file_path = target_dir / filename

        if not file_path.exists():
            return JSONResponse(
                status_code=404,
                content={"error": "Dosya bulunamadı"}
            )

        if type == 'csv':
            # CSV'yi pandas ile oku ve NaN değerleri boş string ile değiştir
            df = pd.read_csv(file_path)
            df = df.replace({np.nan: '', np.inf: '', -np.inf: ''})
            
            # Tüm sayısal değerleri stringe çevir
            for column in df.select_dtypes(include=[np.number]).columns:
                df[column] = df[column].astype(str)
            
            # DataFrame'i JSON formatına çevir
            result = {
                "headers": df.columns.tolist(),
                "rows": df.to_dict('records')
            }
            
            # JSON serileştirme hatalarını önlemek için tüm değerleri stringe çevir
            result["rows"] = [{k: str(v) if v is not None else '' for k, v in row.items()} 
                            for row in result["rows"]]
            
            return JSONResponse(content=result)
        else:
            # JSON dosyaları için
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content

    except Exception as e:
        logger.error(f"Dosya içeriği okunurken hata: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Dosya içeriği okunamadı: {str(e)}"}
        )

@app.get("/")
def read_root():
    return {"message": "API is running"}

@app.post("/api/scenarios/generate")
async def generate_scenarios(request: Request):
    try:
        # Request body'yi JSON olarak al
        data = await request.json()
        logger.info(f"Gelen istek verisi: {data}")
        
        csv_file = data.get("csv_file_name")
        scenario_name = data.get("name")
        generator_type = data.get("generator_type", "bert_ner")

        logger.info(f"CSV Dosyası: {csv_file}")
        logger.info(f"Senaryo Adı: {scenario_name}")
        logger.info(f"Generator Tipi: {generator_type}")

        if not csv_file:
            raise HTTPException(status_code=400, detail="CSV dosyası belirtilmedi")

        file_path = str(CSV_DIR / csv_file)
        logger.info(f"CSV dosya yolu: {file_path}")
        logger.info(f"Dosya mevcut mu: {os.path.exists(file_path)}")

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="CSV dosyası bulunamadı")

        logger.info("Test senaryoları oluşturuluyor...")
        
        if generator_type == "bert_ner":
            try:
                # BERT generator'ı kullanarak senaryoları oluştur
                logger.info("BERT generator başlatılıyor...")
                scenarios = bert_generator.generate_scenarios(csv_file, scenario_name)
                logger.info("BERT generator senaryoları oluşturdu")
                
                # Liste olarak gelen senaryoları stringe çevir
                scenarios_text = "\n\n".join(scenarios) if isinstance(scenarios, list) else scenarios
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{scenario_name}_{timestamp}.txt"
                output_path = str(SCENARIOS_DIR / filename)
                
                # Dosyaya kaydet
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(scenarios_text)
                    
                logger.info(f"Test senaryoları kaydedildi: {output_path}")
                
                # Veritabanına kaydet
                try:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    cur.execute("""
                        INSERT INTO scenarios (name, content, created_at, status)
                        VALUES (%s, %s, %s, %s)
                    """, (filename, scenarios_text, datetime.now(), 'Aktif'))
                    
                    conn.commit()
                    cur.close()
                    conn.close()
                    logger.info("Senaryo veritabanına kaydedildi")
                except Exception as e:
                    logger.error(f"Veritabanına kayıt hatası: {str(e)}")
                    
                return {
                    "status": "success",
                    "message": "Test senaryoları başarıyla oluşturuldu",
                    "filename": filename,
                    "scenarios": scenarios_text
                }
            except Exception as e:
                logger.error(f"BERT generator hatası: {str(e)}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=f"BERT generator hatası: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="Geçersiz generator tipi")

    except Exception as e:
        logger.error(f"Senaryo oluşturulurken hata: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scenarios")
async def save_scenario(scenario_data: dict):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Senaryo bilgilerini veritabanına kaydet
        cur.execute("""
            INSERT INTO scenarios (name, content, created_at, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            scenario_data["name"],
            scenario_data["content"],
            datetime.now(),
            'Aktif'
        ))
        
        scenario_id = cur.fetchone()["id"]
        conn.commit()
        
        # Dosyaya da kaydet
        scenarios_dir = "/app/data/output/test_scenarios"
        os.makedirs(scenarios_dir, exist_ok=True)
        
        file_path = os.path.join(scenarios_dir, f"{scenario_data['name']}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(scenario_data["content"])
        
        cur.close()
        conn.close()
        
        return {"id": scenario_id, "message": "Senaryo başarıyla kaydedildi"}
    except Exception as e:
        logger.error(f"Senaryo kaydedilirken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/scenarios")
async def get_scenarios():
    try:
        # 1. Doğru dizin yolunu kullan
        scenarios_dir = "/app/data/output/test_scenarios"
        logger.info(f"Dizin kontrol: {scenarios_dir}")

        # 2. Dizin var mı kontrol et
        if not os.path.exists(scenarios_dir):
            logger.warning(f"Dizin bulunamadı: {scenarios_dir}")
            os.makedirs(scenarios_dir, exist_ok=True)
            logger.info("Dizin oluşturuldu")
            return {"rows": []}

        # 3. Dosya listesini al
        files = []
        for file in os.listdir(scenarios_dir):
            if file.endswith('.txt'):
                try:
                    file_path = os.path.join(scenarios_dir, file)
                    logger.debug(f"Dosya okunuyor: {file_path}")
                    
                    # Dosya bilgilerini al
                    stat = os.stat(file_path)
                    
                    # Dosya bilgilerini listeye ekle
                    files.append({
                        "Senaryo Adı": file,
                        "Oluşturma Tarihi": datetime.fromtimestamp(stat.st_ctime).strftime('%d.%m.%Y %H:%M'),
                        "Boyut (KB)": f"{stat.st_size / 1024:.2f}",
                        "Durum": "Aktif"
                    })
                    logger.debug(f"Dosya başarıyla eklendi: {file}")
                except Exception as e:
                    logger.error(f"Dosya okuma hatası - {file}: {str(e)}")
                    continue

        logger.info(f"Toplam {len(files)} senaryo bulundu")
        return {"rows": files}

    except Exception as e:
        logger.error(f"Genel hata: {str(e)}")
        return JSONResponse(
            status_code=200,  # Frontend'e boş liste dönüyoruz
            content={"rows": []}
        )

@app.get("/files/scenarios/{filename}")
async def get_scenario_content(filename: str):
    """Senaryo içeriğini getir"""
    try:
        file_path = os.path.join(DATA_DIR, "output", "test_scenarios", filename)
        
        if not os.path.exists(file_path):
            logger.error(f"Senaryo bulunamadı: {filename}")
            raise HTTPException(status_code=404, detail="Senaryo bulunamadı")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {"content": content}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Senaryo okuma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/scenarios/{filename}")
async def delete_scenario(filename: str):
    """Senaryo dosyasını sil"""
    try:
        file_path = SCENARIOS_DIR / filename
        logger.info(f"Silinecek dosya: {file_path}")
        
        if not file_path.exists():
            logger.error(f"Silinecek senaryo bulunamadı: {filename}")
            raise HTTPException(status_code=404, detail="Senaryo bulunamadı")

        os.remove(file_path)
        logger.info(f"Senaryo silindi: {filename}")
        
        return {"message": "Senaryo başarıyla silindi"}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Senaryo silme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scenarios")
async def get_scenarios():
    try:
        scenarios_dir = SCENARIOS_DIR
        if not scenarios_dir.exists():
            return []
            
        scenarios = []
        for file in scenarios_dir.glob("*.txt"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    name = file.stem.split('_')[0]  # İlk kısım senaryo adı
                    date = '_'.join(file.stem.split('_')[1:])  # Geri kalanı tarih
                    scenarios.append({
                        "id": file.stem,
                        "name": name,
                        "date": date,
                        "content": content,
                        "filename": file.name  # Tam dosya adını da ekle
                    })
            except Exception as e:
                logger.error(f"Dosya okuma hatası - {file}: {str(e)}")
                continue
                
        return scenarios

    except Exception as e:
        logger.error(f"Senaryo listeleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/csv/{filename}/content")
async def get_csv_content(filename: str):
    """CSV dosyasının içeriğini getir"""
    try:
        # Dosya yolunu düzelt
        file_path = DATA_DIR / "input" / "CSV" / unquote(filename)
        logger.debug(f"CSV dosya yolu: {file_path}")
        
        if not file_path.exists():
            logger.error(f"CSV dosyası bulunamadı: {filename}")
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")

        # CSV dosyasını oku
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"CSV içeriği okundu: {len(content)} karakter")
            return {"content": content}
        except UnicodeDecodeError:
            # UTF-8 ile okunamazsa diğer encoding'leri dene
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            logger.debug(f"CSV içeriği latin-1 ile okundu: {len(content)} karakter")
            return {"content": content}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"CSV dosyası okuma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/json/{filename}/content")
async def get_json_content(filename: str):
    """JSON dosyasının içeriğini getir"""
    try:
        # Dosya yolunu düzelt
        file_path = DATA_DIR / "input" / "JSON" / unquote(filename)
        logger.debug(f"JSON dosya yolu: {file_path}")
        
        if not file_path.exists():
            logger.error(f"JSON dosyası bulunamadı: {filename}")
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")

        # JSON dosyasını oku
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # JSON formatını doğrula
                json.loads(content)  # Hatalı JSON kontrolü
            logger.debug(f"JSON içeriği okundu: {len(content)} karakter")
            return {"content": content}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Geçersiz JSON formatı")
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            logger.debug(f"JSON içeriği latin-1 ile okundu: {len(content)} karakter")
            return {"content": content}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"JSON dosyası okuma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
