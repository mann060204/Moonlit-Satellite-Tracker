import streamlit as st
import pydeck as pdk
import time
import math
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from skyfield.api import Loader, EarthSatellite, wgs84, load as skyload

# Try sound
try:
    from playsound import playsound
    SOUND_OK = True
except:
    SOUND_OK = False

# ============ SKYFIELD SETUP ============
load = Loader("./.skyfield")
ts = load.timescale()
eph = skyload("de421.bsp")

# ============ TLE FETCH WITH FALLBACK ============
CELESTRAK_URLS = [
    "https://celestrak.org/NORAD/elements/{}.txt",
    "https://celestrak.com/NORAD/elements/{}.txt",
    "https://www.celestrak.org/NORAD/elements/{}.txt",
]

OFFLINE_TLE = [
    ("ISS (ZARYA)",
     "1 25544U 98067A   23311.54897410  .00010850  00000+0  19855-3 0  9991",
     "2 25544  51.6434 207.4032 0006396  92.0988  19.3512 15.49439215224343")
]

def fetch_tle_group(group):
    for base in CELESTRAK_URLS:
        try:
            text = requests.get(base.format(group), timeout=6).text.splitlines()
            out = []
            i = 0
            while i < len(text) - 2:
                if text[i+1].startswith("1 ") and text[i+2].startswith("2 "):
                    out.append((text[i].strip(), text[i+1].strip(), text[i+2].strip()))
                    i += 3
                else:
                    i += 1
            if out:
                return out
        except:
            continue
    st.warning("TLE fetch failed — using offline ISS TLE.")
    return OFFLINE_TLE

def build_sats(tles):
    out = {}
    for name, l1, l2 in tles:
        try:
            out[name] = EarthSatellite(l1, l2, name, ts)
        except:
            pass
    return out

# ============ GEO HELPERS ============
def subpoint(sat, t):
    p = wgs84.subpoint(sat.at(t))
    return float(p.latitude.degrees), float(p.longitude.degrees), float(p.elevation.m)

def topo(sat, t, lat, lon, elev):
    obs = wgs84.latlon(lat, lon, elevation_m=elev)
    diff = sat.at(t) - obs.at(t)
    alt, az, dist = diff.altaz()
    return float(alt.degrees), float(az.degrees), float(dist.km)

def eci(sat, t):
    at = sat.at(t)
    return at.position.km, at.velocity.km_per_s
# ===========================
#        PRO UI EFFECTS
# ===========================
PRO_UI = """
<style>

html, body {
    background: #0d1117 !important;
    font-family: 'Inter', sans-serif;
    overflow-x: hidden;
}

/* ANIMATED GLOWING MOON ICON */
.glow-moon {
    display: inline-block;
    animation: pulse 4s infinite ease-in-out;
}
@keyframes pulse {
    0% { filter: drop-shadow(0 0 2px #ffe9b0); }
    50% { filter: drop-shadow(0 0 12px #ffefc2); }
    100% { filter: drop-shadow(0 0 2px #ffe9b0); }
}

/* FADE-IN HEADER */
.fade-in {
    animation: fadein 2s ease-out;
}
@keyframes fadein {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* STICKY GLASS FOOTER */
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    text-align: center;
    padding: 12px 0;
    font-size: 15px;
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(10px);
    color: #cfd6e1;
    border-top: 1px solid rgba(255,255,255,0.1);
    animation: glowFooter 3s infinite ease-in-out;
}

@keyframes glowFooter {
    0% { box-shadow: 0 -2px 8px rgba(255,255,255,0.04); }
    50% { box-shadow: 0 -2px 18px rgba(0,200,255,0.25); }
    100% { box-shadow: 0 -2px 8px rgba(255,255,255,0.04); }
}

iframe {
    border-radius: 14px !important;
}

</style>
"""

st.markdown(PRO_UI, unsafe_allow_html=True)

# ===========================
#           TITLE
# ===========================
st.markdown(
    """
    <h1 class="fade-in" style='color:white; font-weight:800; font-size:44px; margin-top: -10px;'>
        <span class="glow-moon">🌙</span> Moonlit Satellite Tracker
    </h1>
    """,
    unsafe_allow_html=True
)

