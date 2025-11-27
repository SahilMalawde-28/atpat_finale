#!/usr/bin/env python3
"""
proctor.py
- Opens the webcam (single owner)
- Streams MJPEG at http://127.0.0.1:5000/video_feed (Flask)
- Runs detection polling every 5s (NoFace/MultiFace/OffGaze)
- Runs audio monitor and alt-key monitor
- Adds typing behavior tracking (WPM, backspace ratio, constant typing)
- Emits JSON events on stdout for Electron to pick up
- On stdin "stop" -> stops and writes report.json + report.pdf
"""
import sys, os, time, json, threading, uuid
from pathlib import Path

try:
    import cv2, numpy as np, sounddevice as sd
    from pynput import keyboard
    from flask import Flask, Response
    from fpdf import FPDF
except Exception as e:
    sys.stderr.write(f"IMPORT_ERROR: {e}\n")
    sys.stderr.flush()
    sys.exit(1)

# ---------- configuration ----------
HOST = "127.0.0.1"
PORT = 5000
POLL_INTERVAL = 5.0
DISPLAY_WIDTH = 640
OUT_DIR = Path(__file__).parent.parent / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- reporting state ----------
report = {
    "start_time": time.ctime(),
    "end_time": None,

    # Face/Gaze/Audience-related
    "no_face": 0,
    "multi_face": 0,
    "off_gaze": 0,

    # Keyboard and Interaction
    "alt_tab": 0,
    "typing_events": 0,
    "typing_flags": 0,
    "avg_wpm": 0,
    "backspace_ratio": 0,

    # Detailed typing telemetry
    "mean_interval": 0,
    "std_interval": 0,
    "key_density": 0,
    "burst_count": 0,
    "idle_time_ratio": 0,
    "constant_typing_flags": 0,

    # Audio / environment
    "audio_events": 0,

    # Proofs / screenshots / evidences
    "proofs": []
}

def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

# ---------- camera + flask ----------
app = Flask(__name__)
camera = None
camera_lock = threading.Lock()
last_frame_jpeg = None
running = True

def init_camera(index=0):
    global camera
    camera = cv2.VideoCapture(index)
    if not camera.isOpened():
        for i in range(1, 5):
            camera = cv2.VideoCapture(i)
            if camera.isOpened():
                break
    if not camera.isOpened():
        send({"type": "error", "msg": "Camera not available"})
        return False
    try:
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    except:
        pass
    return True

def frame_grabber():
    global last_frame_jpeg, camera
    while running:
        if camera is None:
            time.sleep(0.1)
            continue
        ret, frame = camera.read()
        if not ret:
            time.sleep(0.05)
            continue
        frame_small = cv2.resize(frame, (DISPLAY_WIDTH, int(frame.shape[0] * DISPLAY_WIDTH / frame.shape[1])))
        _, buf = cv2.imencode('.jpg', frame_small, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        with camera_lock:
            last_frame_jpeg = buf.tobytes()
        time.sleep(0.02)

def gen_frames():
    global last_frame_jpeg
    while running:
        with camera_lock:
            frame = last_frame_jpeg
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.05)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ---------- detection loop ----------
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def save_proof(original_frame, prefix):
    fname = f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:6]}.jpg"
    path = OUT_DIR / fname
    cv2.imwrite(str(path), original_frame)
    return str(path)

def detection_loop():
    global last_frame_jpeg, camera
    consecutive_no_face = 0
    while running:
        if camera is None:
            time.sleep(POLL_INTERVAL)
            continue
        ret, frame = camera.read()
        if not ret or frame is None:
            h, w = 480, 640
            frame = np.zeros((h, w, 3), dtype=np.uint8)
            path = save_proof(frame, "camera_off")
            report['proofs'].append({"type": "CameraOff", "path": path, "ts": int(time.time()*1000)})
            send({"type": "flag", "flag": {"type": "CameraOff", "detail": "Camera not accessible", "proof": path}, "ts": int(time.time()*1000)})
            time.sleep(POLL_INTERVAL)
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (0,0), fx=0.5, fy=0.5)
        faces = face_cascade.detectMultiScale(small, scaleFactor=1.08, minNeighbors=5, minSize=(60,60))
        nfaces = len(faces)
        flags = []
        if nfaces == 0:
            consecutive_no_face += 1
            if consecutive_no_face >= 2:
                path = save_proof(frame, "noface")
                report['no_face'] += 1
                report['proofs'].append({"type": "NoFace", "path": path, "ts": int(time.time()*1000)})
                flags.append({"type": "NoFace", "detail": "No face detected", "proof": path})
                consecutive_no_face = 0
        elif nfaces > 1:
            path = save_proof(frame, "multiface")
            report['multi_face'] += 1
            report['proofs'].append({"type": "MultiFace", "path": path, "ts": int(time.time()*1000)})
            flags.append({"type": "MultiFace", "detail": f"{nfaces} faces detected", "proof": path})
            consecutive_no_face = 0
        else:
            consecutive_no_face = 0
            (x, y, w, h) = faces[0]
            fx = 2.0
            cx = int((x + w/2) * fx)
            frame_w = frame.shape[1]
            if abs(cx - frame_w/2) > frame_w * 0.35:
                path = save_proof(frame, "offgaze")
                report['off_gaze'] += 1
                report['proofs'].append({"type": "OffGaze", "path": path, "ts": int(time.time()*1000)})
                flags.append({"type": "OffGaze", "detail": "User looking away", "proof": path})
        for f in flags:
            send({"type": "flag", "flag": f, "ts": int(time.time()*1000)})
        for _ in range(int(POLL_INTERVAL*10)):
            if not running:
                break
            time.sleep(0.1)

