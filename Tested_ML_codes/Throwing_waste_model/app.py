import cv2
import numpy as np
from flask import Flask, render_template, Response, jsonify
from tensorflow.keras.models import load_model


MODEL_PATH = "models/throwing_waste_model.h5"
model = load_model(MODEL_PATH)

# Labels
CLASS_NAMES = ["NOT_THROWING_WASTE", "THROWING_WASTE"]
IMG_SIZE = 64

# Global detection variable
throwing_detected = False

app = Flask(__name__)

def predict_frame(frame):
    global throwing_detected
    # Preprocess
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, axis=0)

    preds = model.predict(img, verbose=0)[0]
    label_idx = int(1-np.argmax(preds))
    label = CLASS_NAMES[label_idx]

    throwing_detected = (label == "THROWING_WASTE")
    return label, float(preds[label_idx])

def generate_frames():
    cap = cv2.VideoCapture(0)
    #cap=cv2.VideoCapture("demo\istockphoto-1174883746-mp4-480x480-is.mp4")
    while True:
        success, frame = cap.read()
        if not success:
            break

        label, prob = predict_frame(frame)

        # Draw label on video
        color = (0, 0, 255) if label == "THROWING_WASTE" else (0, 255, 0)
        cv2.putText(frame, f"{label} {prob:.2f}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        # Encode and yield frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/control')
def control():
    return render_template('control.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/throwing_status')
def throwing_status():
    return jsonify({"throwing": throwing_detected})

if __name__ == "__main__":
    app.run(debug=True)
