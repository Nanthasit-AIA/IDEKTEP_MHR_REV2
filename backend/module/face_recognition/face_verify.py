# #need to run this command before run the code set TF_ENABLE_ONEDNN_OPTS=0 (Windows) / export TF_ENABLE_ONEDNN_OPTS=0 (Linux)
# import os
# os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

# import pandas as pd
# from numpy import dot
# from numpy.linalg import norm
# import cv2
# from deepface import DeepFace
# from mtcnn import MTCNN
# import time
# from utils import clear_and_ensure_folder, calculate_centered_roi
# from flask_socketio import SocketIO
# from picamera2 import Picamera2

# import os
# # ...
# faceprint_path = os.path.join("static", "information", "faceprints.csv")
# os.makedirs(os.path.dirname(faceprint_path), exist_ok=True)


# def load_faceprints(csv_file):
#     return pd.read_csv(csv_file, header=None)

# def image2df(captured_images, person_name, output_csv=faceprint_path):
#     faceprints = []  
#     for image_path in captured_images:
#         embedding = extract_face_embedding(image_path)
#         faceprints.append([person_name] + embedding)  

#     df = pd.DataFrame(faceprints)

#     if os.path.exists(output_csv):
#         df.to_csv(output_csv, mode='a', header=False, index=False)
#     else:
#         df.to_csv(output_csv, mode='w', header=False, index=False)
    
#     print(f"Faceprints saved to {output_csv}")

# def extract_face_embedding(frame):
#     try:
#         embedding = DeepFace.represent(img_path=frame, model_name='Facenet', detector_backend='mtcnn', enforce_detection=False)
#         if embedding:  
#             return embedding[0]['embedding']
#         else:
#             return None  
#     except Exception as e:
#         print(f"Error during face embedding extraction: {e}")
#         return None
    
# def verify_face(embedding, faceprints_csv, threshold=0.8):
#     if embedding is None:
#         return False, None
#     for index, row in faceprints_csv.iterrows():
#         stored_embedding = row[1:]
#         similarity = dot(embedding, stored_embedding) / (norm(embedding) * norm(stored_embedding))

#         if similarity > threshold:
#             return True, row[0], similarity  
#     return False, None, similarity

# def collect_faceprints(image_path, faceprints_df):
#     embedding = extract_face_embedding(image_path)
#     is_verified, name , similarity = verify_face(embedding, faceprints_df, threshold=0.8)  
    
#     return is_verified, name , similarity 

# def fancyDraw(img, bbox, l=20, t=2, rt=1, color=(255,255,255)):
#     x, y, w, h = bbox

#     x1, y1 = x + w, y + h

#     # Draw main rectangle
#     # cv2.rectangle(img, (x, y), (x1, y1), color, rt)

#     # Top Left
#     cv2.line(img, (x, y), (x + l, y), color, t)
#     cv2.line(img, (x, y), (x, y + l), color, t)

#     # Top Right
#     cv2.line(img, (x1, y), (x1 - l, y), color, t)
#     cv2.line(img, (x1, y), (x1, y + l), color, t)

#     # Bottom Left
#     cv2.line(img, (x, y1), (x + l, y1), color, t)
#     cv2.line(img, (x, y1), (x, y1 - l), color, t)

#     # Bottom Right
#     cv2.line(img, (x1, y1), (x1 - l, y1), color, t)
#     cv2.line(img, (x1, y1), (x1, y1 - l), color, t)

# def stream_face_verify(socketio: SocketIO, device_id=0, img_capture=5):

#     rm_verify_path = os.path.join(os.getcwd(), 'static', 'face_recognition', 'verify_face_img')
#     clear_and_ensure_folder(rm_verify_path)
#     # time.sleep(3)
    
#     img_collect_list = []
#     faceprints_df = load_faceprints(os.path.join(os.getcwd(), faceprint_path))
#     # Initialize video capture
#     # cap = cv2.VideoCapture(device_id, cv2.CAP_MSMF)

#     screen_width, screen_height = 640, 480
#     picam2 = Picamera2(camera_num=0)

#     try:
#         config = picam2.create_preview_configuration(main={'format': 'RGB888', "size": (screen_width, screen_height)})
#         picam2.configure(config)
#         picam2.start()
#     except:
#         print("closing camera")
#         picam2.stop()
#         picam2.stop_encoder()
#         picam2.close()

#     detector = MTCNN(device="CPU:0")  # Initialize MTCNN for face detection
    
#     # Set a lower resolution (e.g., 640x480)
#     # cap = set_up_cap(cap, screen_width, screen_height)

#     roi_x, roi_y, roi_width, roi_height = calculate_centered_roi(screen_width, screen_height)

#     cooldown_start_time = None  # For tracking the start time of cooldown
#     images_captured = 0  # To track how many images have been captured in each cooldown
#     images_cap_status = False

#     res_verify_collect_face = 'Incomplete'
#     socketio.emit('res_verify_collect_face', {'data': res_verify_collect_face})
#     socketio.emit('img_capture', {'data': img_capture})

