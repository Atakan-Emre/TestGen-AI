#!/bin/bash

set -e

host="$POSTGRES_HOST"
port="$POSTGRES_PORT"
user="$POSTGRES_USER"
password="$POSTGRES_PASSWORD"
db="$POSTGRES_DB"

until PGPASSWORD=$password psql -h "$host" -p "$port" -U "$user" -d "$db" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
# NOT: Doğru path app.main:app olmalı (backend/app/main.py)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 