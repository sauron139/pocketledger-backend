#!/bin/bash
alembic upgrade head
python -m app.seeds.default_categories
exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}
