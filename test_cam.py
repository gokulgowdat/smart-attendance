import cv2

# Replace this with the URL from your phone app, keeping /video at the end
CAMERA_URL = "http://192.168.1.3:4747/video"

print(f"Attempting to connect to {CAMERA_URL}...")

cap = cv2.VideoCapture(CAMERA_URL)

if not cap.isOpened():
    print("Error: Could not open the camera stream. Check the URL and network connection.")
    exit()

print("Connection successful! Press 'q' on your keyboard to close the video window.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Show the video feed
    cv2.imshow("PoE Camera Simulation Test", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
