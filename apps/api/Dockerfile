FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DETENTIONS_PARQUET=/app/data/processed/detentions.parquet \
    MANIFEST_PATH=/app/data/processed/manifest.json

WORKDIR /app

COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt

COPY apps/__init__.py /app/apps/__init__.py
COPY apps/api /app/apps/api
COPY src /app/src
COPY pipeline /app/pipeline
COPY config /app/config
COPY data/external /app/data/external

EXPOSE 8000

CMD ["uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
