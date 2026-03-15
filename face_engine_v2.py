import cv2
import face_recognition
import numpy as np
from ultralytics import YOLO
import os

class FaceEngineV2:
    def __init__(self, yolo_model_path="yolov8n-face.pt", known_faces_dir="known_faces"):
        print("[AI Engine] Booting up YOLOv8-Face...")
        self.detector = YOLO(yolo_model_path)
        self.known_faces_dir = known_faces_dir
        self.known_encodings = []
        self.known_labels = []
        
        # Create directories if they don't exist
        os.makedirs(os.path.join(self.known_faces_dir, "faculty"), exist_ok=True)
        os.makedirs(os.path.join(self.known_faces_dir, "students"), exist_ok=True)
        
        self.load_known_faces()

    def load_known_faces(self):
        print(f"[AI Engine] Scanning '{self.known_faces_dir}' for blueprints...")
        self.known_encodings.clear()
        self.known_labels.clear()
        
        valid_extensions = ('.jpg', '.jpeg', '.png')
        
        # os.walk allows us to look inside the faculty and students subfolders!
        for root_dir, dirs, files in os.walk(self.known_faces_dir):
            for filename in files:
                if filename.lower().endswith(valid_extensions):
                    label = os.path.splitext(filename)[0] # e.g., 'gagan'
                    filepath = os.path.join(root_dir, filename)
                    
                    image = face_recognition.load_image_file(filepath)
                    encodings = face_recognition.face_encodings(image)
                    
                    if len(encodings) > 0:
                        self.known_encodings.append(encodings[0])
                        self.known_labels.append(label)
                        # Just a clean print statement to show where it found the file
                        folder_name = os.path.basename(root_dir)
                        print(f"  -> Loaded [{folder_name}]: {label}")
                    else:
                        print(f"  -> WARNING: No face found in {filename}. Skipping.")
                        
        print(f"[AI Engine] Ready. Loaded {len(self.known_labels)} known faces.")

    def process_frame(self, frame):
        """
        Takes a frame, runs YOLO for fast detection, 
        and face_recognition for identification.
        """
        results = self.detector(frame, verbose=False)
        recognized_labels = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                css_box = (y1, x2, y2, x1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                encodings = face_recognition.face_encodings(rgb_frame, [css_box])
                
                if len(encodings) > 0:
                    encoding = encodings[0]
                    if len(self.known_encodings) > 0:
                        distances = face_recognition.face_distance(self.known_encodings, encoding)
                        best_match_index = np.argmin(distances)
                        
                        if distances[best_match_index] < 0.6:
                            matched_label = self.known_labels[best_match_index]
                            recognized_labels.append(matched_label)
                            
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame, matched_label, (x1, y1 - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                            continue
                            
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, "Unknown", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                            
        return frame, list(set(recognized_labels))
