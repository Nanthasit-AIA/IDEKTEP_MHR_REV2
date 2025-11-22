from flask import Flask, Response, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from module.irt_thermal.irt_module import irt_detect_cam


USB_PORT = "/dev/ttyUSB1"  
FACE_CAM = 0               

# --------------- APP SETUP -------------- #
app = Flask(__name__, static_folder="static")
CORS(app)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"  
)

@app.get("/api/mockup")
def api_mockup():
    return jsonify({
        "irt_data": {
            "temp_context": "detect:",
            "temp_max": 36.0,
            "temp_result": 36.0
        },
        "irt_state": {
            "state": "Complete"
        }
    })

@app.get("/video_feed")
def video_feed():
    """
    MJPEG stream endpoint.
    Frontend (HTML) example:
      <img src="http://localhost:5000/video_feed">
    """
    return Response(
        irt_detect_cam(
            socketio=socketio,
            face_cam=FACE_CAM,
            usb_port=USB_PORT,
            temp_offset=1.5
        ),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    # Use socketio.run instead of app.run
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )
