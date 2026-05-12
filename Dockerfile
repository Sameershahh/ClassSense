# ============================================================
# ClassSense — Backend Dockerfile
# ============================================================
FROM python:3.10-slim

# System deps
#   libgl1       → OpenCV (replaces deprecated libgl1-mesa-glx on Debian 12)
#   libglib2.0-0 → OpenCV / MediaPipe
#   libgomp1     → PyTorch OpenMP (required for CPU inference)
#   libpq-dev    → psycopg2
#   build-essential → native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only torch first (avoids pip pulling the 2 GB CUDA wheel)
RUN pip install --no-cache-dir \
    torch==2.2.2 torchvision==0.17.2 \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python deps (torch/torchvision excluded from requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Directories the app writes to at runtime
RUN mkdir -p reports /tmp/classsense_uploads ml/emotion/model_weights

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