#     while True:
#         frame = picam2.capture_array()
#         frame = cv2.flip(frame, -1)
#         frame = cv2.flip(frame, 1)
        
#         roi_color = (0, 0, 255)  # Red
        
#         # Draw the ROI rectangle on the frame
#         cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_width, roi_y + roi_height), roi_color, 2)
#         roi_frame = frame[roi_y:roi_y + roi_height, roi_x:roi_x + roi_height]

#         # Detect faces within the ROI
#         results = detector.detect_faces(roi_frame)

#         # If any face is detected, change ROI color to green
#         if results:
#             roi_color = (0, 255, 0)  # Green
#         else:
#             cooldown_start_time = None  # Reset countdown if no face detected
        
#         # Update the ROI rectangle color based on detection results
#         cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_width, roi_y + roi_height), roi_color, 2)

#         for result in results:
#             confidence = result['confidence']
#             bounding_box = result['box']
#             (x, y, w, h) = bounding_box

#             # Filter out detections that don't resemble faces (aspect ratio and size check)
#             aspect_ratio = w / float(h)
#             if 0.75 <= aspect_ratio <= 1.3 and w > 50 and h > 50:  # Filter close-to-square detections with min size
#                 # keypoints = result['keypoints']
                
#                 # Draw bounding box around detected face
#                 # cv2.rectangle(roi_frame, 
#                 #                 (bounding_box[0], bounding_box[1]), 
#                 #                 (bounding_box[0] + bounding_box[2], bounding_box[1] + bounding_box[3]), 
#                 #                 (0, 255, 0), 2)
#                 fancyDraw(roi_frame, bounding_box)
            

                
#                 # Display confidence value on the top left corner of the bounding box
#                 cv2.putText(roi_frame, f"Conf: {float(confidence):.2f}", (bounding_box[0], bounding_box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#                 if not images_cap_status: 
#                     if cooldown_start_time is None:
#                         cooldown_start_time = time.time()  # Start countdown

#                     elapsed_time = time.time() - cooldown_start_time
#                     remaining_time = max(0, 5 - int(elapsed_time))
#                     cv2.putText(frame, f"Capturing in: {remaining_time}s", (roi_x, roi_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
#                     cv2.putText(frame, f"Image Captured: {images_captured}/{img_capture}", (roi_x, roi_y + roi_height + 30),  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)  # Display capture count
                
#                     if elapsed_time >= 5 and images_captured < img_capture:
#                         # Crop the face region from the ROI frame
#                         cropped_face = roi_frame[y:y+h, x:x+w]
                        
#                         # Resize the cropped face to the target dimensions
#                         resized_face = cv2.resize(cropped_face, (160, 200))
                        
#                         cropped_face_path = os.path.join(os.getcwd(), f'static/face_recognition/verify_face_img/verify_face_{images_captured + 1}.png')
#                         img_collect_list.append(cropped_face)
#                         cv2.imwrite(cropped_face_path, resized_face)

#                         images_captured += 1
#                         cooldown_start_time = time.time()  # Reset countdown for the next capture

#                     if images_captured >= img_capture:
#                         cooldown_start_time = None
#                         images_captured = 0
#                         images_cap_status = True  # All images captured

#                         res_verify_collect_face = 'Processing..'
#                         socketio.emit('res_verify_collect_face', {'data': res_verify_collect_face})

#                         is_verified, name , similarity = collect_faceprints(img_collect_list[-1], faceprints_df)
#                         if not is_verified:
#                             name = 'Unknown'
#                         socketio.emit('res_verify_face', {
#                             'is_verified': is_verified,
#                             'name': name,
#                             'similarity': f'{round(similarity * 100, 2)}%'
#                         })
#                         time.sleep(1)
#                         socketio.emit('res_verify_collect_face', {'data': 'Completed'})
#                         time.sleep(2)
#                         picam2.close()
                        

#         # Encode the frame in JPEG format
#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame = buffer.tobytes()
#         # Yield the frame and cropped face images
#         yield (b'--frame\r\n'
#                 b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#     picam2.close()

# def stream_face_collection(socketio: SocketIO, device_id=0, img_capture=10, person_name=''):

#     rm_collect_path = os.path.join(os.getcwd(), 'static', 'face_recognition', 'collect_face_img')
#     clear_and_ensure_folder(rm_collect_path)
#     # time.sleep(3)

#     captured_images = []
#     # Initialize video capturee
#     # cap = cv2.VideoCapture(device_id, cv2.CAP_MSMF)

#     screen_width, screen_height = 640, 480
    
#     picam2 = Picamera2(camera_num=0)
#     try:
#         config = picam2.create_preview_configuration(main={'format': 'RGB888', "size": (screen_width, screen_height)})
#         picam2.configure(config)  
#         picam2.start()
#     except:
#         print("closing camera")
#         picam2.stop()
#         picam2.stop_encoder()
#         picam2.close()

