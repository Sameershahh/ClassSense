# ClassSense Backend

## Overview
ClassSense is a classroom engagement and emotion monitoring system. The backend provides a FastAPI service that:
- Authenticates users via JWT tokens.
- Manages session lifecycles (create, list, retrieve, delete, end).
- Accepts video uploads, image uploads, and real‑time frame streams.
- Runs a PyTorch based EfficientNet‑B0 (or compatible) model to infer student engagement, emotion, and gaze.
- Stores lightweight analytics per frame in a SQLite database.
- Generates PDF and CSV reports summarising a session.

The backend is deliberately lightweight: raw video frames are never persisted, only numerical analytics are saved. All endpoints (except health) require a Bearer token.

## Repository Structure
```
ClassSense_backend/
├─ backend/                     # FastAPI application
│   ├─ routers/                 # API route definitions
│   │   └─ sessions.py          # Session CRUD and WebSocket stream
│   ├─ services/                # Core services (MLRunner, etc.)
│   │   └─ ml_runner.py
│   ├─ auth.py                  # JWT authentication utilities
│   ├─ database.py              # SQLAlchemy session & models
│   └─ main.py                  # FastAPI entry point
├─ ml/                         # Machine‑learning components
│   ├─ emotion/                 # Classifier and model weights
│   │   ├─ classifier.py        # Dynamic model loading
│   │   └─ model_weights/       # .pth files (ignored by .gitignore)
│   ├─ engagement/              # Engagement scoring utilities
│   └─ gaze/                    # Gaze estimation utilities
├─ ip_camera_relay.py          # Helper script to stream webcam/IP‑camera frames
├─ requirements.txt            # Python dependencies
├─ .gitignore                  # Excludes large files, env, logs, etc.
└─ README.md                   # This document
```

## Prerequisites
- **Operating System**: Windows 10/11 (tested). Linux/macOS are also supported.
- **Python**: 3.11 or newer.
- **Virtual Environment** (recommended): `python -m venv venv`
- **CUDA** (optional): If you have an NVIDIA GPU and install `torch` with CUDA, inference will be accelerated.

## Installation
```bash
# Clone the repository (already done in your workspace)
# cd ClassSense_backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate   # PowerShell/MacOS: source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```
The `requirements.txt` currently contains only the packages required for the backend and the ML pipeline (FastAPI, SQLAlchemy, OpenCV, PyTorch, etc.). Unused packages have been removed.

## Configuration
Environment variables can be defined in a `.env` file at the project root (the file is ignored by git). The following variables are recognised:
- `SECRET_KEY` – JWT secret (default provided for development). Replace with a strong secret in production.
- `ACCESS_TOKEN_EXPIRE_MINUTES` – Token lifetime in minutes (default 480 = 8 h).
- `DATABASE_URL` – SQLite path (`sqlite:///./classsense_dev.db` by default).
- Any other variables required by your chosen IP camera (e.g., RTSP credentials) are handled directly in the `ip_camera_relay.py` script.

## Running the Backend
```bash
# Ensure the virtual environment is active
venv\Scripts\activate

# Start the server (development mode, auto‑reload)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
The API will be reachable at `http://localhost:8000`. Swagger/OpenAPI documentation is available at `http://localhost:8000/docs`.

## Authentication
1. **Login** – `POST /auth/token` with form data `username` and `password`. The default users are:
   - Instructor: `instructor@classsense.com` / `instructor123`
   - Admin: `admin@classsense.com` / `admin123`
2. The endpoint returns a JSON payload containing `access_token` and `token_type` (`bearer`).
3. Include the token in the `Authorization` header for all protected calls:
   ```http
   Authorization: Bearer <access_token>
   ```
   For convenience, the backend also accepts a `?token=` query parameter for direct report downloads (see **Report Generation**).

