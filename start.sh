#!/bin/sh
set -e
# Seed reference tables and interpretation data on startup (idempotent; preserves existing content)
python -m database.seed
python -m database.seed_from_csv --overwrite
exec uvicorn main:app --host 0.0.0.0 --port 10000
