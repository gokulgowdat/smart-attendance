# 🚀 Smart Attendance BYOD (Hybrid-Edge Architecture)

Welcome to a high-tier smart attendance system. This project modernizes classroom management by replacing manual roll calls with a decentralized, AI-powered Face Recognition engine. 

Instead of relying on expensive cloud computing or massive centralized servers, this system utilizes a **Hybrid-Edge Architecture**. It processes heavy video streams entirely on a local network (Edge) while exposing a lightweight, mobile-friendly interface to the internet (Cloud).

---

## 🧠 The Architecture & Workflow

The system is divided into four completely decoupled nodes:

1. **The Edge Server (Laptop/PC):** The brain. Runs the Python Flask backend, the SQLite database, and the YOLOv8 FaceEngineV2.
2. **The Sensor Node (Camera):** A localized eye. A smartphone running an IP Webcam (or a dedicated PoE Camera) streaming video over the local LAN to the Edge Server. 
3. **The Cloud Bridge (Ngrok/Local DNS):** A secure tunnel that exposes the Edge Server's port to the public internet.
4. **The Client Node (Android APK):** A lightweight native wrapper that connects to the Cloud Bridge. The professor acts as the admin, starting sessions and verifying AI results via their mobile device.

**The Data Flow:** When the professor taps "Start Session" on their phone, the Edge Server wakes up a background thread. This thread silently pulls frames from the local Sensor Node, runs YOLOv8 facial recognition, matches blueprints, and logs attendance into the database. When the class ends, the professor verifies the roster on their phone and locks the data.

---

## 🛠️ Physical Deployment & Estimated Cost

To deploy this physically in a real-world classroom, the cost is drastically lower than traditional biometric scanners. 

| Component | Description | Estimated Cost (USD) | Estimated Cost (INR) |
| :--- | :--- | :--- | :--- |
| **Edge Server** | The professor's existing laptop or a dedicated classroom mini-PC (e.g., Raspberry Pi 5 or basic NUC). | $0 (BYOD) - $150 | ₹0 - ₹12,000 |
| **Sensor Node** | Option A: An old Android smartphone running DroidCam on a tripod.<br>Option B: A ceiling-mounted PoE (Power over Ethernet) IP Security Camera. | $0 - $40 | ₹0 - ₹3,500 |
| **Local Network** | A basic gigabit Wi-Fi router to handle the heavy local video stream without relying on spotty college Wi-Fi. | $25 | ₹2,000 |
| **Total Startup Cost** | A complete, military-grade local network setup. | **~$25 - $215** | **₹2,000 - ₹17,500** |

---

## 💻 Installation & Setup Guide

Want to run this simulation on your own machine? Follow these exact steps.

### 1. Clone the Repository
git clone [https://github.com/YOUR_GITHUB_USERNAME/smart-attendance.git](https://github.com/YOUR_GITHUB_USERNAME/smart-attendance.git)
cd smart-attendance

### 2. Setup the Virtual Environment
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

### 3. Install Dependencies
pip install flask opencv-python ultralytics werkzeug


### 4. Download the AI Weights
python3 download_yolo_face.py

### 5. Initialize the Database
Generate a fresh SQLite database and the necessary image directories (known_faces/students and known_faces/faculty):
python3 setup_db_v2.py

### 6. Boot the System
Step A: Open your IP Webcam/DroidCam app on your phone, note the local IP address, and update the CAMERA_URL variable inside web_app.py.
Step B: Start the main server:
python3 web_app.py

Step C: Access the admin panel in your browser at http://localhost:5000, register a faculty account, upload your photo, and start your first AI session!

(Optional: To make the web app accessible globally on a mobile phone, run ngrok http 5000 in a separate terminal and use the generated forwarding URL).