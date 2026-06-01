import cv2
import asyncio
import websockets
import json
import sys

async def stream_camera():
    # ── Configuration ──────────────────────────────────────────────────────────
    # Switch between webcam index (e.g. 0) or physical IP RTSP url
    # Examples:
    #   CAMERA_SOURCE = 0                                       # Webcam
    #   CAMERA_SOURCE = "rtsp://admin:pass@192.168.1.100/h264"  # IP Camera
    CAMERA_SOURCE = 0
    
    # Session ID to stream under (make sure you started this session in the UI first!)
    SESSION_ID = 1
    
    BACKEND_WS_URL = f"ws://localhost:8000/api/sessions/{SESSION_ID}/stream"
    # ─────────────────────────────────────────────────────────────────────────────

    print(f"[*] Initializing camera source: {CAMERA_SOURCE}...")
    cap = cv2.VideoCapture(CAMERA_SOURCE)
    
    if not cap.isOpened():
        print(f"[!] Error: Could not open camera source {CAMERA_SOURCE}.")
        sys.exit(1)
        
    print(f"[*] Connecting to ClassSense WebSocket: {BACKEND_WS_URL}...")
    try:
        async with websockets.connect(BACKEND_WS_URL) as ws:
            print("[+] Connection established! Press Ctrl+C to stop streaming.")
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print("[!] Camera stream interrupted.")
                    break
                    
                # Downsample slightly to 640x480 for ultra-low latency network transfer
                frame_resized = cv2.resize(frame, (640, 480))
                
                # Compress frame to JPEG
                _, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
                
                # Send raw JPEG bytes to backend WebSocket
                await ws.send(buffer.tobytes())
                
                # Receive real-time engagement calculations back from the server
                response = await ws.recv()
                metrics = json.loads(response)
                
                print(f"[Live Analytics] Engagement: {metrics.get('engagement_pct', 0.0)}% | "
                      f"Attentive: {metrics.get('distribution', {}).get('attentive', 0)} | "
                      f"Confused: {metrics.get('distribution', {}).get('attentive', 0)} | "
                      f"Distracted: {metrics.get('distribution', {}).get('attentive', 0)}")
                
                # Control the stream rate (~12 FPS) to avoid network buffer bloat
                await asyncio.sleep(0.08)
                
    except KeyboardInterrupt:
        print("\n[+] Stream stopped by user.")
    except Exception as e:
        print(f"\n[!] Connection error: {e}")
    finally:
        cap.release()
        print("[*] Camera source released.")

if __name__ == "__main__":
    try:
        asyncio.run(stream_camera())
    except KeyboardInterrupt:
        pass