# ---------- audio monitor ----------
def audio_loop(threshold=0.3, interval=0.5):
    def callback(indata, frames, time_, status):
        if not running:
            return
        volume = float(np.linalg.norm(indata)) / frames
        if volume > threshold:
            report['audio_events'] += 1
            send({
                "type": "flag",
                "flag": {"type": "Audio", "detail": f"Volume {volume:.2f}"},
                "ts": int(time.time() * 1000)
            })

    try:
        with sd.InputStream(callback=callback):
            while running:
                time.sleep(interval)
    except Exception as e:
        send({"type": "info", "msg": f"Audio error: {str(e)}"})




# ---------- typing monitor ----------
key_count = 0
backspaces = 0
typing_start_time = time.time()
typing_times = []
last_typing_time = 0
lock_typing = threading.Lock()

def on_typing_key(key):
    global key_count, backspaces, typing_times, last_typing_time
    with lock_typing:
        now = time.time()
        typing_times.append(now)
        report["typing_events"] += 1
        key_count += 1
        last_typing_time = now

        # Detect backspace
        if key == keyboard.Key.backspace:
            backspaces += 1

        


def on_release(key):
    if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
        report["ctrl_pressed"] = False


def typing_monitor_loop():
    global key_count, backspaces, typing_times, last_typing_time
    while running:
        time.sleep(15)
        with lock_typing:
            elapsed = time.time() - typing_start_time
            words = key_count / 5
            wpm = words / (elapsed / 60) if elapsed > 0 else 0
            ratio = backspaces / key_count if key_count > 0 else 0

            report["avg_wpm"] = round(wpm, 2)
            report["backspace_ratio"] = round(ratio, 2)

            # Only analyze last 50 keypresses for pattern stability
            if len(typing_times) > 5:
                recent_times = typing_times[-50:]
                intervals = np.diff(recent_times)
                mean_int = np.mean(intervals)
                std_int = np.std(intervals)
                report["mean_interval"] = round(float(mean_int), 3)
                report["std_interval"] = round(float(std_int), 3)

                # Detect constant typing speed (possible bot or pasted pattern)
                # But ignore if user is idle or few keys typed recently
                time_since_last_key = time.time() - recent_times[-1]
                recent_keystrokes = len(recent_times)

                if (
                    std_int < 0.05                 # very consistent intervals
                    and recent_keystrokes >= 10    # at least 10 keypresses in window
                    and time_since_last_key < 10   # must be active recently
                ):
                    report["typing_flags"] += 1
                    report["constant_typing_flags"] = report.get("constant_typing_flags", 0) + 1
                    send({
                        "type": "flag",
                        "flag": {
                            "type": "Typing",
                            "detail": "Constant typing speed detected"
                        },
                        "ts": int(time.time() * 1000)
                    })

                # Burst detection (typing >3 keys within 0.2 sec)
                burst_intervals = intervals[intervals < 0.2]
                report["burst_count"] = len(burst_intervals)

                # Key density = keys per second (avg over last window)
                if len(typing_times) > 1:
                    total_time = typing_times[-1] - typing_times[0]
                    report["key_density"] = round(len(typing_times) / total_time, 3) if total_time > 0 else 0

                # Idle time ratio = (total idle duration) / total elapsed
                idle_durations = intervals[intervals > 2.0]
                idle_total = np.sum(idle_durations) if len(idle_durations) > 0 else 0
                report["idle_time_ratio"] = round(idle_total / elapsed, 3) if elapsed > 0 else 0

            # Keep typing buffer small
            typing_times = typing_times[-100:]


