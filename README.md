# 🚀 Smart Attendance BYOD (Hybrid-Edge Architecture)

Welcome to a next-generation, decentralized smart attendance system. Built with the intelligence and precision of high-end AI frameworks, this project modernizes classroom management by replacing manual roll calls with a lightning-fast YOLOv8 facial recognition engine.

Instead of relying on expensive cloud computing or massive centralized servers, this system utilizes a **Hybrid-Edge Architecture**. It processes heavy video streams entirely on a local network (Edge) while exposing a lightweight, mobile-friendly interface to the internet (Cloud) via secure tunneling.

---

## 🧠 System Architecture & Data Flow

The system is decoupled into four specific hardware nodes:

1. **The Edge Server (Your PC/Mac):** The core processor. Runs the Python Flask web app, the SQLite database (`attendance_v2.db`), and the custom YOLOv8 `FaceEngineV2`.
2. **The Sensor Node (Camera Phone):** A localized eye. A smartphone running IP Webcam or DroidCam, streaming live HD video over the local Wi-Fi strictly to the Edge Server.
3. **The Cloud Bridge (Ngrok):** A secure reverse-proxy tunnel that exposes the Edge Server's local port (5000) to the public internet securely.
4. **The Client Node (Professor's App):** A lightweight Android APK wrapper that connects to the Cloud Bridge. The professor acts as the admin, starting sessions and verifying AI results seamlessly from their mobile data network.

---

---

## 🏗️ Real-World Deployment & Cost Analysis

In a professional campus-wide deployment, the system follows a **Centralized Edge Architecture**. This removes the burden of processing from the teacher's device and ensures 24/7 availability. 

### Estimated Cost for a Single Classroom Deployment

| Component | Professional Specification | Purpose | Estimated Cost (INR) |
| :--- | :--- | :--- | :--- |
| **Edge Server Node** | Dedicated Mini-PC (Intel i5/Ryzen 5, 16GB RAM) | Centralized AI processing & Database hosting. | ₹35,000 - ₹45,000 |
| **PoE Sensor Node** | 4MP Wide-Angle PoE IP Camera | High-definition facial data capture. | ₹4,000 - ₹6,500 |
| **Network Backbone** | PoE Switch & Cat6 Cabling | Powering the camera & high-speed data transfer. | ₹3,000 - ₹5,000 |
| **Mounting & Infrastructure** | Wall mounts & Conduit pipes | Permanent, tamper-proof installation. | ₹1,500 - ₹2,500 |
| **Total Deployment Cost** | **Professional Grade Setup** | **Scalable Campus Infrastructure** | **₹43,500 - ₹59,000** |

---

## 🧱 Why These Components are Necessary



### 1. Dedicated Edge Server
While a personal laptop can run a simulation, a real-world system requires a **Dedicated Edge Server**. This server remains physically in the department or classroom, allowing it to handle heavy YOLOv8 matrix multiplications 24/7 without overheating or interrupting a professor's personal work. It acts as the local "Brain" that keeps data within the campus network, ensuring low latency and high privacy.

### 2. PoE (Power over Ethernet) Sensor Nodes
For a permanent setup, we use **PoE IP Cameras** instead of wireless devices. PoE is critical because it carries both power and high-speed data over a single Ethernet cable. This eliminates the need for electrical outlets near the ceiling and ensures the video stream is never interrupted by Wi-Fi interference or battery death, which is vital for accurate AI detection.

### 3. Gigabit Network Backbone
A smart attendance system is only as fast as its slowest link. Because we are transmitting high-definition frames for facial analysis, a **Gigabit Switch** and **Cat6 cabling** are necessary to prevent "packet loss" or frame lag. This ensures the AI Engine receives crystal-clear images in real-time for immediate processing.

### 4. Centralized BYOD Mobile Client (The APK)
The Android application allows the system to remain "headless." The professor does not need to interact with the server directly. By using their own mobile device to trigger the session, the system achieves a **Bring Your Own Device (BYOD)** efficiency—reducing hardware costs for the college while providing a familiar, easy-to-use interface for the faculty.
---

## 💻 The Ultimate Setup Guide (From Scratch)

Whether you are on Windows, macOS, or Linux, follow these steps to build the architecture locally. 

### Phase 1: Environment Setup

**1. Clone the Repository**
```bash
git clone [https://github.com/YOUR_GITHUB_USERNAME/smart-attendance.git](https://github.com/YOUR_GITHUB_USERNAME/smart-attendance.git)
cd smart-attendance
```

**2. Create the Virtual Environment**
* **Mac/Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
* **Windows:**
  ```cmd
  python -m venv venv
  venv\Scripts\activate
  ```

**3. Install Core Dependencies**
```bash
pip install flask opencv-python ultralytics werkzeug
```

**4. Download the AI Weights & Initialize Database**
To keep this repo lightweight, the heavy YOLO weights and database are generated locally. Run these two scripts:
```bash
python download_yolo_face.py
python setup_db_v2.py
```

---

### Phase 2: Data Registration

Before scanning faces, the AI needs blueprints. We use a dedicated Desktop UI to register students.

1. Run the admission portal:
   ```bash
   python admission_v2.py
   ```
2. A graphical window will open. Enter a student's Name, Roll Number, Year, and Section.
3. The webcam will open. Have the student look at the camera and press `SPACE` to capture their facial blueprint. 
4. The system will automatically encode and save the data to the SQLite database and the `known_faces/` folder.

---

### Phase 3: The Sensor Node (Camera)

1. Download **IP Webcam** or **DroidCam** from the Google Play Store / Apple App Store on a spare phone.
2. Connect both your PC and the Camera Phone to the **exact same Wi-Fi network**.
3. Start the camera server on the phone app and note the IPv4 Address (e.g., `http://192.168.1.15:8080/video`).
4. Open `web_app.py` in your code editor. Go to line 16 and update the `CAMERA_URL` variable with your phone's IP address.

---

### Phase 4: Booting the Engine

Start the main Flask backend on your Edge Server:
* **Mac/Linux:** `python3 web_app.py`
* **Windows:** `python web_app.py`

*You can now view the system locally by opening a web browser and going to `http://127.0.0.1:5000`.*

---

### Phase 5: Going Global & Building the App

To allow the professor to use this on their 5G mobile data, we tunnel the local server to the internet.

**1. Start the Cloud Bridge**
Install [Ngrok](https://ngrok.com/) on your PC, authenticate your account, and run:
```bash
ngrok http 5000
```
*(Copy the secure `https://...ngrok-free.app` URL it generates).*

**2. Build the Native Android App**
1. Go to [Median.co](https://median.co).
2. Paste your secure Ngrok URL into the website builder.
3. Go to **Native Navigation** and ensure the top bar and sidebars are empty/disabled (to allow our custom web UI to take over).
4. Click **Build & Download APK**.
5. Install the APK on your phone.

You can now open the app from anywhere in the world, log in as faculty, and tap "Start Session" to trigger the local AI engine on your PC!

---

## ⚙️ Administrative Tools

* **Factory Reset:** If you are starting a new semester and need to wipe all attendance records, database tables, and facial blueprints, run `python factory_reset.py`. *Warning: This cannot be undone.*
* **Security:** The `.gitignore` is pre-configured to block pushing your private database and student photos to GitHub.