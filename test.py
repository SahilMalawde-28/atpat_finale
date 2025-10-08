#!/usr/bin/env python3
import cv2, numpy as np, time, threading, json, uuid, os
from pathlib import Path
from pynput import keyboard
import sounddevice as sd
from fpdf import FPDF

OUT_DIR = Path(__file__).parent.parent / "out"
OUT_DIR.mkdir(exist_ok=True)

def send(obj):
    print(json.dumps(obj), flush=True)

# --------------------------
# Report
# --------------------------
report = {
    "no_face": 0,
    "multi_face": 0,
    "off_gaze": 0,
    "alt_tab": 0,
    "audio_events": 0,
    "proofs": []
}

# --------------------------
# Camera detection
# --------------------------
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
cam_running = True
poll_interval = 5  # seconds between detection

def save_image(frame, prefix):
    fname = f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:6]}.jpg"
    path = OUT_DIR / fname
    cv2.imwrite(str(path), frame)
    return str(path)

def camera_loop():
    global cam_running
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        send({'type':'info','msg':'camera not available'})
        return

    last_poll = 0
    flags_to_display = []
    while cam_running:
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80,80))
        nfaces = len(faces)

        current_time = time.time()
        flags_to_display.clear()

        if current_time - last_poll >= poll_interval:
            last_poll = current_time
            # -----------------------
            # Check flags
            # -----------------------
            if nfaces == 0:
                path = save_image(frame, 'noface')
                report['no_face'] += 1
                report['proofs'].append(path)
                flags_to_display.append({'type':'NoFace','detail':'No face detected','proof':path})
                send({'type':'flag','flag':flags_to_display[-1],'ts':int(time.time()*1000)})
            elif nfaces > 1:
                path = save_image(frame, 'multiface')
                report['multi_face'] += 1
                report['proofs'].append(path)
                flags_to_display.append({'type':'MultiFace','detail':f'{nfaces} faces detected','proof':path})
                send({'type':'flag','flag':flags_to_display[-1],'ts':int(time.time()*1000)})
            else:
                # single face: check off-gaze
                x,y,w,h = faces[0]
                cx = x + w/2
                frame_w = frame.shape[1]
                if abs(cx - frame_w/2) > frame_w*0.35:
                    path = save_image(frame, 'offgaze')
                    report['off_gaze'] += 1
                    report['proofs'].append(path)
                    flags_to_display.append({'type':'OffGaze','detail':'Looking away','proof':path})
                    send({'type':'flag','flag':flags_to_display[-1],'ts':int(time.time()*1000)})

        # -----------------------
        # Draw faces and flags
        # -----------------------
        for (x,y,w,h) in faces:
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

        y0 = 30
        for f in flags_to_display:
            cv2.putText(frame, f"{f['type']}: {f['detail']}", (10,y0), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255),2)
            y0 += 30

        # Resize for smooth display
        disp_frame = cv2.resize(frame, (640,480))
        cv2.imshow("Proctor Feed", disp_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cam_running = False
            break

    cap.release()
    cv2.destroyAllWindows()

# --------------------------
# Keyboard monitoring
# --------------------------
def on_press(key):
    try:
        if key in [keyboard.Key.alt_l, keyboard.Key.alt_r]:
            report['alt_tab'] += 1
            send({'type':'flag','flag':{'type':'AltTab','detail':'Alt key pressed','ts':int(time.time()*1000)}})
    except:
        pass

kb_listener = keyboard.Listener(on_press=on_press)

# --------------------------
# Audio monitoring
# --------------------------
def audio_loop(threshold=0.3, interval=0.5):
    def callback(indata, frames, time_, status):
        vol = float(np.linalg.norm(indata))/frames
        if vol > threshold:
            report['audio_events'] += 1
            send({'type':'flag','flag':{'type':'Audio','detail':f'Volume {vol:.2f}','ts':int(time.time()*1000)}})
    try:
        with sd.InputStream(callback=callback):
            while cam_running:
                time.sleep(interval)
    except Exception as e:
        send({'type':'info','msg':f'Audio error: {e}'})

# --------------------------
# PDF report
# --------------------------
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,"Proctor Report",ln=1)
    pdf.set_font("Arial","",12)
    pdf.ln(5)
    pdf.cell(0,10,f"NoFace: {report['no_face']}",ln=1)
    pdf.cell(0,10,f"MultiFace: {report['multi_face']}",ln=1)
    pdf.cell(0,10,f"OffGaze: {report['off_gaze']}",ln=1)
    pdf.cell(0,10,f"AltTab pressed: {report['alt_tab']}",ln=1)
    pdf.cell(0,10,f"Audio events: {report['audio_events']}",ln=1)
    pdf.ln(5)
    pdf.cell(0,10,"Proof Images:",ln=1)
    for img in report['proofs']:
        pdf.cell(0,5,img,ln=1)
    path = OUT_DIR / "proctor_report.pdf"
    pdf.output(str(path))
    send({'type':'info','msg':f'PDF report saved at {path}'})
    return str(path)

# --------------------------
# Main
# --------------------------
def main():
    send({'type':'info','msg':'Proctor started'})
    kb_listener.start()
    cam_thread = threading.Thread(target=camera_loop, daemon=True)
    cam_thread.start()
    audio_thread = threading.Thread(target=audio_loop, daemon=True)
    audio_thread.start()

    try:
        while cam_running:
            time.sleep(1)
    except KeyboardInterrupt:
        cam_running = False

    # Stop threads
    kb_listener.stop()
    cam_thread.join()
    audio_thread.join()

    pdf_path = generate_pdf()
    send({'type':'info','msg':f'Report generated: {pdf_path}'})

if __name__=="__main__":
    main()

