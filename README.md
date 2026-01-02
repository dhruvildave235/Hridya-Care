# ❤️ HridyaCare  
**Smart, Accessible & Context-Aware Digital Health Monitoring**

HridyaCare is a browser-based digital health platform designed to make **heart health, stress, lifestyle, and environmental health monitoring accessible to everyone**, using just a smartphone and the web.  
No wearables. No subscriptions. No hospital visits for basic screening.

---

## 🌍 Problem Statement

Today’s health monitoring solutions are either:
- **Device-dependent** (require wearables),
- **Data-heavy but insight-poor** (just numbers, no meaning),
- **Expensive or inaccessible**, especially in remote or low-resource areas.

People often realize health issues **only after symptoms become serious**.

HridyaCare bridges this gap by combining **real-time physiological signals, lifestyle patterns, stress assessment, and environmental factors** to provide **clear, human-readable health insights** — instantly.

---

## 💡 What Makes HridyaCare Unique?

- Measures **heart rate using a phone camera** (rPPG-based)
- Links health with **real-world context** (AQI, lifestyle, age)
- Includes **clinically recognized stress assessment**
- Provides **actionable insights**, not just raw data
- Works on **any browser-enabled smartphone**
- Optional **telehealth support with verified health coaches**

---

## 🧠 Core Features

### ❤️ Heart Rate Monitoring
- Real-time heart rate measurement using smartphone camera (rPPG-based)
- No wearables required
- Achieved accuracy:
  - **Best case:** ±4 BPM  
  - **Worst case:** ±8 BPM
- Stores the **last 7 heart rate measurements** for short-term tracking
- Displays **clear trends** showing whether heart rate is **upward, downward, or steady**
- Focuses on **trends rather than isolated readings** for better insight
- Provides **context-aware guidance**:
  - **Upward trend:** rest, hydrate, breathing exercises, reduce pollution exposure  
  - **Downward trend:** recovery and normalization  
  - **Steady trend:** stable condition, maintain habits
- **Uniquely integrates real-time city AQI** to show how air pollution affects heart rate
- Allows users to **instantly consult a verified health coach** for expert support
- Designed after **reviewing and validating insights from multiple peer-reviewed research papers**

---

### 🌫️ “How My City AQI Affects My Heart” (Unique Feature)
- Fetches real-time city AQI
- Displays:
  - AQI
  - PM2.5
  - PM10
- Explains how air quality can influence heart rate
- Converts environmental data into **health impact insights**

---

### 😌 Stress Check (Clinically Backed)
- Uses the **Perceived Stress Scale (PSS)**
- Developed by **Cohen et al. (1983)**
- Globally recognized and clinically validated
- Measures:
  - Perceived unpredictability
  - Lack of control
  - Mental overload
- Simple **10-question assessment**
- Generates an **easy-to-understand stress score**
- **Unique feature:** categorizes results into **5 distinct stress levels**, each paired with **clear, practical solutions**
- Visualizes stress dimensions through a **radar chart**, making stress patterns easy to understand at a glance

---

### 🧬 Lifestyle Analysis
- Built on **World Health Organization (WHO) lifestyle assessment matrices**
- Uses **WHO-defined benchmarks and risk thresholds** to ensure medically reliable evaluation
- Analyzes:
  - Physical activity levels  
  - Sleep quality & duration  
  - Daily lifestyle habits  
  - Sedentary behavior patterns  
- **Visually flags weak lifestyle areas** for instant understanding
- Transforms lifestyle inputs into **clear, actionable health recommendations**

---

### 📊 Health Insights & Reports
- Combines:
  - Heart rate
  - Stress level
  - Lifestyle score
  - Environmental exposure
- Generates:
  - Visual insights
  - Trend-based analysis
  - Downloadable reports
- Focuses on **“why” health changes**, not just “what”

---

### 🩺 Telehealth Support
- Access to **verified health coaches**
- Coaches can:
  - View user reports (with consent)
  - Analyze health trends
  - Provide personalized guidance remotely
- **Admin verifies coach credentials** before approval to ensure trust and safety
- Especially helpful for **elderly and higher-aged users**, enabling professional support for **basic wellness without hospital visits**

---

## 👥 User Roles

### 👤 User
- Measure heart rate
- Check stress levels
- Analyze lifestyle
- View AQI impact on health
- Track reports and trends
- Consult health coaches

### 🧑‍⚕️ Health Coach
- Secure dashboard
- View assigned user reports
- Provide guidance
- No access without admin approval

### 🛠️ Admin
- Verify and approve health coaches
- Manage platform data
- Ensure system integrity

---

(Admin and Coach dashboards operate independently and are non-linear.)

---

## 🧪 Technology Stack

### Frontend
- HTML5
- CSS3 (Glassmorphism / Futuristic UI)
- JavaScript (ES Modules)
- Chart.js

### Backend
- Flask (Python)
- REST APIs

### Database
- PostgreSQL

### 🔌 APIs Used

- **Air Quality Data (AQI & Pollutants)**  
  - (AQICN / WAQI) API
  - Uses the official **`AQICN_API_TOKEN`** for authenticated access
  - Fetches **real-time city AQI and pollutant data** using geographic coordinates
  - **Trusted globally**; for India, AQI data is sourced from **(CPCB) government monitoring stations**
  - Enables correlation of **air pollution levels with heart rate and cardiovascular stress**

---

## 🔐 Privacy & Ethics
- No medical diagnosis claims
- User data remains private
- Coach access only after admin verification
- Designed as a **decision-support system**, not a replacement for doctors

---

## 🚀 Impact & Vision

- Breaks the **wealth and access barrier in healthcare**
- Enables **early awareness before conditions worsen**
- Makes health monitoring:
  - Proactive
  - Preventive
  - Personalized
- Anyone with a phone and browser can access professional-grade insights

---

## 📌 Future Scope

- **Long-term trend prediction** for proactive cardiovascular risk awareness  
- **Personalized alerts** based on health trends and environmental exposure  
- **Integration with public health systems** to support population-level insights  
- **Expanded environmental health indicators** (pollution, heat, lifestyle factors)

- Currently, **there is no unified government platform** that continuously links daily heart health with real-time environmental data  
- Existing public health data collection for **elderly populations is often infrequent (e.g., periodic checkups every few months)** and largely **reactive**, with limited follow-up or actionable feedback  
- HridyaCare aims to **bridge this gap** by enabling **continuous, at-home monitoring**, early insights, and timely guidance—before issues escalate

---

## 📄 Disclaimer

HridyaCare is a health monitoring and awareness platform.  
It does **not provide medical diagnoses** and should not replace professional medical consultation.

---

## 👨‍💻 Project Name

**HridyaCare**  
_Heart health, understood — not just measured._

© 2025 HridyaCare. All rights reserved.
Developed by Om J. Bhinsara and Team.  
