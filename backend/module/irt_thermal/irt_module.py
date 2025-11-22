import os
import sys
import time
import serial
import cv2
import numpy as np
import matplotlib.pyplot as plt 

from logging import info, error
from flask_socketio import SocketIO
from picamera2 import Picamera2  

from utils import clear_and_ensure_folder, calculate_centered_roi

np.set_printoptions(threshold=sys.maxsize)

# ------------- SERIAL & PROTOCOL HELPERS ------------- #

def initialize_serial(usb_port: str) -> serial.Serial:
    """Initialize and return a serial connection to the IR sensor."""
    try:
        connection = serial.Serial(
            port=usb_port,
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1,
        )
        info(f"Serial connection initialized on {usb_port}")
        return connection
    except serial.SerialException as e:
        error(f"Failed to initialize serial connection on {usb_port}: {e}")
        raise


def build_request(start_address: int, num_registers: int) -> bytearray:
    """Build request frame for the IR sensor."""
    if not (0 <= start_address <= 259):
        raise ValueError(f"start_address must be in the range 0–259. Got {start_address}.")
    if not (1 <= num_registers <= 259):
        raise ValueError(f"num_registers must be in the range 1–259. Got {num_registers}.")

    request = bytearray()
    request.append(0x11)  # START

    # Start address
    request.append((start_address >> 8) & 0xFF)  # MSB
    request.append(start_address & 0xFF)         # LSB

    # Number of registers
    request.append((num_registers >> 8) & 0xFF)  # MSB
    request.append(num_registers & 0xFF)         # LSB

    request.append(0x98)  # END

    info(f"Request frame: {request}")
    return request


def parse_response_data(data: bytes) -> np.ndarray:
    """
    Parse raw bytes from the sensor to a 16x16 matrix.
    Assumes:
        - First 2 bytes: START
        - Last 2 bytes: END
        - Middle: 16x16 temperature values (2 bytes each)
    """
    data_bytes = list(data)

    if len(data_bytes) < 4:
        raise ValueError(f"Response too short: {len(data_bytes)} bytes")

    # START
    start_msb = data_bytes[0]
    start_lsb = data_bytes[1]
    start_value = (start_msb << 8) | start_lsb

    temp_data = []
    index = 2
    while index < len(data_bytes) - 2:
        temp_msb = data_bytes[index]
        temp_lsb = data_bytes[index + 1]
        temperature = (temp_msb << 8) | temp_lsb
        temp_data.append(round(temperature * 0.1, 2))
        index += 2

    # END
    end_msb = data_bytes[-2]
    end_lsb = data_bytes[-1]
    end_value = (end_msb << 8) | end_lsb

    response_list = [start_value] + temp_data + [end_value]

    # Ensure exactly 16x16
    if len(response_list) > 256:
        response_list = response_list[:256]
    elif len(response_list) < 256:
        # pad with last value if short
        response_list += [response_list[-1]] * (256 - len(response_list))

    response_matrix = np.array(response_list).reshape(16, 16)
    return response_matrix


def extract_temp_data(data: np.ndarray) -> np.ndarray:
    """
    Clean / adjust temperature matrix.
    Original logic: find value 5784.0, replace with mean of neighbors.
    Now we make it safer.
    """
    flattened = np.array(data, dtype=float).flatten()

    indices = np.where(flattened == 5784.0)[0]
    if indices.size > 0:
        idx = indices[0]
        # You used three fixed neighbors before; keep the idea but safe:
        neighbors = []

        # Example: use first three actual valid cells (simplify)
        neighbors.extend(data[0, 1:3])
        neighbors.append(data[1, 0])

        mean_value = round(float(np.mean(neighbors)), 1)
        flattened[idx] = mean_value

    temperature_matrix = flattened.reshape((16, 16))
    return temperature_matrix


# ------------- VISION / HEATMAP HELPERS ------------- #

