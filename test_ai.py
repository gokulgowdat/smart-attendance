import cv2
from face_engine_v2 import FaceEngineV2

# --- UPDATE THIS TO YOUR PHONE'S URL ---
CAMERA_URL = "http://192.168.1.3:4747/video"

print("Initializing AI Engine...")
engine = FaceEngineV2()

print(f"Connecting to Camera at {CAMERA_URL}...")
cap = cv2.VideoCapture(CAMERA_URL)

if not cap.isOpened():
    print("Error: Could not open the camera stream.")
    exit()

print("Connection successful! Point the camera at yourself or your group mates.")
print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Pass the frame to our AI Engine!
    processed_frame, recognized_students = engine.process_frame(frame)

    # Show the result
    cv2.imshow("AI Vision Test", processed_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
