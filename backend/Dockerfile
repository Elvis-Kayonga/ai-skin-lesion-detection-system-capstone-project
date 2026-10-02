FROM python:3.11-slim

WORKDIR /app

# libglib is needed by OpenCV at runtime
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch keeps the image small (no GPU is needed for single-image inference)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt psycopg2-binary

COPY app ./app
COPY model ./model
RUN mkdir -p storage

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
