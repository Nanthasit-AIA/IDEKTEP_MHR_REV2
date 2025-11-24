import cv2, time, os
import numpy as np
from collections import Counter
from picamera2 import Picamera2, CameraConfiguration #type:ignore

picam2 = Picamera2(camera_num=1)
config = picam2.create_preview_configuration(main={'format': 'RGB888', 'size': (900, 900)})
picam2.configure(config)
print("PiCamera Configuation!")
picam2.start()
print("PiCamera Start")
try:
        while True:
            frame = picam2.capture_array()
            frame = cv2.flip(frame, -1)
            cv2.imshow("t", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                picam2.close()
except Exception as e:
    print(f"Error during OCR detection: {e}")
finally:
    picam2.close()
