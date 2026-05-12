# ClassSense Backend — Setup & Usage Guide

**FYP 2025-2026 | Iqra University CS**
Sameer Shah (62662) & Ismail Haroon (63188) | Supervisor: Ms. Zuha Soomro

---

## Directory Structure

```
classsense/
├── backend/
│   ├── __init__.py
│   ├── main.py              ← FastAPI app entry point
│   ├── database.py          ← SQLAlchemy setup
│   ├── auth.py              ← JWT authentication
│   ├── models/
│   │   ├── session.py       ← ORM models (Session, FrameAnalytic, SessionSummary)
│   │   └── schemas.py       ← Pydantic request/response schemas
│   ├── routers/
│   │   ├── sessions.py      ← Session lifecycle endpoints
│   │   └── analytics.py     ← Analytics + report endpoints
│   └── services/
│       ├── ml_runner.py     ← ML pipeline bridge (singleton)
│       └── report.py        ← PDF + CSV generation
├── ml/
│   └── emotion/
│       └── model_weights/
│           └── classsense_mobilenetv2.pth   ← copy from Colab here
├── reports/                 ← generated PDFs and CSVs saved here
├── .env                     ← copy from .env.example and fill in
├── .env.example
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## Step 1 — Prerequisites

```bash
# Python 3.10
python3.10 --version

# PostgreSQL running locally or via Docker
sudo service postgresql start     # Linux/WSL
brew services start postgresql    # Mac
```

---

## Step 2 — Install Dependencies

```bash
cd classsense
python3.10 -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

---

## Step 3 — Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql://classsense_user:classsense_pass@localhost:5432/classsense_db
SECRET_KEY=your-random-32-char-secret-key-here
```

---

## Step 4 — Set Up PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE classsense_db;
CREATE USER classsense_user WITH PASSWORD 'classsense_pass';
GRANT ALL PRIVILEGES ON DATABASE classsense_db TO classsense_user;
\q
```

Tables are created automatically on first startup — no migrations needed.

---

## Step 5 — Copy Your Trained Model

After running the Colab training notebook, copy the exported `.pth` file:

```
Google Drive: ClassSense_Model/classsense_BEST.pth
         ↓
Local path:   ml/emotion/model_weights/classsense_mobilenetv2.pth
```

---

## Step 6 — Start the Server

```bash
# From project root (classsense/)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000/docs** — you will see the Swagger UI with all endpoints.

---

## Step 7 — Test the API Flow

### 1. Login
```bash
curl -X POST http://localhost:8000/auth/token \
  -F "username=instructor@classsense.com" \
  -F "password=instructor123"
```
Copy the `access_token` from the response.

### 2. Start a session
```bash
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"course_name": "CS101", "time_slot": "Mon 10:00 AM"}'
```
Note the `session_id`.

### 3. Upload a classroom video
```bash
curl -X POST http://localhost:8000/api/sessions/1/upload-video \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/classroom_video.mp4"
```
This runs the full ML pipeline. Wait for processing to complete.

### 4. End the session
```bash
curl -X POST http://localhost:8000/api/sessions/1/end \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Download PDF report
```bash
curl -X GET http://localhost:8000/api/analytics/1/report/pdf \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o session_1_report.pdf
```

---

## API Endpoints Reference

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | `/auth/token` | No | Login, get JWT |
| GET | `/auth/me` | Yes | Current user info |
| POST | `/api/sessions/` | Yes | Start new session |
| GET | `/api/sessions/` | Yes | List all sessions |
| GET | `/api/sessions/{id}` | Yes | Get one session |
| DELETE | `/api/sessions/{id}` | Yes | Delete session |
| POST | `/api/sessions/{id}/upload-video` | Yes | Upload + process video |
| POST | `/api/sessions/{id}/upload-image` | Yes | Upload + analyse image |
| POST | `/api/sessions/{id}/end` | Yes | End session, compute summary |
| GET | `/api/analytics/{id}/summary` | Yes | Session summary stats |
| GET | `/api/analytics/{id}/timeseries` | Yes | Per-frame chart data |
| GET | `/api/analytics/{id}/report/pdf` | Yes | Download PDF report |
| GET | `/api/analytics/{id}/report/csv` | Yes | Download CSV export |
| GET | `/api/analytics/course/{name}` | Yes | Course trend analytics |
| GET | `/api/analytics/model-status` | Yes | ML model health check |
| GET | `/health` | No | API health check |

---

## Docker Deployment

```bash
# Build and start everything (DB + backend + frontend)
docker-compose up --build

# Background mode
docker-compose up -d

# View backend logs
docker-compose logs -f backend

# Stop everything
docker-compose down

# Stop and delete database volume (full reset)
docker-compose down -v
```

After `docker-compose up`, open:
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

---

## Default Credentials

| Email | Password | Role |
|-------|----------|------|
| instructor@classsense.com | instructor123 | instructor |
| admin@classsense.com | admin123 | admin |

Change these in `backend/auth.py` before deployment.

---

## Checklist for FYP Submission

- [ ] `GET /health` returns `{"status": "ok", "model_loaded": true}`
- [ ] Full video upload → end session → PDF download flow works
- [ ] Session history visible at `GET /api/sessions/`
- [ ] Course analytics visible at `GET /api/analytics/course/{name}`
- [ ] `docker-compose up --build` starts all three services cleanly
- [ ] No names or face images in the database (privacy check)
