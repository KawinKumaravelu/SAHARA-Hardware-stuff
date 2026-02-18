from flask import Flask, render_template
from flask_socketio import SocketIO
from tensorflow.keras.models import load_model
import cv2, numpy as np, os

# ===== Load model (same as in notebook) =====
model = load_model("violence_model.h5")
IMG_SIZE, SEQUENCE_LEN = 112, 20

def predict_video(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while len(frames) < SEQUENCE_LEN and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_resized = cv2.resize(frame, (IMG_SIZE, IMG_SIZE)).astype("float32") / 255.0
        frames.append(frame_resized)
    cap.release()

    label = "Video too short"
    if len(frames) == SEQUENCE_LEN:
        frames = np.expand_dims(frames, axis=0)
        pred = model.predict(frames)
        print("Raw prediction (Flask):", pred)  # debug
        label = "Violence" if np.argmax(pred) == 0 else "NonViolence"
    return label

# ===== Flask setup =====
app = Flask(__name__, template_folder="WEBSITE")
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/control")
def control():
    return render_template("control.html")

@app.route("/test/<filename>")
def test_video(filename):
    video_path = os.path.join("TestVideos", filename)
    result = predict_video(video_path)
    if result == "Violence":
        socketio.emit("notification", {"message": "Violence Detected!"})
    return {"result": result}

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000,
                 debug=True, allow_unsafe_werkzeug=True, use_reloader=False)
