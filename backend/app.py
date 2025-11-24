from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from module.ir_thermal.irt_module import irt_detect_cam
from module.blood_pressure.bp_module import bp_controller
from module.drawer_control.drawer_module import drawer_controller

import time
from logging import info, error
from coloredlogs import install

log_format = "%(asctime)s - %(hostname)s:%(username)s:%(programname)s - %(levelname)s: %(message)s"
install(level="info", format=log_format)

USB_PORT = "/dev/ttyUSB1"
BP_PORT = "/dev/ttyUSB0"   # ✅ fixed: added leading slash
FACE_CAM = 0
OCR_CAM = 1

# --------------- APP SETUP -------------- #
app = Flask(__name__, static_folder="static")
CORS(app)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# -------- IRT MJPEG STREAM -------- #
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

# -------- DRAWER CONTROL (used by bp_measurement.vue) -------- #
def trigger_drawer(data, value=None):
    port = "/dev/ttyACM0"
    baudrate = 115200
    info(data["data"])

    if data["data"] == "med_1DrawerOpen":
        d_status = 0
        d_number = 1
        drawer_controller(port, baudrate, d_status, d_number)
        time.sleep(5)
        socketio.emit("mhr_status", {"status": "1DrawerOpen"})

    elif data["data"] == "med_1DrawerClose":
        d_status = 1
        d_number = 1
        time.sleep(1)      # small delay before closing
        drawer_controller(port, baudrate, d_status, d_number)
        time.sleep(1)
        socketio.emit("mhr_status", {"status": "1DrawerClose"})

    else:
        error(f"Unknown drawer command: {data['data']}")

@socketio.on("drawer_control")
def handle_drawer_control(data):
    """Receive drawer commands from frontend."""
    trigger_drawer(data)

# -------- BP MEASUREMENT API (called when user clicks Measurement) -------- #
@app.post("/api/bp_measurement")
def api_bp_measurement():
    """
    Trigger one blood pressure measurement.
    Frontend: POST http://localhost:5000/api/bp_measurement
    """
    measure_time = "1"

    bp_data = bp_controller(
        socketio=socketio,
        measure_time=measure_time,
        ocr_cam=OCR_CAM,
        usb_port=BP_PORT,
    )

    # bp_data already includes systolic/diastolic (and msg if you added earlier)
    return jsonify(bp_data)

# -------- MAIN -------- #
if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True,
    )
