#!/bin/sh
set -e
# Seed reference tables and interpretation data on startup (idempotent; preserves existing content)
python -m database.seed
python -m database.seed_from_csv --overwrite
# Merge sun_sign_interpretations into signs (no-op if table already dropped)
python -m scripts.merge_sun_into_signs 2>/dev/null || true
exec uvicorn main:app --host 0.0.0.0 --port 10000
