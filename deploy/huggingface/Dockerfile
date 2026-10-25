# One container for the online demo on Hugging Face Spaces: the API also serves the built web app.
# Build context = repo root:  docker build -f deploy/huggingface/Dockerfile -t skin-screening .

# ---- 1. build the web app ----
FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# "same-origin": the web app calls the API on the address it was loaded from
RUN VITE_API_URL=same-origin npm run build

# ---- 2. the API with the model ----
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
# Only the deployed model; the original model stays in the repo as a fallback.
COPY backend/model/efficientnet_b3_best.pth backend/model/model_config.json ./model/
COPY --from=web /web/dist ./web

# Hugging Face runs the container as a non-root user and only /tmp is writable.
# The database and uploaded images live there, so they are wiped when the Space restarts (fine for a demo).
ENV FRONTEND_DIR=/app/web \
    DATABASE_URL=sqlite:////tmp/skin_screening.db \
    STORAGE_DIR=/tmp/storage \
    MPLCONFIGDIR=/tmp/matplotlib \
    CORS_ORIGINS='[]'
# Build the plotting font cache now, so the first start is not slowed down by it
RUN python -c "import matplotlib.pyplot" && chmod -R a+rwX /tmp/matplotlib

EXPOSE 7860
# SECRET_KEY: use the Space secret if one is set, otherwise make a random one at each start.
# A new key only logs out the anonymous browser sessions, and the app silently creates new ones;
# the database is wiped on restart anyway. No key is ever stored in Git.
CMD ["sh", "-c", "export SECRET_KEY=${SECRET_KEY:-$(python -c 'import secrets; print(secrets.token_hex(32))')} && exec uvicorn app.main:app --host 0.0.0.0 --port 7860"]