def get_center_frame(frame: np.ndarray, roi_size: int = 350):
    """Calculate centered ROI within frame."""
    height, width, _ = frame.shape
    center_x, center_y = width // 2, height // 2
    x_start = max(0, center_x - roi_size // 2)
    y_start = max(0, center_y - roi_size // 2)
    x_end = min(width, center_x + roi_size // 2)
    y_end = min(height, center_y + roi_size // 2)
    return (center_x, center_y), (x_start, y_start, x_end, y_end)


def save_image(region: np.ndarray, filename: str) -> None:
    cv2.imwrite(filename, region)


def ir_heatmap(frame: np.ndarray, data: np.ndarray) -> np.ndarray:
    """Generate overlay heatmap for a 16x16 temperature matrix on top of the frame."""
    # Normalize data safely
    d_min, d_max = np.min(data), np.max(data)
    if d_max == d_min:
        data_normalized = np.zeros_like(data, dtype=float)
    else:
        data_normalized = (data - d_min) / (d_max - d_min)

    data_normalized = 1 - data_normalized  # invert for colormap

    colormap = plt.cm.jet
    heatmap = colormap(data_normalized)
    heatmap = (heatmap[:, :, :3] * 255).astype(np.uint8)

    height, width, _ = frame.shape
    heatmap_resized = cv2.resize(heatmap, (width, height), interpolation=cv2.INTER_LINEAR)

    blended = cv2.addWeighted(frame, 0.5, heatmap_resized, 0.5, 0)

    # Draw numeric values
    offset_pixel = 4
    grid_size = 16
    cell_width = width // grid_size
    cell_height = height // grid_size
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.25
    font_thickness = 1
    text_color = (255, 255, 255)

    for i in range(offset_pixel, grid_size + offset_pixel):
        for j in range(offset_pixel, grid_size + offset_pixel):
            val = data[i - offset_pixel, j - offset_pixel]
            temp_value = f"{val:.1f}"
            x = j * cell_width + cell_width // 4
            y = i * cell_height + cell_height // 2
            cv2.putText(blended, temp_value, (x - 5, y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)

    return blended


def read_temperature(serial_port: serial.Serial):
    """Send request → read response → return (temp_matrix, raw_matrix)."""
    start_address = 1
    num_registers = 256
    num_of_byte = (num_registers * 2) + 4

    try:
        request_packet = build_request(start_address, num_registers)
        serial_port.write(request_packet)

        response = serial_port.read(num_of_byte)

        if not response:
            info("No response from serial port.")
            time.sleep(0.1)
            return None, None

        info(
            f"Debug: len={len(response)}, "
            f"start ok={len(response) >= 4 and response[0] == 22 and response[1] == 152}, "
            f"end ok={len(response) >= 4 and response[-2] == 26 and response[-1] == 156}"
        )

        if len(response) >= 4 and response[0] == 22 and response[1] == 152 and response[-2] == 26 and response[-1] == 156:
            parsed = parse_response_data(response)
            temp_matrix = extract_temp_data(parsed)
            time.sleep(0.1)
            return temp_matrix, parsed

        info("Response markers invalid.")
        time.sleep(0.1)
        return None, None

    except serial.SerialException as e:
        error(f"Serial communication error: {e}")
    except Exception as e:
        error(f"Unexpected error in read_temperature: {e}")

    time.sleep(0.1)
    return None, None


# ------------- MAIN DETECTOR / STREAM FUNCTION ------------- #

def irt_detect_cam(socketio: SocketIO, face_cam: int, usb_port: str, temp_offset: float = 1.5):
    """
    Main generator for:
      - capturing frames via Picamera2
      - detecting face in ROI
      - reading IR matrix
      - emitting irt_data & irt_state via Socket.IO
      - streaming MJPEG frames (yield)
    """

    time.sleep(1)

    temp_data = {
        "temp_data_collect": []
    }

    ser = None
    picam2 = None

    try:
        ser = initialize_serial(usb_port)
        socketio.emit('irt_state', {'state': 'Connecting'})
        time.sleep(0.5)

        if not ser.is_open:
            socketio.emit('irt_state', {'state': 'Error'})
            error("Serial port not open.")
            return

        info("Serial port is open and configured.")
        socketio.emit('irt_state', {'state': 'Connected'})
        time.sleep(0.5)

        screen_width, screen_height = 640, 480
        picam2 = Picamera2(camera_num=face_cam)

        socketio.emit('irt_state', {'state': 'Open Camera Successfully'})
        time.sleep(0.5)

        try:
            config = picam2.create_preview_configuration(
                main={'format': 'RGB888', "size": (screen_width, screen_height)}
            )
            picam2.configure(config)
            picam2.start()
        except Exception as cam_err:
            error(f"Error starting camera: {cam_err}")
            socketio.emit('irt_state', {'state': 'Error'})
            if picam2 is not None:
                picam2.stop()
                picam2.close()
            return

        roi_x, roi_y, roi_width, roi_height = calculate_centered_roi(screen_width, screen_height)

        haarcascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(haarcascade_path)

        if face_cascade.empty():
            error("Error loading Haar cascade.")
            socketio.emit('irt_state', {'state': 'Error'})
            return

        last_heatmap = None
        socketio.emit('irt_state', {'state': 'Ready'})
        info("IRT ready for measurement.")

        while True:
            frame = picam2.capture_array()
            frame = cv2.flip(frame, -1)
            frame = cv2.flip(frame, 1)

            cv2.rectangle(frame, (roi_x, roi_y),
                          (roi_x + roi_width, roi_y + roi_height),
                          (255, 255, 255), 2)

            # BUG FIX: crop by roi_width, roi_height (was roi_height twice)
            roi_frame = frame[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width]

            faces = face_cascade.detectMultiScale(
                roi_frame,
                scaleFactor=1.1,
                minNeighbors=10,
                minSize=(60, 60)
            )

            if len(faces) == 0:
                socketio.emit('irt_state', {'state': 'Ready'})
            else:
                socketio.emit('irt_state', {'state': 'Measuring'})

                for (x, y, w, h) in faces:
                    cv2.rectangle(roi_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                temp_matrix, raw_response = read_temperature(ser)

                if temp_matrix is not None:
                    temp_data_max = round(float(np.max(temp_matrix)) + temp_offset, 1)
                    temp_data_min = round(float(np.min(temp_matrix)), 1)
                    temp_data_mean = round(float(np.mean(temp_matrix)), 1)

                    temp_data["temp_data_collect"].append(temp_data_max)

                    # Emit interim data (no final result yet)
                    socketio.emit('irt_data', {
                        'temp_context': 'detect:',
                        'temp_max': temp_data_max,
                        'temp_min': temp_data_min,
                        'temp_result': 'N/A'
                    })

                    last_heatmap = ir_heatmap(roi_frame, temp_matrix)
                    save_image(
                        last_heatmap,
                        os.path.join(os.getcwd(), 'static', 'irt_image', 'heatmap_images.png')
                    )

            # Final result when collected enough samples
            if len(temp_data["temp_data_collect"]) == 10:
                temp_data_result = round(
                    sum(temp_data["temp_data_collect"]) / len(temp_data["temp_data_collect"]), 1
                )

                socketio.emit('irt_data', {
                    'temp_context': 'result',
                    'temp_max': temp_data_max,
                    'temp_min': temp_data_min,
                    'temp_result': temp_data_result
                })

                info(f"Final Temperature Data: {temp_data_result}")
                # publish_run(temp_data_result)  # PUBLISH MHR if needed

                socketio.emit('irt_state', {'state': 'Complete'})

                if ser is not None and ser.is_open:
                    ser.close()
                if picam2 is not None:
                    picam2.stop()
                    picam2.close()

                print("Serial port and camera closed.")
                return temp_data_result

            # Stream camera frame
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    except serial.SerialException as e:
        error(f"Serial communication error: {e}")
        socketio.emit('irt_state', {'state': 'Error'})
    except KeyboardInterrupt:
        print("Stopped by user.")
        socketio.emit('irt_state', {'state': 'Error'})
    except Exception as e:
        error(f"Unexpected error in irt_detect_cam: {e}")
        socketio.emit('irt_state', {'state': 'Error'})
    finally:
        # Ensure resources are closed
        try:
            if ser is not None and ser.is_open:
                ser.close()
        except Exception:
            pass

        try:
            if picam2 is not None:
                picam2.stop()
                picam2.close()
        except Exception:
            pass

        print("Cleanup done in irt_detect_cam.")

def get_mockup_data():
    return {
        "irt_data": {
            "temp_context": "detect:",
            "temp_max": 36,
            "temp_result": 36
        },
        "irt_state": {
            "state": "Complete"
        }
    }