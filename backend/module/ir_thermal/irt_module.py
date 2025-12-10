import os, sys, time, serial, cv2
import numpy as np
import matplotlib.pyplot as plt 

from flask_socketio import SocketIO 
from picamera2 import Picamera2  

from logging import info, error
from utils import clear_and_ensure_folder, calculate_centered_roi

np.set_printoptions(threshold=sys.maxsize)

# ----------------------------
#  SERIAL & PROTOCOL HELPERS
# ----------------------------

def initialize_serial(usb_port):
    try:
        connection = serial.Serial(
            port=usb_port,
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )
        info(f"Serial connection initialized on {usb_port}")
        return connection
    except serial.SerialException as e:
        error(f"Failed to initialize serial connection on {usb_port}: {e}")
        raise
    
def build_request(start_address, num_registers):
    if not (0 <= start_address <= 259):
        raise ValueError(f"start_address must be in the range 0-259. Got {start_address}.")
    if not (1 <= num_registers <= 259):
        raise ValueError(f"num_registers must be in the range 1-259. Got {num_registers}.")
    
    request = bytearray()
    request.append(0x11)  # START_BYTE

    # Start Address (2 bytes)
    request.append((start_address >> 8) & 0xFF)  # MSB
    request.append(start_address & 0xFF)         # LSB

    # Number of Registers (2 bytes)
    request.append((num_registers >> 8) & 0xFF)  # MSB
    request.append(num_registers & 0xFF)         # LSB

    request.append(0x98)  # END_BYTE

    # info(f"Request: {request.hex()}")  # Log as a hex string for readability
    info(f"Request: {request}")  # Log as a hex string for readability
    return request

def parse_response_data(data):
    data_bytes = list(data)

    # EXTRACT START BYTES
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

    # EXTRACT END BYTES
    end_msb = data_bytes[-2]
    end_lsb = data_bytes[-1]
    end_value = (end_msb << 8) | end_lsb

    response_list = [start_value] + temp_data + [end_value]

    if len(response_list) > 256:
        response_list = response_list[:256]  # Truncate if there's excess data

    response_matrix = np.array(response_list).reshape(16, 16)
    return response_matrix

# ----------------------------
#  IR TEMPERATURE CONTROL
# ----------------------------

def extract_temp_data(data):
    flattened_data = np.array(data).flatten()

    index_5784 = np.where(flattened_data == 5784.0)[0][0]
    values = [data[0][1], data[1][0], data[1][1]]
    mean_value = round(sum(values) / len(values), 1)

    flattened_data[index_5784] = mean_value

    temperature_matrix = flattened_data.reshape((16, 16))
    return temperature_matrix

