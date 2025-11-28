from logging import info, error
from flask_socketio import SocketIO
from typing import Dict, Any, Tuple

import serial #type:ignore
import RPi.GPIO as GPIO 

import pytesseract as tess
import cv2, time, os
import numpy as np
from collections import Counter
from picamera2 import Picamera2, CameraConfiguration #type:ignore

from utils import clear_and_ensure_folder

tess.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

bp_emp_data = {"systolic": 0, "diastolic": 0}

def initialize_serial(usb_port):
    try:
        connection = serial.Serial(
            port=usb_port,
            baudrate=9600,
            timeout=1
        )
        info(f"Serial connection initialized on {usb_port}")
        return connection
    except serial.SerialException as e:
        error(f"Failed to initialize serial connection on {usb_port}: {e}")
        raise

def save_image(region, filename):
    cv2.imwrite(filename, region)

def bp_gpio_setup(socketio, RELAY_1, RELAY_2):
    try:
        info("Starting BP GPIO Configuration")
        socketio.emit('bp_update', {
            'bp_state': {'state': 'GPIO config'},
            'bp_indicator': {'state': 'm'}
        })

        # ---- Safe / idempotent GPIO mode handling ----
        current_mode = GPIO.getmode()
        if current_mode is not None and current_mode != GPIO.BCM:
            # Some other code (or previous run) used a different mode → reset everything
            info(f"GPIO mode was {current_mode}, calling GPIO.cleanup() before re-init")
            try:
                GPIO.cleanup()
            except Exception as e:
                error(f"GPIO.cleanup() before re-init failed: {e}")

        # After cleanup, or when mode was None, set BCM once
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)

        socketio.emit('bp_update', {
            'bp_state': {'state': 'GPIO setup'},
            'bp_indicator': {'state': 'm'}
        })

        # ---- Set up GPIO pins ----
        GPIO.setup(RELAY_1, GPIO.OUT)
        GPIO.setup(RELAY_2, GPIO.OUT)

        # Assume active-low relay → HIGH = off
        GPIO.output(RELAY_1, GPIO.HIGH)
        GPIO.output(RELAY_2, GPIO.HIGH)

        time.sleep(1)

        info("BP GPIO Configuration Completed!")
        socketio.emit('bp_update', {
            'bp_state': {'state': 'GPIO success'},
            'bp_indicator': {'state': 'c'}
        })

    except Exception as e:
        # Catch *any* error and report via Socket.IO
        error_message = f"Unexpected error during GPIO setup: {e}"
        error(error_message)
        socketio.emit('bp_update', {
            'bp_state': {'state': 'GPIO config-error'},
            'bp_indicator': {'state': 'e'}
        })
        # Re-raise so Flask still returns 500 and you see the stack trace
        raise

def bp_gpio_clear(RELAY_1=None, RELAY_2=None, cleanup=True):
    try:
        if RELAY_1 is not None:
            GPIO.output(RELAY_1, GPIO.HIGH)
        if RELAY_2 is not None:
            GPIO.output(RELAY_2, GPIO.HIGH)

        if cleanup:
            GPIO.cleanup()  # resets mode to None
        info("BP GPIO cleanup completed.")
    except Exception as e:
        error(f"GPIO cleanup error: {e}")

        
def relay_control(socketio, relay, RELAY_1=17, RELAY_2=18):
    relay_pin = RELAY_1 if relay == 1 else RELAY_2
    try:
        GPIO.output(relay_pin, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(relay_pin, GPIO.LOW)
        time.sleep(0.5)
        GPIO.output(relay_pin, GPIO.HIGH)
        socketio.emit('bp_update', {
                'bp_state': {'state': f'Trigger GPIO {relay_pin}'},
                'bp_indicator': {'state': 'm'}
        })
        
    except Exception as e:
        info(f"Error controlling relay {relay}: {e}")

def receive_state(serial_port, BUFFER_SIZE=5):
    if serial_port.in_waiting >= BUFFER_SIZE:
        hex_data = serial_port.read(BUFFER_SIZE)
        return ''.join(chr(b) if 32 <= b <= 126 else '.' for b in hex_data)
    return ""

def bp_process_state(socketio, state, bp_states, state_size=6):
    required_states = ["INF..", "DEF..", "EXH.."]
    ocr_triggered = False

    if state in ["OFF..", "ON ..", "CHK..", "WAI..", "FIT..", "INF..", "DEF..", "EXH.."]:
        bp_states.append(state)
        info(f"STAGE: BP {state}")

        if state == "OFF..":
            relay_control(socketio, 1)
        elif state == "WAI..":
            relay_control(socketio, 2)

        if len(bp_states) >= state_size:
            if set(required_states).issubset(bp_states):
                ocr_triggered = True
                return False, ocr_triggered

            if bp_states.count("WAI..") >= 2:
                ocr_triggered = False
                relay_control(socketio, 1)
                return False, ocr_triggered

    # socketio.emit('bp_state', {'state': f'Measurement State Completed!'})
    return True, ocr_triggered

def bp_control(socketio, usb_port):
    rm_ocr_path = os.path.join(os.getcwd(), 'static', 'bp_image')
    clear_and_ensure_folder(rm_ocr_path)
    time.sleep(1)
    ser = None 
    ocr_triggered = False
    
    try:
        ser = initialize_serial(usb_port)
        socketio.emit('bp_update', {
                'bp_state': {'state': 'Connection..'},
                'bp_indicator': {'state': 'm'}
        })
        time.sleep(0.5)

        if ser.is_open:
            info("Serial port is open and configured.")
            socketio.emit('bp_update', {
                'bp_state': {'state': 'Connected!'},
                'bp_indicator': {'state': 'c'}
            })
            relay_control(socketio, 1)
            
            bp_states = []
            while True:
                try:
                    bp_stage = receive_state(ser)
                    if bp_stage:
                        info(f"Received Stage: {bp_stage}")
                        socketio.emit('bp_update', {
                            'bp_state': {'state': 'Processing..', 'msg': bp_stage},
                            'bp_indicator': {'state': 'm'}
                        })
                        info(f"Debug BP Stage: {bp_stage}")
                        # socketio.emit('bp_state', {'msg_state': f'Measurement State {bp_stage}'})
                        in_process, ocr_triggered = bp_process_state(socketio, bp_stage, bp_states)
                        if not in_process:
                            break
                except Exception as e:
                    error(f"Error processing state: {e}")
                time.sleep(0.5)
    except Exception as e:
        info(f"Error during BP control: {e}")
    finally:
        try:
            ser.close()
        except Exception as e:
            info(f"Error closing serial port: {e}")
    return ocr_triggered

def process_frame_ocr(roi, contour_area_threshold):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(6, 6))
    gray_clahe = clahe.apply(gray)
    blurred = cv2.GaussianBlur(gray_clahe, (15, 15), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detected_text = ""
    for contour in contours:
        if cv2.contourArea(contour) > contour_area_threshold:
            inverted_roi = cv2.bitwise_not(closing)
            text = tess.image_to_string(inverted_roi, config="--oem 3 --psm 8", lang="ssd")
            detected_text = text.strip()
    return detected_text, closing, gray_clahe

def ocr_function(frame, roi_coordinates, color, buffer, contour_area_threshold=1600):
    x1, x2, y1, y2 = roi_coordinates
    roi = frame[y1:y2, x1:x2]
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    detected_text, closing, clahe = process_frame_ocr(roi, contour_area_threshold)
    if detected_text.isdigit():
        buffer.append(int(detected_text))
        if len(buffer) > 10:
            buffer.pop(0)
    return buffer, detected_text, closing, clahe

def verify_value(buffer):
    if buffer:
        most_common, count = Counter(buffer).most_common(1)[0]
        if count >= 7:
            return most_common
    return None

def bp_ocr_reader(measure_time, ocr_cam):

    # rm_ocr_path = os.path.join(os.getcwd(), 'static', 'blood_pressure')
    # clear_and_ensure_folder(rm_ocr_path)

    buffer_sys, buffer_dia , buffer_pulse= [], [], []
    start_time = time.time()

    picam2 = Picamera2(camera_num=ocr_cam)
    config = picam2.create_preview_configuration(main={'format': 'RGB888', 'size': (640, 480)})
    picam2.configure(config)
    info("PiCamera Configuation!")
    picam2.start()
    info("PiCamera Start")

    try:
        while True:
            frame = picam2.capture_array()
            frame = cv2.flip(frame, -1)

            buffer_sys, text_sys, closing_sys, clahe_sys = ocr_function(frame, (210, 450, 110, 270), (0, 255, 0), buffer_sys)
            buffer_dia, text_dia, closing_dia, clahe_dia = ocr_function(frame, (230, 450, 270, 440), (255, 0, 255), buffer_dia)
            buffer_pulse, text_pulse, closing_pulse, clahe_pulse = ocr_function(frame, (230, 400, 440, 540), (255, 255, 0), buffer_pulse)
            # buffer_sys, text_sys, closing_sys, clahe_sys = ocr_function(frame, (200, 460, 20, 185), (0, 255, 0), buffer_sys)
            # buffer_dia, text_dia, closing_dia, clahe_dia = ocr_function(frame, (200, 460, 180, 360), (255, 0, 255), buffer_dia)
            
            final_sys = verify_value(buffer_sys)
            final_dia = verify_value(buffer_dia)
            final_pulse = verify_value(buffer_pulse)

            cv2.putText(frame, f"sys: {text_sys}", (70, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"dia: {text_dia}", (70, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            cv2.putText(frame, f"pulse: {text_pulse}", (70, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

            if final_sys and final_dia:
                info("OCR Data:", {"systolic": final_sys, "diastolic": final_dia, "pulse": final_pulse})
                save_image(frame, os.path.join(os.getcwd(), f'static/bp_image/bp_images_{measure_time}.png'))
                save_image(closing_sys, os.path.join(os.getcwd(), f'static/bp_image/bp_images_closing_sys_{measure_time}.png'))
                save_image(closing_dia, os.path.join(os.getcwd(), f'static/bp_image/bp_images_closing_dia_{measure_time}.png'))
                save_image(clahe_sys, os.path.join(os.getcwd(), f'static/bp_image/bp_images_clahe_sys_{measure_time}.png'))
                save_image(clahe_dia, os.path.join(os.getcwd(), f'static/bp_image/bp_images_clahe_dia_{measure_time}.png'))
                save_image(closing_pulse, os.path.join(os.getcwd(), f'static/bp_image/bp_images_closing_pulse_{measure_time}.png'))
                save_image(clahe_pulse, os.path.join(os.getcwd(), f'static/bp_image/bp_images_closing_pulse_{measure_time}.png'))
                break
            
            if time.time() - start_time > 30:
                info("OCR Detection Timeout - Error reading OCR.")
                save_image(frame, os.path.join(os.getcwd(), f'static/bp_image/bp_images_{measure_time}.png'))
                save_image(closing_sys, os.path.join(os.getcwd(), f'static/bp_image/bp_images_closing_sys_{measure_time}.png'))
                save_image(closing_dia, os.path.join(os.getcwd(), f'static/bp_image/bp_images_closing_dia_{measure_time}.png'))
                save_image(clahe_sys, os.path.join(os.getcwd(), f'static/bp_image/bp_images_clahe_sys_{measure_time}.png'))
                save_image(clahe_dia, os.path.join(os.getcwd(), f'static/bp_image/bp_images_clahe_dia_{measure_time}.png'))
                save_image(closing_pulse, os.path.join(os.getcwd(), f'static/bp_image/bp_images_closing_pulse_{measure_time}.png'))
                save_image(clahe_pulse, os.path.join(os.getcwd(), f'static/bp_image/bp_images_closing_pulse_{measure_time}.png'))
                return bp_emp_data

        picam2.close()
    except Exception as e:
        info(f"Error during OCR detection: {e}")
    finally:
        picam2.close()

    return {"systolic": final_sys, "diastolic": final_dia}

def bp_process_acceptable(socketio, ocr_triggered, measure_time, ocr_cam):
    bp_msg = 'Incompleted'
    if ocr_triggered:
        socketio.emit('bp_update', {
            'bp_state': {'state': 'Checking Result'},
            'bp_indicator': {'state': 'm'}
        })
        
        bp_data = bp_ocr_reader(measure_time, ocr_cam)
        acceptable_range = {"systolic": (60, 190), "diastolic": (40, 130)}
        if all(acceptable_range[key][0] <= bp_data[key] <= acceptable_range[key][1] for key in acceptable_range):
            info("SYS & DIA ARE WITHIN ACCEPT RANGE.")
            info(f"BLOOD PRESSURE STATUS : MEASUREMENT COMPLETE.")
            bp_msg = 'Completed'
            socketio.emit('bp_update', {
                'bp_state': {'state': 'Result Completed'},
                'bp_indicator': {'state': 'c'}
            })
            return bp_data, bp_msg
        else:
            error("SYS & DIA ARE OUT OF ACCEPT RANGE.")
            error(f"BLOOD PRESSURE STATUS : MEASUREMENT FAILED.")
            socketio.emit('bp_update', {
                'bp_state': {'state': 'Result Failed!'},
                'bp_indicator': {'state': 'e'}
            })
    else:
        error("BLOOD PRESSURE STATUS: CANNOT DETECT.")
        socketio.emit('bp_update', {
            'bp_state': {'state': 'Cannot Detected!'},
            'bp_indicator': {'state': 'e'}
        })

    return bp_emp_data, bp_msg

def bp_controller(socketio: SocketIO, measure_time, ocr_cam, usb_port):
    info("START MEASUREMENT: BLOOD PRESSURE")

    RELAY_1 = 17
    RELAY_2 = 18

    # default result structure
    bp_data = {
        "systolic": 0,
        "diastolic": 0,
        "pulse": 0,
        "msg": "Incompleted",
        "success": False,
    }

    try:
        # --- GPIO setup ---
        bp_gpio_setup(socketio, RELAY_1, RELAY_2)

        # --- Serial & state control ---
        ocr_triggered = bp_control(socketio, usb_port)

        # --- OCR + acceptable range ---
        bp_result, bp_msg = bp_process_acceptable(
            socketio, ocr_triggered, measure_time, ocr_cam
        )
        bp_data.update(bp_result)
        bp_data["msg"] = bp_msg
        bp_data["success"] = (bp_msg == "Completed")

        return bp_data

    finally:
        # Always attempt to clean up GPIO so next call starts clean
        try:
            bp_gpio_clear(RELAY_1, RELAY_2, cleanup=True)
        except Exception as e:
            error(f"GPIO cleanup error during bp_controller: {e}")