#     detector = MTCNN(device="CPU:0")  # Initialize MTCNN for face detection
    
#     # cap = set_up_cap(cap, screen_width, screen_height)

#     roi_x, roi_y, roi_width, roi_height = calculate_centered_roi(screen_width, screen_height)

#     cooldown_start_time = None  # For tracking the start time of cooldown
#     images_captured = 0  # To track how many images have been captured in each cooldown
#     images_cap_status = False

#     res_collect_face = 'Incomplete'
#     socketio.emit('res_collect_face', {'data': res_collect_face})
    
#     while True:
#         frame = picam2.capture_array()
#         frame = cv2.flip(frame, -1)
#         frame = cv2.flip(frame, 1)
        
#         # Set default ROI color to red (no face detected)
#         roi_color = (0, 0, 255)  # Red
        
#         # Draw the ROI rectangle on the frame
#         cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_width, roi_y + roi_height), roi_color, 2)
#         roi_frame = frame[roi_y:roi_y + roi_height, roi_x:roi_x + roi_height]

#         # Detect faces within the ROI
#         results = detector.detect_faces(roi_frame)

#         # If any face is detected, change ROI color to green
#         if results:
#             roi_color = (0, 255, 0)  # Green
#         else:
#             cooldown_start_time = None  # Reset countdown if no face detected
        
#         # Update the ROI rectangle color based on detection results
#         cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_width, roi_y + roi_height), roi_color, 2)

#         for result in results:
#             confidence = result['confidence']
#             bounding_box = result['box']
#             (x, y, w, h) = bounding_box

#             # Filter out detections that don'5 resemble faces (aspect ratio and size check)
#             aspect_ratio = w / float(h)
#             if 0.75 <= aspect_ratio <= 1.3 and w > 50 and h > 50:  # Filter close-to-square detections with min size

#                 # Draw bounding box around detected face
#                 cv2.rectangle(roi_frame, 
#                                 (bounding_box[0], bounding_box[1]), 
#                                 (bounding_box[0] + bounding_box[2], bounding_box[1] + bounding_box[3]), 
#                                 (0, 255, 0), 2)
                
#                 # Display confidence value on the top left corner of the bounding box
#                 cv2.putText(roi_frame, f"Conf: {float(confidence):.2f}", (bounding_box[0], bounding_box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#                 if not images_cap_status: 
#                     if cooldown_start_time is None:
#                         cooldown_start_time = time.time()  # Start countdown

#                     elapsed_time = time.time() - cooldown_start_time
#                     remaining_time = max(0, 1 - int(elapsed_time))
#                     cv2.putText(frame, f"Capturing in: {remaining_time}s", (roi_x, roi_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
#                     cv2.putText(frame, f"Image Captured: {images_captured}/{img_capture}", (roi_x, roi_y + roi_height + 30),  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)  # Display capture count
                
#                     if elapsed_time >= 1 and images_captured < img_capture:
#                         # Crop the face region from the ROI frame
#                         cropped_face = roi_frame[y:y+h, x:x+w]

#                         # Resize the cropped face to the target dimensions
#                         resized_face = cv2.resize(cropped_face, (140, 180))

#                         cropped_face_path = os.path.join(
#                             os.getcwd(),
#                             'static/face_recognition/collect_face_img',
#                             f'collect_face_{images_captured + 1}.png'
#                         )
#                         cv2.imwrite(cropped_face_path, resized_face)

#                         captured_images.append(cropped_face_path)

#                         # 🔁 emit both count and person_id (id from register)
#                         socketio.emit('res_collect_face_img', {
#                             'count': images_captured + 1,
#                             'person_id': person_name,
#                         })

#                         images_captured += 1
#                         cooldown_start_time = time.time()  # Reset countdown for the next capture

#                     if images_captured >= img_capture:
#                         cooldown_start_time = None
#                         images_captured = 0
#                         images_cap_status = True  # All images captured

#                         image2df(captured_images, person_name)

#                         res_collect_face = 'Completed'
#                         socketio.emit('res_collect_face', {'data': res_collect_face})

#                         time.sleep(3)
#                         picam2.close()

#                         # 🔁 Send last captured image path for preview on frontend
#                     if captured_images:
#                         last_img = captured_images[-1]
#                         # Convert absolute path → URL under /static/...
#                         static_root = os.path.join(os.getcwd(), "static")
#                         rel_path = os.path.relpath(last_img, static_root).replace(os.sep, "/")
#                         socketio.emit('res_collect_face_preview', {
#                             'image_url': f'/static/{rel_path}',
#                             'person_id': person_name,
#                         })

#                     time.sleep(3)
#                     picam2.close()

#         # Encode the frame in JPEG format
#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame = buffer.tobytes()
#         # Yield the frame and cropped face images
#         yield (b'--frame\r\n'
#                 b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
#     picam2.close()

# def set_up_cap(cap, screen_width, screen_height):
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, screen_width)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, screen_height)
    # cap.set(cv2.CAP_PROP_FPS, 60)
    # cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    # return cap