def get_center_frame(frame, roi_size=350):
    # CALCULATE ROI
    height, width, _ = frame.shape
    center_x, center_y = width // 2, height // 2
    x_start = max(0, center_x - roi_size // 2)
    y_start = max(0, center_y - roi_size // 2)
    x_end = min(width, center_x + roi_size // 2)
    y_end = min(height, center_y + roi_size // 2)
    return (center_x, center_y), (x_start, y_start, x_end, y_end)

def save_image(region, filename):
    cv2.imwrite(filename, region)

def ir_heatmap(frame, data, alpha=0.6, show_text=True, show_grid=True):
    """
    Render a 16x16 IR temperature matrix as a heatmap over a frame.

    Parameters
    ----------
    frame : np.ndarray
        BGR image (e.g. ROI from camera).
    data : array-like
        16x16 temperature matrix (float).
    alpha : float
        Weight of heatmap vs original frame (0..1).
    show_text : bool
        If True, draw temperature values in each cell.
    show_grid : bool
        If True, draw grid lines for 16x16 cells.
    """

    # --- Ensure numpy float32 array ---
    data_arr = np.array(data, dtype=np.float32)

    # --- Normalize to 0–255 for applyColorMap ---
    min_v = float(np.min(data_arr))
    max_v = float(np.max(data_arr))

    if max_v - min_v < 1e-6:
        # Avoid divide-by-zero if all values are (almost) equal
        norm = np.zeros_like(data_arr, dtype=np.uint8)
    else:
        norm = ((data_arr - min_v) / (max_v - min_v) * 255.0).astype(np.uint8)

    # --- Resize to frame size using nearest neighbor (so each sensor cell becomes a block) ---
    h, w = frame.shape[:2]
    heat_resized = cv2.resize(norm, (w, h), interpolation=cv2.INTER_NEAREST)

    # --- Apply JET colormap directly in OpenCV ---
    heat_color = cv2.applyColorMap(heat_resized, cv2.COLORMAP_JET)

    # --- Blend with original frame ---
    alpha = float(alpha)
    alpha = max(0.0, min(1.0, alpha))
    blended = cv2.addWeighted(heat_color, alpha, frame, 1.0 - alpha, 0)

    # --- Optional: draw temperature text + grid ---
    grid_h, grid_w = data_arr.shape  # should be 16 x 16
    cell_w = w / grid_w
    cell_h = h / grid_h

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.35
    font_thickness = 1
    text_color = (255, 255, 255)

    if show_grid:
        # Vertical lines
        for j in range(1, grid_w):
            x = int(j * cell_w)
            cv2.line(blended, (x, 0), (x, h), (255, 255, 255), 1, lineType=cv2.LINE_AA)
        # Horizontal lines
        for i in range(1, grid_h):
            y = int(i * cell_h)
            cv2.line(blended, (0, y), (w, y), (255, 255, 255), 1, lineType=cv2.LINE_AA)

    if show_text:
        for i in range(grid_h):
            for j in range(grid_w):
                temp_value = f"{data_arr[i, j]:.1f}"

                # Center of the cell
                x_center = int(j * cell_w + cell_w / 2)
                y_center = int(i * cell_h + cell_h / 2)

                # Slight offset so text looks centered
                x_text = x_center - 12
                y_text = y_center + 4

                cv2.putText(
                    blended,
                    temp_value,
                    (x_text, y_text),
                    font,
                    font_scale,
                    text_color,
                    font_thickness,
                    cv2.LINE_AA
                )

    return blended

def read_temperature(serial_port):
    # start_address = 0
    # num_registers = 259
    
    start_address = 1
    num_registers = 256
    num_of_byte = (num_registers*2) + 4
    temp_matrix = None

    try:
        request_packet = build_request(start_address, num_registers)
        serial_port.write(request_packet) 

        response = serial_port.read(num_of_byte)
        # info(f"Response: {response}")

        if response is not None:
            try:
                info(f"Debug: {len(response)} >= 4 {len(response) >= 4}, {response[0]} == 22 {response[0] == 22}, {response[1]} == 152 {response[1] == 152}, {response[-2]} == 26 {response[-2] == 26}, {response[-1]} == 156 {response[-1] == 156}")

                if len(response) >= 4 and response[0] == 22 and response[1] == 152 and response[-2] == 26 and response[-1] == 156:
                    response = parse_response_data(response)
                    temp_matrix = extract_temp_data(response)
                    
                time.sleep(0.1) 
                
                return temp_matrix, response
            except Exception as parse_error:
                print(f"Error while parsing response data: {parse_error}")
        else:
            print("Error: No response received from the serial port.")
        time.sleep(0.1)

    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"Unexpected error in temperature reading thread: {e}")

def estimate_face_temp(temp_matrix: np.ndarray) -> float:
    h, w = temp_matrix.shape  # should be 16x16
    i0, i1 = h // 2 - 2, h // 2 + 2
    j0, j1 = w // 2 - 2, w // 2 + 2

    center_patch = temp_matrix[i0:i1, j0:j1]
    flat = center_patch.flatten()
    flat_sorted = np.sort(flat)[::-1]
    top_n = flat_sorted[:5]  # average of 5 hottest pixels
    return float(np.mean(top_n))

def calibrate_to_body(raw_face_temp: float, CALIB_OFFSET=1.8) -> float:
    return round(raw_face_temp + CALIB_OFFSET, 1)
# ----------------------------
#  MAIN DETECTOR / STREAM FUNCTION
# ----------------------------

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
    ser = None
    picam2 = None

    temp_data = {
        "temp_data_collect": []
    }

    try:
        ser = initialize_serial(usb_port)
        socketio.emit('irt_update', {
            'irt_state': {'state': 'Connecting'},
            'irt_indicator': {'state': 'm'}
        })
        time.sleep(0.5)

        if not ser.is_open:
            socketio.emit('irt_update', {
                'irt_state': {'state': 'serial e.'},
                'irt_indicator': {'state': 'e'}
            })
            error("Serial port not open.")
            return

        info("Serial port is open and configured.")
        socketio.emit('irt_update', {
                'irt_state': {'state': 'Connected'},
                'irt_indicator': {'state': 'm'}
        })
        time.sleep(0.5)

        screen_width, screen_height = 640, 480
        picam2 = Picamera2(camera_num=face_cam)

        socketio.emit('irt_update', {
                'irt_state': {'state': 'Camera active'},
                'irt_indicator': {'state': 'm'}
        })
        time.sleep(0.5)

        try:
            config = picam2.create_preview_configuration(
                main={'format': 'RGB888', "size": (screen_width, screen_height)}
            )
            picam2.configure(config)
            picam2.start()
        except Exception as cam_err:
            error(f"Error starting camera: {cam_err}")
            socketio.emit('irt_update', {
                'irt_state': {'state': 'camera e.'},
                'irt_indicator': {'state': 'e'}
            })

            if picam2 is not None:
                picam2.stop()
                picam2.close()
            return

        roi_x, roi_y, roi_width, roi_height = calculate_centered_roi(screen_width, screen_height)

        haarcascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(haarcascade_path)

        if face_cascade.empty():
            error("Error loading Haar cascade.")
            socketio.emit('irt_update', {
                'irt_state': {'state': 'face e.'},
                'irt_indicator': {'state': 'e'}
            })
            return

        last_heatmap = None
        socketio.emit('irt_update', {
                'irt_state': {'state': 'Ready'},
                'irt_indicator': {'state': 'm'}
        })
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
                socketio.emit('irt_update', {
                        'irt_state': {'state': 'Find a Face'},
                        'irt_indicator': {'state': 'm'}
                })
            else:
                socketio.emit('irt_update', {
                        'irt_state': {'state': 'Meas.'},
                        'irt_indicator': {'state': 'm'}
                })

                for (x, y, w, h) in faces:
                    cv2.rectangle(roi_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                temp_matrix, raw_response = read_temperature(ser)

                if temp_matrix is not None:
                    # 1) estimate forehead temp from IR matrix
                    raw_face_temp = estimate_face_temp(temp_matrix)

                    # 2) apply calibration to get body-equivalent temp
                    temp_data_max = calibrate_to_body(raw_face_temp)

                    # optional: keep raw min/mean for debug/visualization
                    temp_data_min = round(float(np.min(temp_matrix)), 1)
                    temp_data_mean = round(float(np.mean(temp_matrix)), 1)

                    temp_data["temp_data_collect"].append(temp_data_max)
                    print("RAW_FACE:", raw_face_temp, "CALIB:", temp_data_max)
                    print("RAW_MIN:", temp_data_min, "RAW_MEAN:", temp_data_mean)

                    socketio.emit('irt_data', {
                        'temp_max': temp_data_max,
                        'temp_min': temp_data_min,
                        'temp_result': ''
                    })

                    last_heatmap = ir_heatmap(roi_frame, temp_matrix)
                    save_image(
                        last_heatmap,
                        os.path.join(os.getcwd(), 'static', 'irt_image', 'heatmap_images.png')
                    )

            if len(temp_data["temp_data_collect"]) == 15:
                temp_data_result = round(
                    sum(temp_data["temp_data_collect"]) / len(temp_data["temp_data_collect"]), 1
                )

                socketio.emit('irt_data', {
                    'temp_max': temp_data_max,
                    'temp_min': temp_data_min,
                    'temp_result': temp_data_result
                })

                info(f"Final Temperature Data: {temp_data_result}")
                if last_heatmap is not None:
                    save_image(
                        frame,
                        os.path.join(os.getcwd(), 'static', 'irt_image', 'irt_images.png')
                    )
                    image_rel_path = '/static/irt_image/irt_images.png'
                    socketio.emit('irt_result', {'image_url': image_rel_path})

                socketio.emit('irt_update', {
                        'irt_state': {'state': 'Complete'},
                        'irt_indicator': {'state': 'c'}
                })

                if ser is not None and ser.is_open:
                    ser.close()
                if picam2 is not None:
                    picam2.stop()
                    picam2.close()

                info("Serial port and camera closed.")
                return temp_data_result

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    except serial.SerialException as e:
        error(f"Serial communication error: {e}")
        socketio.emit('irt_update', {
                'irt_state': {'state': 'serial e.'},
                'irt_indicator': {'state': 'e'}
            })
    except KeyboardInterrupt:
        print("Stopped by user.")
        socketio.emit('irt_update', {
                'irt_state': {'state': 'user stop'},
                'irt_indicator': {'state': 'e'}
            })
    except Exception as e:
        error(f"Unexpected error in irt_detect_cam: {e}")
        socketio.emit('irt_update', {
                'irt_state': {'state': 'detect e.'},
                'irt_indicator': {'state': 'e'}
            })
    finally:
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

        info("Cleanup done in irt_detect_cam.")
