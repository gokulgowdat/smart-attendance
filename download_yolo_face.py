import urllib.request
import os

# Updated to a stable mirror because the original GitHub link was moved
url = "https://huggingface.co/junjiang/GestureFace/resolve/main/yolov8n-face.pt"
filename = "yolov8n-face.pt"

print(f"Downloading {filename} from stable mirror...")
try:
    urllib.request.urlretrieve(url, filename)
    print("Download complete! YOLOv8-Face is ready.")
except Exception as e:
    print(f"An error occurred: {e}")