# ===========================
#          FOOTER
# ===========================
st.markdown(
    """
    <div class="footer">
        Created By <b>Mann Monpara</b> © 2025
    </div>
    """,
    unsafe_allow_html=True
)
# ============ STREAMLIT SETUP ============
st.set_page_config(page_title="Ultimate 3D Tracker — Clean", layout="wide")

# ============ SIDEBAR ============
st.sidebar.header("TLE Groups")
groups = st.sidebar.multiselect(
    "Select groups",
    ["stations", "visual", "science", "weather", "amateur", "noaa"],
    default=["stations", "visual"],
)

if st.sidebar.button("Load TLEs", key="load_tles"):
    all_tles = []
    for g in groups:
        all_tles += fetch_tle_group(g)
    st.session_state["sats"] = build_sats(all_tles)
    st.sidebar.success(f"Loaded {len(st.session_state['sats'])} satellites!")

if "sats" not in st.session_state:
    st.session_state["sats"] = build_sats(fetch_tle_group("stations"))

sats = st.session_state["sats"]
sat_list = sorted(sats.keys())

# ============ TRACKING OPTIONS ============
st.sidebar.header("Tracking Options")

selected_sats = st.sidebar.multiselect(
    "Select satellites",
    sat_list,
    default=[n for n in sat_list if "ISS" in n.upper()][:2]
)

refresh_sec = st.sidebar.slider("Refresh interval (sec)", 1, 10, 1)
trail_len = st.sidebar.slider("Trail length (points)", 50, 1500, 600)
follow_cam = st.sidebar.checkbox("Auto-follow first satellite", True)
show_orbit = st.sidebar.checkbox("Show orbit track", True)
orbit_mins = st.sidebar.slider("Orbit projection (minutes)", 5, 180, 90)
show_vel = st.sidebar.checkbox("Velocity vector", True)
show_fp = st.sidebar.checkbox("Visibility footprint", True)

# Alerts
alert_dist = st.sidebar.number_input("Alert distance (km)", 1.0, 20000.0, 500.0)
alert_elev = st.sidebar.number_input("Alert elevation (deg)", 0.0, 90.0, 20.0)
sound_alert = st.sidebar.checkbox("Sound on alert", False)

# Observers
st.sidebar.header("Ground Stations")
if "observers" not in st.session_state:
    st.session_state["observers"] = [
        {"name": "New Delhi", "lat": 28.6139, "lon": 77.2090, "elev": 216},
        {"name": "New York", "lat": 40.7128, "lon": -74.0060, "elev": 10},
    ]

with st.sidebar.expander("Edit Observers"):
    df_obs = pd.DataFrame(st.session_state["observers"])
    edited = st.data_editor(df_obs, num_rows="dynamic", key="edit_obs")
    if st.button("Save Observers", key="save_obs"):
        st.session_state["observers"] = edited.to_dict(orient="records")
        st.sidebar.success("Saved!")

# Trails
if "trails" not in st.session_state:
    st.session_state["trails"] = {}

# ECI log
if "eci_log" not in st.session_state:
    st.session_state["eci_log"] = []

# Clear logs
if st.sidebar.button("Clear Trails & Logs", key="clear_logs"):
    st.session_state["trails"] = {}
    st.session_state["eci_log"] = []
    st.sidebar.success("Cleared!")

# CSV download
df_log = pd.DataFrame(st.session_state["eci_log"])
if st.sidebar.button("Prepare CSV", key="prepare_csv"):
    if df_log.empty:
        st.sidebar.warning("No ECI data yet!")
    else:
        st.sidebar.download_button(
            "Download ECI CSV",
            df_log.to_csv(index=False).encode("utf-8"),
            file_name="eci_log.csv",
            mime="text/csv",
            key="csv_download"
        )

# ============ 3D MAP PLACEHOLDER ============
map_placeholder = st.empty()

# ============ MAIN LOOP ============

