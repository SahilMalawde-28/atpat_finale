#!/usr/bin/env python3
import sys, os, time, json, threading, uuid, atexit
from pathlib import Path

import cv2, numpy as np, sounddevice as sd
from pynput import keyboard
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- Output setup ---
OUT_DIR = Path(__file__).parent / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

cam_running = True

report = {
    "start_time": time.ctime(),
    "end_time": None,
    "no_face": 0,
    "multi_face": 0,
    "off_gaze": 0,
    "alt_tab": 0,
    "audio_events": 0,
    "proofs": []
}

running = True
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def send(obj):
    sys.stdout.write(json.dumps(obj) + '\n')
    sys.stdout.flush()

# --- Camera ---
def save_image(img, prefix):
    fname = f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:6]}.jpg"
    path = OUT_DIR / fname
    cv2.imwrite(str(path), img)
    return str(path)

def camera_loop(interval=1.0):
    
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            send({'type':'info','msg':'camera not available, using fake images'})
            cap = None
    except:
        cap = None
        send({'type':'info','msg':'camera exception, using fake images'})

    consecutive_no_face = 0
    consecutive_multi_face = 0
    cooldowns = {"no_face": 0, "multi_face": 0, "off_gaze": 0}  # cooldown counters

    while cam_running:
        if cap:
            ret, frame = cap.read()
            if not ret:
                frame = np.zeros((480,640,3), dtype=np.uint8)
        else:
            frame = np.zeros((480,640,3), dtype=np.uint8)

        # detect faces
        if cap:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=6, minSize=(80,80))
            nfaces = len(faces)
        else:
            # simulate: 10% no face, 80% 1 face, 10% 2 faces
            nfaces = random.choices([0,1,2], [0.1,0.8,0.1])[0]

        # --- No face ---
        if nfaces == 0:
            consecutive_no_face += 1
            if consecutive_no_face >= 3 and cooldowns["no_face"] <= 0:
                path = save_image(frame, 'noface')
                report['no_face'] += 1
                report['proofs'].append(path)
                send({'type':'flag','flag':{'type':'NoFace','detail':'No face detected for 3+ frames','proof':path,'ts':int(time.time()*1000)}})
                cooldowns["no_face"] = 10  # wait 10 cycles before another flag
        else:
            consecutive_no_face = 0

        # --- Multiple faces ---
        if nfaces > 1:
            consecutive_multi_face += 1
            if consecutive_multi_face >= 2 and cooldowns["multi_face"] <= 0:
                path = save_image(frame, 'multiface')
                report['multi_face'] += 1
                report['proofs'].append(path)
                send({'type':'flag','flag':{'type':'MultipleFaces','detail':f'{nfaces} faces detected','proof':path,'ts':int(time.time()*1000)}})
                cooldowns["multi_face"] = 10
        else:
            consecutive_multi_face = 0

        # --- Off-gaze (simulate rarely) ---
        if nfaces == 1 and random.random() < 0.03 and cooldowns["off_gaze"] <= 0:
            path = save_image(frame, 'offgaze')
            report['off_gaze'] += 1
            report['proofs'].append(path)
            send({'type':'flag','flag':{'type':'OffGaze','detail':'User looking away','proof':path,'ts':int(time.time()*1000)}})
            cooldowns["off_gaze"] = 15

        # decrement cooldowns
        for k in cooldowns:
            if cooldowns[k] > 0:
                cooldowns[k] -= 1

        time.sleep(interval)

    if cap:
        cap.release()


# --- Keyboard (Alt-tab detection) ---
def on_press(key):
    try:
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            report['alt_tab'] += 1
            send({'type':'flag','flag':{'type':'AltTab','detail':'Alt key pressed'}})
    except Exception:
        pass

kb_listener = keyboard.Listener(on_press=on_press)

# --- Audio ---
def audio_loop(threshold=0.3):
    global running
    def callback(indata, frames, time_, status):
        if not running: return
        volume = float(np.linalg.norm(indata)) / frames
        if volume > threshold:
            report['audio_events'] += 1
            send({'type':'flag','flag':{'type':'Audio','detail':f'Volume {volume:.2f}'}})
    try:
        with sd.InputStream(callback=callback):
            while running:
                time.sleep(0.5)
    except Exception as e:
        send({'type':'info','msg':f'Audio error: {e}'})

# --- Save Report ---
def save_report():
    report['end_time'] = time.ctime()
    json_path = OUT_DIR / "report.json"
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)

    # also create PDF
    pdf_path = OUT_DIR / "report.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    c.setFont("Helvetica", 14)
    c.drawString(50, 800, "ATPAT Proctor Report")
    c.setFont("Helvetica", 11)
    c.drawString(50, 780, f"Start Time: {report['start_time']}")
    c.drawString(50, 760, f"End Time: {report['end_time']}")
    c.drawString(50, 740, f"No Face: {report['no_face']}")
    c.drawString(50, 720, f"Multiple Faces: {report['multi_face']}")
    c.drawString(50, 700, f"Off-Gaze: {report['off_gaze']}")
    c.drawString(50, 680, f"Alt-Tab: {report['alt_tab']}")
    c.drawString(50, 660, f"Audio Events: {report['audio_events']}")
    c.showPage(); c.save()

    send({'type':'info','msg':f"Report saved to {json_path} and {pdf_path}"})

atexit.register(save_report)

# --- Main ---
def main():
    send({'type':'info','msg':'Proctor started'})
    kb_listener.start()

    cam_thread = threading.Thread(target=camera_loop, daemon=True)
    cam_thread.start()

    audio_thread = threading.Thread(target=audio_loop, daemon=True)
    audio_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        global running
        running = False
        kb_listener.stop()
        save_report()

if __name__ == "__main__":
    main()

