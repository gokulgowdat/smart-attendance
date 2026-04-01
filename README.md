# 🚀 Smart Attendance BYOD (Hybrid-Edge Architecture V2)

Welcome to a next-generation, decentralized smart attendance system. Built with the intelligence and precision of high-end AI frameworks, this project modernizes classroom management by replacing manual roll calls with a lightning-fast YOLOv8 facial recognition engine.

Instead of relying on expensive cloud computing or massive centralized servers, this system utilizes a **Hybrid-Edge Architecture**. It processes heavy video streams entirely on a local network (Edge) while exposing a lightweight, mobile-friendly interface to the internet (Cloud) via secure tunneling.

---

## ✨ What's New in V2: The Smart Sensor & CLAHE Engine
This system has been upgraded to handle harsh real-world classroom environments:
* **Custom 4K WebRTC Sensor:** We dropped third-party camera apps. The system now features a custom, browser-based sensor node (`/sensor`) that forces smartphone cameras into 4K resolution and continuous hardware auto-focus to catch faces at the back of massive lecture halls.
* **Interactive Gesture Controls:** The camera operator can pinch-to-zoom and swipe up/down to manually adjust optical brightness on the fly before sending the frame to the AI.
* **Military-Grade Auto-Lighting (CLAHE):** Before the AI analyzes a frame, the Python backend intercepts it and applies Contrast Limited Adaptive Histogram Equalization (CLAHE). This mathematically balances shadows and highlights, exposing faces hidden in terrible classroom lighting without blowing out the bright spots.

---

## 🧠 System Architecture & Data Flow

The system is decoupled into four specific hardware nodes:

1. **The Edge Server (Your PC/Mac):** The core processor. Runs the Python Flask web app, the SQLite database (`attendance_v2.db`), the CLAHE image processor, and the custom YOLOv8 `FaceEngineV2`.
2. **The Sensor Node (Camera Phone):** A localized eye. A smartphone acting as a wireless webcam by navigating to the local `/sensor` web route. It captures high-res frames and sends them via WebRTC/Base64 to the Edge Server.
3. **The Cloud Bridge (Ngrok):** A secure reverse-proxy tunnel that exposes the Edge Server's local port (5000) to the public internet securely.
4. **The Client Node (Professor's App):** A lightweight Android APK wrapper that connects to the Cloud Bridge. The professor acts as the admin, starting sessions and verifying AI results seamlessly from their mobile data network.

---

## 🔬 Technical Workflow: How the AI "Simulation" Works Step-by-Step

When a professor initiates an attendance session, a complex orchestration of front-end web technologies, network protocols, and back-end computer vision algorithms fires off in seconds. Here is the exact lifecycle of a scan:

**Step 1: Session Initiation (The Admin)**
The professor logs into their dashboard, selects their subject, year, and room, and clicks "Start Attendance." The SQLite database logs a new session with the status `'ONGOING'`.

**Step 2: Sensor Calibration (The Hardware)**
A volunteer or TA opens the Sensor Node (`/sensor`) on a smartphone. The browser's `getUserMedia` API requests maximum hardware resolution (up to 4K) and continuous auto-focus. The operator uses touch gestures (pinch/swipe) to frame the crowd perfectly.

**Step 3: Capture & Transmission (The Network)**
Every 15 seconds, the Sensor Node fires a "shutter." It draws the current video frame to a hidden HTML5 `<canvas>`, applies the user's manual brightness/zoom constraints, encodes the image as a Base64 JPEG, and POSTs it via an asynchronous JavaScript `fetch` payload to the Edge Server.

**Step 4: Pre-Processing & CLAHE (The Intercept)**
The Flask backend receives the Base64 payload, decodes it into a raw NumPy array, and converts it to standard RGB. It then isolates the "Lightness" channel and applies **CLAHE**. This flattens the image's histogram, rescuing faces that are backlit by windows or shrouded in the shadows of the lecture hall. 

**Step 5: YOLOv8 Inference (The Brain)**
The enhanced image is passed to `FaceEngineV2`. The YOLOv8 neural network scans the image for facial bounding boxes. Once faces are isolated, the system extracts facial embeddings and compares them against the known databases of registered students using Euclidean distance mapping. *Fallback Check:* If no faces are found, the system auto-rotates the image 90 degrees clockwise and counter-clockwise to check for landscape/portrait orientation mismatches.

**Step 6: Database Logging & Visual Feedback (The Return)**
Matched faces are stripped of their system tags (e.g., `_1`, `_2`) and cross-referenced with the active session. The SQLite database marks them as `'Present'` and updates their `last_seen` timestamp. Simultaneously, OpenCV draws green bounding boxes around recognized faces, encodes a low-res preview image, and sends it *back* to the Sensor Node so the operator knows the scan was successful.

**Step 7: Manual Verification (The Human Element)**
The professor clicks "End Class." The system pulls the final tally and presents a clean UI matrix of Present vs. Absent students. The professor has the ultimate authority to manually override the AI via override checkboxes before finalizing the database commit.

---

## 🏗️ Real-World Deployment & Cost Analysis

In a professional campus-wide deployment, the system follows a **Centralized Edge Architecture**. This removes the burden of processing from the teacher's device and ensures 24/7 availability. 

The following model evaluates the investment required for a medium-sized campus deployment of 50 rooms.

| Component | Professional Specification | Purpose | Estimated Cost (INR) |
| :--- | :--- | :--- | :--- |
| **Central AI Server** | High-core CPU, 64GB RAM, **NVIDIA RTX 4070 GPU** | Centralized high-speed AI inference & Database hosting. | ₹1,50,000 |
| **PoE Sensor Nodes** | 4MP Wide Dynamic Range (WDR) PoE IP Dome Cameras | Capturing high-definition facial data from 50 rooms (₹4,000 x 50). | ₹2,00,000 |
| **Network Infrastructure** | 24-Port PoE Switches & Category 6 (Cat6) Cabling | Providing power and data connectivity over a Star Topology. | ₹60,000 |
| **Total Campus Investment** | **Full 50-Room Professional Deployment** | **Scalable, Enterprise-Grade Infrastructure.** | **₹4,10,000** |

> **Note on Scalability:** In this centralized model, adding additional classrooms is highly cost-effective, requiring only the purchase of a single camera (~₹4,000) rather than a full computing module per room.

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
pip install flask opencv-python ultralytics werkzeug numpy
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
3. Use the webcam or upload multiple photos. The system will automatically encode and save the data to the SQLite database and the `known_faces/` folder.

---

### Phase 3: Booting the Engine & Sensor Node

**1. Start the Flask Backend:**
* **Mac/Linux:**
  ```bash
  python3 web_app.py
  ```
* **Windows:**
  ```cmd
  python web_app.py
  ```

**2. Connect the Sensor Camera:**
1. Connect your smartphone to the **exact same Wi-Fi network** as your PC.
2. Find your PC's local IPv4 address (e.g., `192.168.1.15`).
3. Open Safari or Chrome on your phone and navigate to `http://YOUR_PC_IP:5000/sensor`.
4. Grant camera permissions. Your phone is now an active AI Sensor Node!

---

### Phase 4: Going Global & Building the App

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