## API Endpoints
### Session Management
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/sessions/` | Create a new session and initialise the ML pipeline. Returns `session_id`.
| `GET`  | `/api/sessions/` | List sessions, optionally filtered by `status`.
| `GET`  | `/api/sessions/{session_id}` | Retrieve details of a specific session.
| `DELETE`| `/api/sessions/{session_id}` | Delete a session and all associated analytics.
| `POST` | `/api/sessions/{session_id}/upload-video` | Upload a prerecorded classroom video for batch processing.
| `POST` | `/api/sessions/{session_id}/upload-image` | Upload a single image for instant analysis.
| `POST` | `/api/sessions/{session_id}/end` | Mark the session as completed, compute summary statistics, and make reports available.
| `POST` | `/api/sessions/{session_id}/stream` *(WebSocket)* | Real‑time streaming endpoint. Clients send JPEG bytes; the server returns a JSON payload containing engagement metrics after each frame.

### Analytics
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/analytics/model-status` | Verify that the ML model is loaded correctly.
| `GET` | `/api/analytics/{session_id}/summary` | Aggregated summary after a session ends.
| `GET` | `/api/analytics/{session_id}/timeseries` | Per‑frame engagement time‑series.
| `GET` | `/api/analytics/{session_id}/report/pdf?token=` | Download a PDF report for the session.
| `GET` | `/api/analytics/{session_id}/report/csv?token=` | Download a CSV export of the time‑series data.
| `GET` | `/api/analytics/course/{course_name}` | Cross‑session engagement trends for a specific course.

### Health
`GET /health` – Simple health‑check endpoint.

## Real‑Time Streaming
The backend implements a WebSocket endpoint at:
```
ws://<host>:<port>/api/sessions/{session_id}/stream
```
Clients must send raw JPEG bytes (e.g., a webcam frame) and will receive a JSON response after each frame, for example:
```json
{
  "engagement_pct": 74.2,
  "student_count": 1,
  "distribution": {"attentive": 1, "confused": 0, "distracted": 0}
}
```
The server processes frames in a separate thread to keep the event loop responsive.

### Using the Provided Relay Script
`ip_camera_relay.py` is a convenience script that:
1. Logs in and obtains a JWT token.
2. Creates a new session automatically.
3. Captures frames from either:
   - A local USB webcam (`CAMERA_SOURCE = 0` or another index).
   - An IP camera via RTSP (`CAMERA_SOURCE = "rtsp://user:pass@192.168.x.x:554/stream"`).
4. Streams frames to the WebSocket endpoint.
5. Prints direct download links for PDF and CSV reports, including the token as a query parameter.

To use an IP camera, edit lines 14‑16 of the script and replace the example URL with your camera’s RTSP address.

## Generating Reports
After ending a session (either via the `POST /api/sessions/{session_id}/end` endpoint or automatically when the relay script finishes), the backend stores aggregated statistics. Reports can be retrieved with the URLs printed by the relay script or via the Swagger UI. Because the URLs include the JWT token, they work without additional headers.

## Testing
1. **Unit Tests** – The repository includes a `tests/` directory (not shown here) that exercises each endpoint with the FastAPI `TestClient`. Run them with:
   ```bash
   pytest
   ```
2. **Manual Test** – Start the server, run `ip_camera_relay.py`, watch the console output, press `Ctrl+C` to stop, and open the printed PDF/CSV links in a browser.

## Dependency Management
All unnecessary packages have been removed from `requirements.txt`. The current list is:
```
fastapi==0.110.0
uvicorn==0.29.0
sqlalchemy==2.0.28
pydantic==2.6.3
python-multipart==0.0.9
python-jose==3.3.0
passlib[bcrypt]==1.7.4
opencv-python==4.9.0.80
torch==2.2.0
numpy==1.26.4
```
If you need CUDA support, reinstall `torch` with the appropriate wheel from the PyTorch website.

## Contribution Guidelines
- Fork the repository and create a feature branch.
- Follow the existing coding style (type hints, docstrings, logging).
- Run the full test suite before submitting a PR.
- Keep the `.gitignore` up‑to‑date to avoid committing large model files or logs.

## License
This project is licensed under the MIT License.

---
*End of README*
