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

The following model evaluates the investment required for a medium-sized campus deployment of 50 rooms.

| Component | Professional Specification | Purpose | Estimated Cost (INR) |
| :--- | :--- | :--- | :--- |
| **Central AI Server** | High-core CPU, 64GB RAM, **NVIDIA RTX 4070 GPU** | Centralized high-speed AI inference & Database hosting. | ₹1,50,000 |
| **PoE Sensor Nodes** | 4MP Wide Dynamic Range (WDR) PoE IP Dome Cameras | Capturing high-definition facial data from 50 rooms (₹4,000 x 50). | ₹2,00,000 |
| **Network Infrastructure** | 24-Port PoE Switches & Category 6 (Cat6) Cabling | Providing power and data connectivity over a Star Topology. | ₹60,000 |
| **Total Campus Investment** | **Full 50-Room Professional Deployment** | **Scalable, Enterprise-Grade Infrastructure.** | **₹4,10,000** |
> **Note on Scalability:** In this centralized model, adding additional classrooms is highly cost-effective, requiring only the purchase of a single camera (~₹4,000) rather than a full computing module per room.
---

## 🧱 Why These Components are Necessary

### 1. The NVIDIA RTX 4070 "Smart Core"
The **NVIDIA RTX 4070** is the operational linchpin of the system. Equipped with 4th-generation Tensor cores, it executes the dense matrix multiplications required for **YOLOv8** (crowd detection) and **Face Recognition** (encoding matching) asynchronously across dozens of classrooms. Without this dedicated GPU, CPU-only processing would result in massive latency, rendering a large-scale system unusable for simultaneous lectures.

### 2. High-Resolution PoE Sensor Nodes
Real-world deployment necessitates **Power over Ethernet (PoE) IP Cameras**. These sensors use H.265 compression to transmit high-definition 4MP frames while consuming minimal bandwidth. PoE is critical because it carries both power and data over a single Ethernet cable, ensuring the system is immune to Wi-Fi instability and eliminating the need for electrical outlets at every ceiling-mounted camera point.

### 3. Gigabit Network Backbone
A professional **Star Network topology** utilizing Cat6 cabling and a 1 Gigabit Ethernet uplink is required to aggregate traffic from multiple floors. This backbone prevents network saturation even if all 50 classrooms trigger attendance sessions simultaneously, ensuring the central server receives clear video streams without frame loss or lag.

### 4. Frictionless BYOD Mobile Integration
The **Bring Your Own Device (BYOD)** approach utilizes the professor’s smartphone as a secure authentication and trigger mechanism. This eliminates the need for expensive, unhygienic wall-mounted biometric terminals. By shifting to "passive observation" via overhead cameras, the system eradicates the queuing bottlenecks inherent to traditional biometric kiosks.

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