FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home appuser

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

RUN mkdir -p /app/backend/encrypted_models /app/backend/models \
    && chown -R appuser:appuser /app

USER appuser
WORKDIR /app/backend

EXPOSE 8000

# Production startup: prepare ONLY the Logistic Regression model (fast, skipped
# when logistic_regression.enc already exists), then start FastAPI immediately.
# Uvicorn binds to Render's PORT environment variable; 8000 is only a fallback.
CMD ["sh", "-c", "python -m app.ml.ensure_model && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