while True:
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    t_now = ts.from_datetime(now)
    layers = []
    alerts_msg = []

    # Earth Globe Layer
    layers.append(
        pdk.Layer(
            "GeoJsonLayer",
            data={"type": "Sphere", "radius": 6371000},
            get_fill_color=[20, 30, 60, 255],
        )
    )

    for name in selected_sats:
        sat = sats.get(name)
        if sat is None:
            continue

        lat, lon, alt_m = subpoint(sat, t_now)
        alt_km = alt_m / 1000

        # ---- Trail ----
        trail = st.session_state["trails"].setdefault(name, [])
        trail.append([lon, lat])
        if len(trail) > trail_len:
            trail = trail[-trail_len:]
            st.session_state["trails"][name] = trail

        # Satellite marker
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=[{"lon": lon, "lat": lat, "name": name, "alt": alt_km}],
                get_position='[lon, lat]',
                get_color='[255,0,0]',
                get_radius=50000,
                pickable=True,
            )
        )

        # Trail line
        if len(trail) > 1:
            layers.append(
                pdk.Layer(
                    "PathLayer",
                    data=[{"path": trail}],
                    get_path="path",
                    get_color="[255,165,0]",
                    width_scale=10,
                    width_min_pixels=2,
                )
            )

        # Velocity vector
        if show_vel:
            tf = ts.from_datetime(now + timedelta(seconds=30))
            lat2, lon2, _ = subpoint(sat, tf)
            layers.append(
                pdk.Layer(
                    "PathLayer",
                    data=[{"path": [[lon, lat], [lon2, lat2]]}],
                    get_path="path",
                    get_color="[255,0,255]",
                    width_scale=10,
                    width_min_pixels=2,
                )
            )

        # Orbit projection
        if show_orbit:
            orbit_pts = []
            for sec in range(0, orbit_mins * 60, 20):
                tf = ts.from_datetime(now + timedelta(seconds=sec))
                la, lo, _ = subpoint(sat, tf)
                orbit_pts.append([lo, la])
            layers.append(
                pdk.Layer(
                    "PathLayer",
                    data=[{"path": orbit_pts}],
                    get_path="path",
                    get_color="[0,180,255]",
                    width_scale=6,
                    width_min_pixels=2,
                )
            )

        # Footprint
        if show_fp:
            R = 6371.0
            try:
                ang = math.degrees(math.acos(R / (R + alt_km + 600)))
            except:
                ang = 20
            fp = []
            for a in np.linspace(0, 360, 80):
                rad = math.radians(a)
                la = lat + ang * math.cos(rad)
                lo = lon + (ang * math.sin(rad)) / max(1e-6, math.cos(math.radians(lat)))
                fp.append([lo, la])
            layers.append(
                pdk.Layer(
                    "PolygonLayer",
                    data=[{"polygon": fp}],
                    get_polygon="polygon",
                    get_fill_color="[50,200,50,40]",
                    get_line_color="[50,200,50]",
                    line_width_min_pixels=1,
                )
            )

        # ECI Logging
        pos, vel = eci(sat, t_now)
        st.session_state["eci_log"].append({
            "time": now.isoformat(),
            "sat": name,
            "lat": lat,
            "lon": lon,
            "alt": alt_m,
            "px": pos[0], "py": pos[1], "pz": pos[2],
            "vx": vel[0], "vy": vel[1], "vz": vel[2],
        })

        # Alerts
        for obs in st.session_state["observers"]:
            al, az, dist = topo(sat, t_now, obs["lat"], obs["lon"], obs["elev"])
            if dist <= alert_dist or al >= alert_elev:
                alerts_msg.append(f"⚠ {name} near {obs['name']} — {dist:.1f} km, elev {al:.1f}°")

    # Ground stations
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=st.session_state["observers"],
            get_position='[lon, lat]',
            get_color='[0,200,255]',
            get_radius=60000,
        )
    )

    # CAMERA FOLLOW
    if follow_cam and selected_sats:
        try:
            first_sat = sats[selected_sats[0]]
            la, lo, _ = subpoint(first_sat, t_now)
            view = pdk.ViewState(latitude=la, longitude=lo, zoom=2, pitch=40)
        except:
            view = pdk.ViewState(latitude=0, longitude=0, zoom=0.5)
    else:
        view = pdk.ViewState(latitude=0, longitude=0, zoom=0.5)

    deck = pdk.Deck(
        map_provider=None,
        map_style=None,
        views=[pdk.View(type="_GlobeView", controller=True)],
        initial_view_state=view,
        layers=layers,
    )

    map_placeholder.pydeck_chart(deck)

    # Show Alerts
    for m in alerts_msg:
        st.warning(m)
        if sound_alert and SOUND_OK:
            try:
                playsound("beep.mp3", block=False)
            except:
                pass

    time.sleep(refresh_sec)
