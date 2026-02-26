#!/bin/sh
set -e
# Seed placeholder interpretations (idempotent)
python -m database.seed 2>/dev/null || true
exec uvicorn main:app --host 0.0.0.0 --port 10000
