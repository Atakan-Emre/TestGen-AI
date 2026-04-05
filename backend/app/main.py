import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .routes import (
    csv_routes,
    json_routes,
    file_routes,
    business_rule_routes,
    dashboard_routes,
    binding_profile_routes,
    scenario_routes,
    variables_routes,
    ngi_routes,
    test_routes,
    ngv_routes,
    opt_routes,
    bsc_routes,
)
from .database import engine, Base

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,  # DEBUG yerine INFO kullan
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logging.getLogger('urllib3').setLevel(logging.WARNING)


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

# Veritabanı tablolarını oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TestGen AI API",
    description="TestGen AI senaryo, eslestirme ve test uretim API'si",
)

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

# API versiyonu ve prefix'i
API_PREFIX = "/api"

# Router'ları kaydet
app.include_router(scenario_routes.router, prefix=f"{API_PREFIX}/scenarios", tags=["scenarios"])
app.include_router(csv_routes.router, prefix=f"{API_PREFIX}/csv", tags=["csv"])
app.include_router(json_routes.router, prefix=f"{API_PREFIX}/json", tags=["json"])
app.include_router(dashboard_routes.router, prefix=f"{API_PREFIX}/dashboard", tags=["dashboard"])
app.include_router(binding_profile_routes.router, prefix=f"{API_PREFIX}/bindings", tags=["binding-profiles"])
app.include_router(test_routes.router, prefix=f"{API_PREFIX}/tests", tags=["tests"])
app.include_router(bsc_routes.router, prefix=f"{API_PREFIX}/tests/bsc", tags=["bsc"])
app.include_router(opt_routes.router, prefix=f"{API_PREFIX}/tests/opt", tags=["opt"])
app.include_router(ngv_routes.router, prefix=f"{API_PREFIX}/tests/ngv", tags=["ngv"])
app.include_router(ngi_routes.router, prefix=f"{API_PREFIX}/tests/ngi", tags=["ngi"])
app.include_router(variables_routes.router, prefix="/api/variables", tags=["variables"])
app.include_router(business_rule_routes.router, tags=["business-rules"])
app.include_router(file_routes.router, prefix=f"{API_PREFIX}/files", tags=["files"])

# Request middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Gelen istek: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.debug(f"Yanıt durumu: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Hata oluştu: {str(e)}", exc_info=True)
        raise

@app.get("/")
async def root():
    return {"message": "TestGen AI API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 
