import cv2
import asyncio
import websockets
import json
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────
# Switch between webcam index (e.g. 0) or physical IP RTSP url
# Examples:
#   CAMERA_SOURCE = 0                                       # Webcam
#   CAMERA_SOURCE = "rtsp://admin:pass@192.168.1.100/h264"  # IP Camera
CAMERA_SOURCE = 0

BACKEND_HTTP_URL = "http://localhost:8000"
BACKEND_WS_URL   = "ws://localhost:8000"
USERNAME         = "instructor@classsense.com"
PASSWORD         = "instructor123"
# ─────────────────────────────────────────────────────────────────────────────

def get_auth_token():
    """Login to FastAPI and retrieve a JWT Bearer token using urllib."""
    url = f"{BACKEND_HTTP_URL}/auth/token"
    payload = urllib.parse.urlencode({
        "username": USERNAME,
        "password": PASSWORD
    }).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            return data["access_token"]
    except urllib.error.URLError as e:
        print(f"[!] Authentication failed: {e}. Is the server running on {BACKEND_HTTP_URL}?")
        sys.exit(1)

def create_new_session(token: str):
    """Dynamically register a new session in the database."""
    url = f"{BACKEND_HTTP_URL}/api/sessions/"
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    payload = json.dumps({
        "course_name": f"Live Camera Test ({timestamp})",
        "time_slot": "Real-time stream",
        "instructor_id": 1
    }).encode("utf-8")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            return data["session_id"], data["course_name"]
    except urllib.error.URLError as e:
        print(f"[!] Failed to create new session: {e}")
        sys.exit(1)

def end_session(token: str, session_id: int):
    """End the session and trigger report generation on the backend."""
    url = f"{BACKEND_HTTP_URL}/api/sessions/{session_id}/end"
    headers = {"Authorization": f"Bearer {token}"}
    req = urllib.request.Request(url, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            print(f"[+] Session {session_id} ended successfully on the backend.")
    except urllib.error.URLError as e:
        print(f"[!] Failed to end session {session_id}: {e}")

async def stream_camera():
    print("[*] Logging in to ClassSense backend...")
    token = get_auth_token()
    
    print("[*] Creating a brand-new live session...")
    session_id, session_name = create_new_session(token)
    print(f"[+] Created Session ID: {session_id} | Name: '{session_name}'")
    
    print(f"[*] Initializing camera source: {CAMERA_SOURCE}...")
    cap = cv2.VideoCapture(CAMERA_SOURCE)
    
    if not cap.isOpened():
        print(f"[!] Error: Could not open camera source {CAMERA_SOURCE}.")
        sys.exit(1)
        
    ws_endpoint = f"{BACKEND_WS_URL}/api/sessions/{session_id}/stream"
    print(f"[*] Connecting to ClassSense WebSocket: {ws_endpoint}...")
    
    try:
        async with websockets.connect(ws_endpoint) as ws:
            print("\n" + "="*50)
            print("🚀 LIVE STREAMING ACTIVE")
            print("Press Ctrl+C in this terminal to STOP the stream and get your report!")
            print("="*50 + "\n")
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print("[!] Camera stream interrupted.")
                    break
                    
                # Downsample to 640x480 for real-time networking speed
                frame_resized = cv2.resize(frame, (640, 480))
                
                # Compress to JPEG
                _, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
                
                # Send raw JPEG bytes
                await ws.send(buffer.tobytes())
                
                # Receive real-time engagement calculations
                response = await ws.recv()
                metrics = json.loads(response)
                
                dist = metrics.get('distribution', {})
                print(f"[Live Session {session_id}] Engagement: {metrics.get('engagement_pct', 0.0)}% | "
                      f"Attentive: {dist.get('attentive', 0)} | "
                      f"Confused: {dist.get('confused', 0)} | "
                      f"Distracted: {dist.get('distracted', 0)}")
                
                # Send at ~12 FPS
                await asyncio.sleep(0.08)
                
    except KeyboardInterrupt:
        print("\n[+] Stream stopped by user.")
    except Exception as e:
        print(f"\n[!] Connection error: {e}")
    finally:
        cap.release()
        print("[*] Camera source released.")
        
        print("\n[*] Finalizing session and saving reports...")
        end_session(token, session_id)
        
        print("\n" + "="*60)
        print("🎉 REPORTS READY FOR DOWNLOAD:")
        print(f"📄 PDF Summary Report:  {BACKEND_HTTP_URL}/api/analytics/{session_id}/report/pdf?token={token}")
        print(f"📊 CSV Data Export:     {BACKEND_HTTP_URL}/api/analytics/{session_id}/report/csv?token={token}")
        print("="*60 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(stream_camera())
    except KeyboardInterrupt:
        pass
