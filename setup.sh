#!/usr/bin/env bash
# ============================================================
# ClassSense — Local Dev Setup
# Run once from the project root:
#   chmod +x setup.sh && ./setup.sh
#
# Windows (PowerShell) equivalent commands are in comments.
# ============================================================
set -e

echo "=== ClassSense Backend Setup ==="

# 1. Python version check
python --version | grep -q "3.10" || python3 --version | grep -q "3.10" || {
    echo "⚠  Python 3.10 recommended. Continuing anyway..."
}

# 2. Virtual environment
if [ ! -d "venv" ]; then
    echo "→ Creating virtualenv..."
    python -m venv venv
    # Windows: python -m venv venv
fi

# 3. Activate
source venv/bin/activate
# Windows: .\venv\Scripts\Activate.ps1

echo "→ Installing CPU-only PyTorch (saves ~1.5 GB vs CUDA)..."
pip install --quiet torch==2.2.2 torchvision==0.17.2 \
    --index-url https://download.pytorch.org/whl/cpu

echo "→ Installing project dependencies..."
pip install --quiet -r requirements.txt

# 4. .env
if [ ! -f ".env" ]; then
    cp env_example.txt .env
    echo "→ Created .env from env_example.txt — edit DATABASE_URL if needed."
else
    echo "→ .env already exists, skipping."
fi

# 5. Directories
mkdir -p reports ml/emotion/model_weights /tmp/classsense_uploads

# 6. Model weights check
WEIGHTS="ml/emotion/model_weights/classsense_mobilenetv2.pth"
if [ ! -f "$WEIGHTS" ]; then
    echo ""
    echo "⚠  Model weights not found at: $WEIGHTS"
    echo "   Copy your Colab export:"
    echo "     classsense_BEST.pth  →  $WEIGHTS"
    echo "   The API will start but return neutral predictions until you add the file."
    echo ""
else
    echo "✅ Model weights found."
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Start PostgreSQL (if not running via Docker):"
echo "  docker run -d --name classsense-pg \\"
echo "    -e POSTGRES_DB=classsense_db \\"
echo "    -e POSTGRES_USER=classsense_user \\"
echo "    -e POSTGRES_PASSWORD=classsense_pass \\"
echo "    -p 5432:5432 postgres:15-alpine"
echo ""
echo "Start the API:"
echo "  source venv/bin/activate   # Windows: .\\venv\\Scripts\\Activate.ps1"
echo "  uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Swagger UI → http://localhost:8000/docs"
echo "Health     → http://localhost:8000/health"
