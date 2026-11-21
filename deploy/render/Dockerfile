# Free online demo on Render (512 MB RAM): one container, the API also serves the built web app.
# Uses ONNX Runtime instead of PyTorch (same model and maths, about a quarter of the memory; see
# backend/app/ml/onnx_runtime.py). Build context = repo root:
#   docker build -f deploy/render/Dockerfile -t skin-screening .

# ---- 1. build the web app ----
FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# "same-origin": the web app calls the API on the address it was loaded from
RUN VITE_API_URL=same-origin npm run build

# ---- 2. the API with the ONNX model ----
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt

COPY backend/app ./app
# Only the files the ONNX backend needs (exported by backend/scripts/export_onnx.py)
COPY backend/model/efficientnet_b3_features.onnx backend/model/classifier_head.npz \
     backend/model/model_config.json ./model/
COPY --from=web /web/dist ./web

# DATABASE_URL (PostgreSQL) and SECRET_KEY come from the Render dashboard / render.yaml, never from Git.
# Photos and heatmaps are kept in the database because Render's free disk is wiped on every restart.
ENV FRONTEND_DIR=/app/web \
    INFERENCE_BACKEND=onnx \
    IMAGE_STORE=db \
    STORAGE_DIR=/tmp/storage \
    CORS_ORIGINS='[]' \
    PORT=10000
EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
