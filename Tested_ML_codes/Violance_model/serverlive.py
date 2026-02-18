from flask import Flask, render_template, Response
from flask_socketio import SocketIO
from tensorflow.keras.models import load_model
import cv2, numpy as np

# ===== Load trained model =====
model = load_model("violence_model.h5")
IMG_SIZE, SEQUENCE_LEN = 112, 20

# ===== Flask setup =====
app = Flask(__name__, template_folder="WEBSITE")
socketio = SocketIO(app, cors_allowed_origins="*")

# ===== Camera capture =====
cap = cv2.VideoCapture(0)
#cap = cv2.VideoCapture("demo\V_1.mp4")
frames_buffer = []

def generate_frames():
    global frames_buffer
    while True:
        success, frame = cap.read()
        if not success:
            break

        # Preprocess frame for model
        frame_resized = cv2.resize(frame, (IMG_SIZE, IMG_SIZE)).astype("float32") / 255.0
        frames_buffer.append(frame_resized)

        if len(frames_buffer) > SEQUENCE_LEN:
            frames_buffer.pop(0)

        label = "Collecting..."
        color = (255, 255, 0)

        # Run detection when buffer is ready
        if len(frames_buffer) == SEQUENCE_LEN:
            input_data = np.expand_dims(frames_buffer, axis=0)
            pred = model.predict(input_data)

            # ⚠ Adjust index mapping if needed
            label = "Violence" if np.argmax(pred) == 1 else "NonViolence"  #...
            color = (0, 0, 255) if label == "Violence" else (0, 255, 0)

            # Trigger popup only for Violence
            if label == "Violence":
                socketio.emit("notification", {"message": "⚠ Violence Detected (Live)!"})

        # Draw overlay text
        cv2.putText(frame, f"Prediction: {label}", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

        # Encode frame for streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/control")
def control():
    return render_template("control.html")

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000,
                 debug=True, allow_unsafe_werkzeug=True, use_reloader=False)
