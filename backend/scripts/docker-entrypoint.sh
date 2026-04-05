#!/bin/bash
set -e

DATA_ROOT="${DATA_ROOT:-/app/data}"
APP_SOURCE_ROOT="${APP_SOURCE_ROOT:-/app}"

if [ -d "$APP_SOURCE_ROOT" ]; then
    cd "$APP_SOURCE_ROOT"
fi

mkdir -p \
    "$DATA_ROOT/input/Csv" \
    "$DATA_ROOT/input/Json" \
    "$DATA_ROOT/input/Variables" \
    "$DATA_ROOT/input/BindingProfiles" \
    "$DATA_ROOT/output/test_scenarios" \
    "$DATA_ROOT/output/test_cases" \
    "$DATA_ROOT/output/binding_validation_reports"

# Alembic migrations'ı çalıştır
echo "Running database migrations..."
alembic upgrade head || echo "Migration failed, continuing..."

# Environment'a göre uvicorn'u başlat
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Starting in PRODUCTION mode..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 4 \
        --log-level info
else
    echo "Starting in DEVELOPMENT mode with hot reload..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --reload-dir "$APP_SOURCE_ROOT/app" \
        --reload-exclude 'data/*' \
        --reload-exclude '*.log' \
        --reload-exclude '*.pyc' \
        --reload-exclude '*.pyo' \
        --reload-exclude '*.sqlite' \
        --reload-exclude '__pycache__/*' \
        --reload-exclude '.pytest_cache/*' \
        --reload-exclude 'htmlcov/*' \
        --log-level debug
fi
