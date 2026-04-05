from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import os

# NOT: src.database.db modülü mevcut değil - bu dosya kullanılmıyor
# Ana uygulama backend/app/main.py'de çalışıyor
try:
    from src.database.db import TestDB
except ImportError:
    TestDB = None  # Modül bulunamadı, stub olarak devam et

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

db = TestDB({
    "dbname": os.getenv("POSTGRES_DB", "test_scenarios"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "password"),
    "host": os.getenv("POSTGRES_HOST", "localhost")
}) if TestDB else None

class TestScenario(BaseModel):
    category: str
    name: str
    description: str
    test_data: Dict
    expected_result: str

@app.post("/scenarios")
async def create_scenario(scenario: TestScenario):
    if not db:
        raise HTTPException(status_code=501, detail="Bu API kullanılmıyor. Ana API: http://localhost:8000/api")
    try:
        scenario_id = db.save_test_scenario(
            scenario.category,
            scenario.name,
            scenario.description,
            scenario.test_data,
            scenario.expected_result
        )
        return {"id": scenario_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scenarios")
async def get_scenarios(category: Optional[str] = None):
    if not db:
        raise HTTPException(status_code=501, detail="Bu API kullanılmıyor. Ana API: http://localhost:8000/api")
    try:
        return db.get_test_scenarios(category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/scenarios/{scenario_id}")
async def update_scenario(scenario_id: int, scenario: TestScenario):
    if not db:
        raise HTTPException(status_code=501, detail="Bu API kullanılmıyor. Ana API: http://localhost:8000/api")
    try:
        updated = db.update_test_scenario(
            scenario_id,
            scenario.category,
            scenario.name,
            scenario.description,
            scenario.test_data,
            scenario.expected_result
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Senaryo bulunamadı")
        return {"message": "Senaryo güncellendi"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: int):
    if not db:
        raise HTTPException(status_code=501, detail="Bu API kullanılmıyor. Ana API: http://localhost:8000/api")
    try:
        deleted = db.delete_test_scenario(scenario_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Senaryo bulunamadı")
        return {"message": "Senaryo silindi"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
