# 🌙 Moonlit Satellite Tracker  
### Real-Time 3D ISS & Multi-Satellite Tracking with PyDeck Globe, Orbits, Alerts & ECI Logging

**Moonlit Satellite Tracker** is a powerful real-time satellite tracking system built using  
**Streamlit + PyDeck + Skyfield + Celestrak TLE**.

It displays a **3D interactive globe** with:

- 🛰 Real-time satellite positions  
- 🌍 3D Globe visualization  
- ✨ Orbit prediction (future path)  
- 🚀 Velocity vectors  
- 📌 Ground stations  
- 👣 Satellite trail history  
- ⚠ Alerts (distance / elevation)  
- 📄 ECI logging + CSV export  

This project gives a professional NASA-style satellite tracking dashboard.

---

# 📌 PART 1 — Features

### 🛰 Real-Time Tracking  
- Multiple satellites at once  
- ISS by default  
- Auto refresh every X seconds  

### 🌍 3D Visualization  
- PyDeck `_GlobeView` for interactive earth  
- Trail line (history)  
- Orbit prediction (future projection)  
- Footprint (visibility circle)  
- Satellite velocity vector  

### 🔔 Alert System  
- **Distance alert** (km)  
- **Elevation alert** (deg)  
- Optional **sound alert** using `playsound`  

### 📈 ECI Data Logging  
Logs for every satellite:  
- px, py, pz  
- vx, vy, vz  
- lat, lon, altitude  
- Timestamp  
- CSV download  

### 📡 Ground Stations  
- Add/Edit/Delete observer locations  
- Auto visibility & alert calculations  

### 📡 TLE Autoload System  
Loads from Celestrak:  
- stations  
- visual  
- amateur  
- weather  
- NOOA  
- science  
- fallback ISS TLE  

---

# 📌 PART 2 — Technologies Used

### 🐍 Python Libraries
| Library | Purpose |
|--------|---------|
| **Streamlit** | UI dashboard |
| **PyDeck** | 3D globe rendering |
| **Skyfield** | Satellite orbit math |
| **Requests** | Fetch TLE from Celestrak |
| **Pandas** | Logging & CSV export |
| **NumPy** | Numerical calculations |
| **Playsound** | Alert sounds |
| **Datetime** | Timestamps, UTC time |

### 🌌 Space Data Sources  
- **Celestrak NORAD TLE datasets**  
- **Skyfield eph. `de421.bsp`**  

---

# 📌 PART 3 — Installation & How To Run

## 🔧 Step 1 — Clone Repository
```bash
git clone https://github.com/your-username/Moonlit-Satellite-Tracker.git
cd Moonlit-Satellite-Tracker
```

## 🧱 Step 2 — Create Virtual Environment (Recommended)
### Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### Mac / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

---

# 📦 Step 3 — Install Python Libraries

Create a `requirements.txt` or install manually.

### Requirements:
```
streamlit
pydeck
skyfield
numpy
pandas
requests
playsound
```

### Install:
```bash
pip install -r requirements.txt
```

or:
```bash
pip install streamlit pydeck skyfield numpy pandas requests playsound
```

---

# ▶ Step 4 — Run the Application

Run Streamlit:

```bash
streamlit run tracker.py
```

Streamlit will open:

```
http://localhost:8501
```

Click it → your **3D satellite tracker UI loads**.

---

# 📁 Project Structure

```
📦 Moonlit-Satellite-Tracker
 ┣ 📜 README.md
 ┣ 📜 tracker.py
 ┣ 📜 requirements.txt   (optional)
 ┗ 📁 .skyfield/          (auto-created)
```

---

# 💡 How It Works (Internally)

### 1️⃣ TLE Fetching  
It tries 3 Celestrak URLs.  
If all fail → loads offline ISS TLE.

### 2️⃣ Skyfield Orbital Math  
- `EarthSatellite()` parses TLE  
- `.at(t)` computes ECI position  
- `.subpoint()` gives lat/lon/alt  
- `.altaz()` gives elevation/azimuth  

### 3️⃣ PyDeck Globe Rendering  
Layers used:
- `ScatterplotLayer` → satellites  
- `PathLayer` → trail + orbit + velocity  
- `PolygonLayer` → footprint  
- `_GlobeView` → Earth  

### 4️⃣ Real-Time Alerts  
Every cycle checks:

```
if elevation >= alert_elev
if distance <= alert_dist
```

If true → warning + optional sound.

### 5️⃣ ECI Logging  
Every refresh saves:

```
lat, lon, alt
px, py, pz
vx, vy, vz
timestamp
```

CSV export button available.

---

# 🧪 Compatibility

- Tested on **Python 3.10 – 3.12**  
- Windows 10 / 11  
- Streamlit on Chrome/Edge  
- Works offline after first ephemeris download  

# ⭐ Support This Project  
If you like Moonlit Satellite Tracker, please give the repo a **⭐ STAR** on GitHub!

---