def on_press(key):
    try:
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            report['alt_tab'] += 1
            send({"type": "flag", "flag": {"type": "AltPressed", "detail": "Alt key pressed"}, "ts": int(time.time()*1000)})
        else:
            on_typing_key(key)
    except Exception:
        pass

def on_release(key):
    pass

# ---------- report generation ----------
def generate_pdf(report_json_path, pdf_path):
    # Always regenerate fresh PDF
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    with open(report_json_path, 'r') as f:
        r = json.load(f)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ---------- Header ----------
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Proctor Report", ln=True, align='C')
    pdf.ln(6)

    pdf.set_font("Arial", "", 12)

    # ---------- All Metrics ----------
    metrics = [
        "start_time", "end_time",
        "no_face", "multi_face", "off_gaze",
        "alt_tab", "audio_events",
        "typing_events", "avg_wpm", "backspace_ratio", "typing_flags",
        "mean_interval", "std_interval", "key_density", "burst_count",
        "idle_time_ratio", "constant_typing_flags"
    ]

    for k in metrics:
        pdf.cell(0, 8, f"{k}: {r.get(k, 0)}", ln=True)

    pdf.ln(10)

    # ---------- Proofs Section ----------
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Proofs:", ln=True)
    pdf.ln(6)

    pdf.set_font("Arial", "", 11)
    proofs = r.get("proofs", [])

    if not proofs:
        pdf.cell(0, 8, "No proofs recorded.", ln=True)
    else:
        for p in proofs:
            path = p.get("path")
            label = p.get("type", "img")
            timestamp = p.get("ts", "")

            pdf.cell(0, 6, f"{label} ({timestamp})", ln=True)
            pdf.ln(2)

            if path and os.path.exists(path):
                try:
                    pdf.image(path, w=120)
                    pdf.ln(8)
                except Exception as e:
                    pdf.cell(0, 6, f"(Image load failed: {e})", ln=True)
                    pdf.ln(4)
            else:
                pdf.cell(0, 6, f"{label} - (missing or deleted)", ln=True)
                pdf.ln(4)

    # ---------- Save File ----------
    pdf.output(str(pdf_path))
    print(f"✅ PDF generated successfully at: {pdf_path}")


# ---------- stdin listener ----------
def stdin_listener():
    while True:
        line = sys.stdin.readline()
        if not line:
            time.sleep(0.1)
            continue
        try:
            obj = json.loads(line.strip())
            if obj.get("cmd") == "stop":
                stop_proctor()
                break
        except Exception:
            if line.strip().lower() == "stop":
                stop_proctor()
                break

# ---------- graceful stop ----------
keyboard_listener = None

def stop_proctor():
    global running
    if not running:
        return
    running = False
    report['end_time'] = time.ctime()
    report_path = OUT_DIR / "report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    pdf_path = OUT_DIR / "report.pdf"
    try:
        generate_pdf(report_path, pdf_path)
    except Exception as e:
        send({"type": "info", "msg": f"PDF generation error: {str(e)}"})
    send({"type": "info", "msg": f"Report saved: {report_path}, PDF: {pdf_path}"})
    try:
        send({"type": "final_report", "data": report})
    except Exception as e:
        send({"type": "error", "msg": f"Failed to emit final report: {str(e)}"})

# ---------- main ----------
def main():
    global running, camera, keyboard_listener
    ok = init_camera()
    if not ok:
        send({"type": "error", "msg": "No camera found. Exiting."})
        return
    t_grab = threading.Thread(target=frame_grabber, daemon=True); t_grab.start()
    t_flask = threading.Thread(target=lambda: app.run(host=HOST, port=PORT, debug=False, use_reloader=False), daemon=True); t_flask.start()
    send({"type": "info", "msg": f"Video stream running at http://{HOST}:{PORT}/video_feed"})
    t_detect = threading.Thread(target=detection_loop, daemon=True); t_detect.start()
    t_audio = threading.Thread(target=audio_loop, daemon=True); t_audio.start()
    t_typing = threading.Thread(target=typing_monitor_loop, daemon=True); t_typing.start()
    keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    keyboard_listener.start()
    t_stdin = threading.Thread(target=stdin_listener, daemon=True); t_stdin.start()
    try:
        while running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_proctor()
    try:
        camera.release()
    except:
        pass
    try:
        keyboard_listener.stop()
    except:
        pass
    send({"type": "info", "msg": "Proctor exited"})

if __name__ == "__main__":
    main()

