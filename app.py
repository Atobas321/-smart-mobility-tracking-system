import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import time

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SMTAS · Smart Mobility Tracking",
    page_icon="🛰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Global */
  [data-testid="stAppViewContainer"] { background: #0d1117; }
  [data-testid="stSidebar"] { background: #161b27; border-right: 1px solid #21293d; }
  [data-testid="stHeader"] { background: transparent; }
  h1, h2, h3 { color: #e8ecf8 !important; }
  .block-container { padding-top: 1rem; padding-bottom: 1rem; }

  /* Metric cards */
  [data-testid="metric-container"] {
    background: #161b27;
    border: 1px solid #21293d;
    border-radius: 10px;
    padding: 14px 18px;
  }
  [data-testid="stMetricLabel"] { color: #8895bc !important; font-size: 12px !important; text-transform: uppercase; letter-spacing: 1px; }
  [data-testid="stMetricValue"] { color: #e8ecf8 !important; font-family: 'JetBrains Mono', monospace; }
  [data-testid="stMetricDelta"] svg { display: none; }

  /* Alert boxes */
  .alert-critical {
    background: rgba(255,77,106,0.07);
    border: 1px solid rgba(255,77,106,0.25);
    border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;
  }
  .alert-warning {
    background: rgba(245,166,35,0.07);
    border: 1px solid rgba(245,166,35,0.25);
    border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;
  }
  .alert-info {
    background: rgba(77,143,255,0.07);
    border: 1px solid rgba(77,143,255,0.25);
    border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;
  }
  .alert-title { font-weight: 600; font-size: 13px; color: #e8ecf8; }
  .alert-meta  { font-size: 11px; color: #8895bc; margin-top: 2px; }

  /* Status pills */
  .pill-moving  { background:#0d7a5522;color:#22e5a0;border:1px solid #22e5a044;padding:2px 9px;border-radius:12px;font-size:11px;font-weight:600; }
  .pill-idle    { background:#7a5c0d22;color:#f5a623;border:1px solid #f5a62344;padding:2px 9px;border-radius:12px;font-size:11px;font-weight:600; }
  .pill-alert   { background:#7a0d1d22;color:#ff4d6a;border:1px solid #ff4d6a44;padding:2px 9px;border-radius:12px;font-size:11px;font-weight:600; }

  /* Top banner */
  .top-banner {
    background: linear-gradient(90deg, #0d1117 0%, #161b27 50%, #0d1117 100%);
    border: 1px solid #21293d; border-radius: 12px;
    padding: 14px 22px; margin-bottom: 18px;
    display: flex; align-items: center; justify-content: space-between;
  }
  .banner-title { font-size: 20px; font-weight: 700; color: #e8ecf8; letter-spacing: .5px; }
  .banner-title span { color: #22e5a0; }
  .live-badge {
    background: rgba(34,229,160,.1); border: 1px solid rgba(34,229,160,.25);
    color: #22e5a0; font-size: 11px; font-weight: 600;
    padding: 4px 12px; border-radius: 20px; letter-spacing: 1px;
  }

  /* Section headers */
  .section-header {
    font-size: 11px; font-weight: 600; letter-spacing: 1.5px;
    text-transform: uppercase; color: #4a5578; margin-bottom: 10px;
    border-bottom: 1px solid #21293d; padding-bottom: 6px;
  }
  div[data-testid="stMarkdownContainer"] p { color: #8895bc; }
</style>
""", unsafe_allow_html=True)


# ─── Fake GPS Data ────────────────────────────────────────────────────────────
CITIES = {
    "Lagos":   (6.5244,  3.3792),
    "Abuja":   (9.0579,  7.4951),
    "Kano":    (12.0022, 8.5920),
    "Enugu":   (6.4584,  7.5464),
    "Ibadan":  (7.3775,  3.9470),
    "Kaduna":  (10.5200, 7.4400),
    "Port Harcourt": (4.8156, 7.0498),
}

@st.cache_data(ttl=5)
def get_fleet_data():
    random.seed(int(time.time() / 5))
    rows = []
    ids_cfg = [
        ("LAG-0017","car",   "Lagos",         "alert"),
        ("ABJ-0042","car",   "Abuja",         "alert"),
        ("ABJ-0031","car",   "Abuja",         "moving"),
        ("KAN-0091","moto",  "Kano",          "moving"),
        ("KAN-0055","moto",  "Kano",          "idle"),
        ("LAG-0082","trike", "Lagos",         "moving"),
        ("ENU-0014","car",   "Enugu",         "moving"),
        ("IBD-0003","trike", "Ibadan",        "moving"),
        ("PHC-0022","car",   "Port Harcourt", "moving"),
        ("KAD-0007","moto",  "Kaduna",        "idle"),
        ("LAG-0055","car",   "Lagos",         "moving"),
        ("ABJ-0019","car",   "Abuja",         "moving"),
    ]
    for vid, vtype, city, status in ids_cfg:
        base_lat, base_lon = CITIES[city]
        jitter = 0.15 if status == "moving" else 0.03
        lat = base_lat + random.uniform(-jitter, jitter)
        lon = base_lon + random.uniform(-jitter, jitter)
        speed = 0 if status == "idle" else random.randint(25, 120 if vtype == "moto" else 90)
        heading = random.randint(0, 359)
        rows.append({
            "id": vid, "type": vtype, "city": city, "status": status,
            "lat": round(lat, 5), "lon": round(lon, 5),
            "speed": speed, "heading": heading,
            "fuel": random.randint(20, 100),
            "trips_today": random.randint(1, 12),
            "km_today": random.randint(5, 180),
            "driver": f"Driver {random.randint(100,999)}",
            "last_seen": f"{random.randint(0,12)}m ago",
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=60)
def get_hourly_trips():
    hours = list(range(0, 24))
    np.random.seed(42)
    base = [5,3,2,2,4,8,22,45,62,70,68,72,74,71,69,76,83,79,65,52,38,28,18,10]
    noise = np.random.randint(-4, 5, 24)
    return pd.DataFrame({"hour": [f"{h:02d}:00" for h in hours], "trips": np.array(base)+noise})


@st.cache_data(ttl=30)
def get_route_history(vehicle_id):
    random.seed(hash(vehicle_id) % 10000)
    city = vehicle_id[:3]
    city_map = {"LAG": "Lagos", "ABJ": "Abuja", "KAN": "Kano",
                "ENU": "Enugu", "IBD": "Ibadan", "PHC": "Port Harcourt", "KAD": "Kaduna"}
    cname = city_map.get(city, "Lagos")
    base_lat, base_lon = CITIES[cname]
    points = []
    lat, lon = base_lat + random.uniform(-0.1, 0.1), base_lon + random.uniform(-0.1, 0.1)
    for i in range(20):
        lat += random.uniform(-0.015, 0.015)
        lon += random.uniform(-0.015, 0.015)
        points.append({
            "lat": round(lat, 5), "lon": round(lon, 5),
            "time": (datetime.now() - timedelta(minutes=(20-i)*8)).strftime("%H:%M"),
            "speed": random.randint(0, 90),
            "seq": i,
        })
    return pd.DataFrame(points)


def build_map(df, show_trails=True, filter_type="all", selected_id=None):
    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # Geofence circle around Abuja
    folium.Circle(
        location=CITIES["Abuja"], radius=25000,
        color="#4d8fff", weight=1.5, fill=True, fill_opacity=0.05,
        tooltip="Geofence Zone A — Abuja FCT",
    ).add_to(m)

    # City labels
    for city, (lat, lon) in CITIES.items():
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;color:#8895bc;font-family:monospace;white-space:nowrap;background:rgba(13,17,23,.75);padding:2px 5px;border-radius:3px;border:1px solid #21293d">{city}</div>',
                icon_size=(80, 20), icon_anchor=(40, 10),
            )
        ).add_to(m)

    COLOR_MAP = {"car": "#22e5a0", "moto": "#f5a623", "trike": "#4d8fff"}
    ICON_MAP  = {"car": "🚗", "moto": "🏍", "trike": "🛺"}

    for _, row in df.iterrows():
        if filter_type != "all" and row["type"] != filter_type:
            continue

        color = "#ff4d6a" if row["status"] == "alert" else COLOR_MAP.get(row["type"], "#22e5a0")
        is_sel = row["id"] == selected_id
        radius = 10 if is_sel else 7
        weight = 3 if is_sel else 1.5

        popup_html = f"""
        <div style='background:#161b27;color:#e8ecf8;font-family:monospace;padding:10px;border-radius:6px;min-width:180px;border:1px solid #21293d'>
          <b style='color:{color};font-size:13px'>{ICON_MAP.get(row['type'],'')} {row['id']}</b><br>
          <span style='color:#8895bc;font-size:11px'>─────────────────</span><br>
          <span style='color:#8895bc'>Type:</span> {row['type'].title()}<br>
          <span style='color:#8895bc'>Speed:</span> <b style='color:{"#ff4d6a" if row["speed"]>80 else "#22e5a0"}'>{row['speed']} km/h</b><br>
          <span style='color:#8895bc'>Status:</span> {row['status'].upper()}<br>
          <span style='color:#8895bc'>Driver:</span> {row['driver']}<br>
          <span style='color:#8895bc'>Trips today:</span> {row['trips_today']}<br>
          <span style='color:#8895bc'>Fuel:</span> {row['fuel']}%<br>
          <span style='color:#8895bc'>Coords:</span> {row['lat']}, {row['lon']}
        </div>"""

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            weight=weight,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{row['id']} · {row['speed']} km/h",
        ).add_to(m)

        # Pulsing ring for alerts
        if row["status"] == "alert":
            folium.Circle(
                location=[row["lat"], row["lon"]],
                radius=3000,
                color="#ff4d6a", weight=1, fill=False, opacity=0.4,
                tooltip="⚠ ALERT ZONE",
            ).add_to(m)

    # Trail for selected vehicle
    if selected_id and show_trails:
        trail = get_route_history(selected_id)
        coords = list(zip(trail["lat"], trail["lon"]))
        folium.PolyLine(
            coords, color="#4d8fff", weight=2.5,
            opacity=0.7, dash_array="6 4",
            tooltip=f"Route history — {selected_id}",
        ).add_to(m)
        # Start/end markers
        if len(coords) >= 2:
            folium.CircleMarker(coords[0],  radius=5, color="#4a5578", fill=True, fill_color="#4a5578", tooltip="Start").add_to(m)
            folium.CircleMarker(coords[-1], radius=5, color="#4d8fff", fill=True, fill_color="#4d8fff", tooltip="Latest position").add_to(m)

    return m


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='display:flex;align-items:center;gap:10px;margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid #21293d'>
      <div style='background:#22e5a0;width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px'>🛰</div>
      <div>
        <div style='font-size:15px;font-weight:700;color:#e8ecf8'>SMTAS</div>
        <div style='font-size:10px;color:#4a5578;letter-spacing:.5px'>Smart Mobility Tracking</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("Navigation", ["🗺  Live Map", "📊  Analytics", "🕐  Route History", "🚨  Alerts", "ℹ  About"], label_visibility="collapsed")

    st.markdown("<div class='section-header'>Filters</div>", unsafe_allow_html=True)
    filter_type = st.selectbox("Vehicle Type", ["all", "car", "moto", "trike"], format_func=lambda x: {"all":"All Types","car":"🚗 Cars","moto":"🏍 Motorcycles","trike":"🛺 Tricycles"}[x])
    filter_status = st.multiselect("Status", ["moving", "idle", "alert"], default=["moving","idle","alert"])
    show_trails = st.toggle("Show Route Trails", value=True)

    st.markdown("<div class='section-header' style='margin-top:16px'>Quick Stats</div>", unsafe_allow_html=True)
    df_all = get_fleet_data()
    st.markdown(f"""
    <div style='font-size:12px;line-height:2;color:#8895bc'>
      🟢 Moving: <b style='color:#22e5a0'>{len(df_all[df_all.status=="moving"])}</b><br>
      🟡 Idle: <b style='color:#f5a623'>{len(df_all[df_all.status=="idle"])}</b><br>
      🔴 Alerts: <b style='color:#ff4d6a'>{len(df_all[df_all.status=="alert"])}</b><br>
      🛰 Total tracked: <b style='color:#e8ecf8'>247</b><br>
      📍 Active geofences: <b style='color:#4d8fff'>4</b>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄  Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(f"<div style='font-size:10px;color:#4a5578;text-align:center;margin-top:8px'>Last updated: {datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)


# ─── Main Content ─────────────────────────────────────────────────────────────
df = get_fleet_data()
if filter_status:
    df = df[df["status"].isin(filter_status)]

# Banner
st.markdown(f"""
<div class='top-banner'>
  <div>
    <div class='banner-title'>Smart Mobility Tracking <span>&amp; Analytics</span></div>
    <div style='font-size:11px;color:#4a5578;margin-top:3px'>Nigeria · Real-time GPS Intelligence Platform</div>
  </div>
  <div class='live-badge'>● LIVE</div>
</div>""", unsafe_allow_html=True)

# ── KPI Row
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Tracked",    "247",  "+12 today")
c2.metric("Moving Now",        str(len(df[df.status=="moving"])),  "Fleet active")
c3.metric("Active Alerts",     "3",   "2 critical", delta_color="inverse")
c4.metric("Geofence Breaches", "7",   "Last 24h",   delta_color="inverse")
c5.metric("Avg Speed",         "47 km/h", "+3 km/h")
st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
if "🗺" in page:
    col_map, col_side = st.columns([3, 1])

    with col_side:
        st.markdown("<div class='section-header'>Fleet Status</div>", unsafe_allow_html=True)
        selected_id = None
        for _, row in df.iterrows():
            pill = {"moving":"pill-moving","idle":"pill-idle","alert":"pill-alert"}[row["status"]]
            with st.container():
                if st.button(
                    f"{{'car':'🚗','moto':'🏍','trike':'🛺'}[row['type']]} {row['id']}  ·  {row['city']}",
                    key=f"vbtn_{row['id']}", use_container_width=True,
                ):
                    st.session_state["selected_id"] = row["id"]
            st.markdown(f"<div style='font-size:10px;color:#4a5578;margin:-8px 0 6px 4px'>{row['speed']} km/h · {row['trips_today']} trips · {row['last_seen']}</div>", unsafe_allow_html=True)

        selected_id = st.session_state.get("selected_id")

        if selected_id:
            sel = df[df["id"] == selected_id]
            if not sel.empty:
                row = sel.iloc[0]
                st.markdown("<div class='section-header' style='margin-top:12px'>Vehicle Detail</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style='background:#161b27;border:1px solid #21293d;border-radius:8px;padding:12px;font-size:12px'>
                  <div style='font-size:14px;font-weight:700;color:#e8ecf8;margin-bottom:8px'>
                    {{'car':'🚗','moto':'🏍','trike':'🛺'}[row['type']]} {row['id']}
                  </div>
                  <div style='color:#8895bc;line-height:2'>
                    City: <b style='color:#e8ecf8'>{row['city']}</b><br>
                    Speed: <b style='color:{"#ff4d6a" if row["speed"]>80 else "#22e5a0"}'>{row['speed']} km/h</b><br>
                    Fuel: <b style='color:#f5a623'>{row['fuel']}%</b><br>
                    Trips today: <b style='color:#e8ecf8'>{row['trips_today']}</b><br>
                    Km today: <b style='color:#e8ecf8'>{row['km_today']}</b><br>
                    Driver: <b style='color:#e8ecf8'>{row['driver']}</b>
                  </div>
                </div>""", unsafe_allow_html=True)

    with col_map:
        st.markdown("<div class='section-header'>Live GPS Map — Nigeria</div>", unsafe_allow_html=True)
        m = build_map(df, show_trails=show_trails, filter_type=filter_type,
                      selected_id=st.session_state.get("selected_id"))
        st_folium(m, width="100%", height=540, returned_objects=[])


# ─────────────────────────────────────────────────────────────────────────────
elif "📊" in page:
    st.markdown("<div class='section-header'>Analytics Dashboard</div>", unsafe_allow_html=True)
    hourly = get_hourly_trips()

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        fig = px.bar(hourly, x="hour", y="trips",
                     title="Hourly Trip Volume",
                     color_discrete_sequence=["#22e5a0"])
        fig.update_layout(
            paper_bgcolor="#161b27", plot_bgcolor="#0d1117",
            font_color="#8895bc", title_font_color="#e8ecf8",
            xaxis=dict(showgrid=False, tickfont=dict(size=9)),
            yaxis=dict(gridcolor="#21293d", tickfont=dict(size=9)),
            margin=dict(l=10,r=10,t=40,b=10), height=260,
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with r1c2:
        type_counts = df.groupby("type").size().reset_index(name="count")
        type_counts["label"] = type_counts["type"].map({"car":"Cars","moto":"Motorcycles","trike":"Tricycles"})
        fig2 = px.pie(type_counts, values="count", names="label",
                      title="Vehicle Type Distribution",
                      color_discrete_sequence=["#22e5a0","#f5a623","#4d8fff"])
        fig2.update_layout(
            paper_bgcolor="#161b27", plot_bgcolor="#0d1117",
            font_color="#8895bc", title_font_color="#e8ecf8",
            margin=dict(l=10,r=10,t=40,b=10), height=260,
            legend=dict(font=dict(color="#8895bc")),
        )
        fig2.update_traces(hole=0.55, textfont_color="#0d1117")
        st.plotly_chart(fig2, use_container_width=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        # Speed distribution
        speeds = [random.randint(0, 130) for _ in range(300)]
        fig3 = px.histogram(x=speeds, nbins=20, title="Speed Distribution (km/h)",
                            color_discrete_sequence=["#4d8fff"])
        fig3.update_layout(
            paper_bgcolor="#161b27", plot_bgcolor="#0d1117",
            font_color="#8895bc", title_font_color="#e8ecf8",
            xaxis=dict(title="Speed km/h", showgrid=False),
            yaxis=dict(title="Vehicles", gridcolor="#21293d"),
            margin=dict(l=10,r=10,t=40,b=10), height=240, showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with r2c2:
        # City coverage
        city_df = df.groupby("city").size().reset_index(name="units")
        fig4 = px.bar(city_df.sort_values("units", ascending=True),
                      x="units", y="city", orientation="h",
                      title="Units per City",
                      color_discrete_sequence=["#a78bfa"])
        fig4.update_layout(
            paper_bgcolor="#161b27", plot_bgcolor="#0d1117",
            font_color="#8895bc", title_font_color="#e8ecf8",
            xaxis=dict(gridcolor="#21293d"),
            yaxis=dict(showgrid=False),
            margin=dict(l=10,r=10,t=40,b=10), height=240,
        )
        st.plotly_chart(fig4, use_container_width=True)

    # KPI table
    st.markdown("<div class='section-header'>Fleet Performance Summary</div>", unsafe_allow_html=True)
    summary = df.groupby("city").agg(
        vehicles=("id","count"),
        avg_speed=("speed","mean"),
        total_trips=("trips_today","sum"),
        total_km=("km_today","sum"),
        alerts=("status", lambda x: (x=="alert").sum()),
    ).round(1).reset_index()
    summary.columns = ["City","Vehicles","Avg Speed (km/h)","Total Trips","Total KM","Alerts"]
    st.dataframe(summary, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
elif "🕐" in page:
    st.markdown("<div class='section-header'>Route History Replay</div>", unsafe_allow_html=True)

    sel_vehicle = st.selectbox("Select Vehicle", df["id"].tolist(),
                               format_func=lambda x: f"{x} · {df[df.id==x].iloc[0]['city']} · {df[df.id==x].iloc[0]['type'].title()}")

    trail = get_route_history(sel_vehicle)
    c1, c2 = st.columns([2, 1])
    with c1:
        m2 = folium.Map(location=[trail["lat"].mean(), trail["lon"].mean()],
                        zoom_start=13, tiles="CartoDB dark_matter")
        coords = list(zip(trail["lat"], trail["lon"]))
        folium.PolyLine(coords, color="#4d8fff", weight=3, opacity=0.8).add_to(m2)
        for i, (_, pt) in enumerate(trail.iterrows()):
            color = "#22e5a0" if i == len(trail)-1 else ("#ff4d6a" if i == 0 else "#4d8fff")
            folium.CircleMarker(
                [pt["lat"], pt["lon"]], radius=5 if i in [0, len(trail)-1] else 3,
                color=color, fill=True, fill_color=color, fill_opacity=.9,
                tooltip=f"{pt['time']} · {pt['speed']} km/h",
            ).add_to(m2)
        st_folium(m2, width="100%", height=420, returned_objects=[])

    with c2:
        st.markdown("<div class='section-header'>Waypoints</div>", unsafe_allow_html=True)
        for _, pt in trail.iterrows():
            speed_color = "#ff4d6a" if pt["speed"] > 80 else "#22e5a0" if pt["speed"] > 20 else "#f5a623"
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #21293d;font-size:11px'>
              <span style='color:#4a5578'>{pt['time']}</span>
              <span style='color:{speed_color};font-family:monospace'>{pt['speed']} km/h</span>
            </div>""", unsafe_allow_html=True)

        # Speed over time chart
        fig = px.line(trail, x="time", y="speed", title="Speed Profile",
                      color_discrete_sequence=["#22e5a0"])
        fig.update_layout(
            paper_bgcolor="#161b27", plot_bgcolor="#0d1117",
            font_color="#8895bc", title_font_color="#e8ecf8",
            xaxis=dict(showgrid=False, tickfont=dict(size=8)),
            yaxis=dict(gridcolor="#21293d", tickfont=dict(size=8)),
            margin=dict(l=10,r=10,t=36,b=10), height=200,
        )
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
elif "🚨" in page:
    st.markdown("<div class='section-header'>Active Alerts &amp; Incidents</div>", unsafe_allow_html=True)

    alerts = [
        {"type":"critical","icon":"🔴","title":"Geofence Breach — ABJ-0042",
         "meta":"Unauthorized zone exit · Maitama, Abuja · 9.0821°N 7.5012°E","time":"2 min ago",
         "detail":"Vehicle exited Geofence Zone A perimeter. Driver not responding to ping. Response unit dispatched."},
        {"type":"critical","icon":"🔴","title":"SOS Triggered — LAG-0017",
         "meta":"Emergency button pressed · Lekki Expressway, Lagos","time":"7 min ago",
         "detail":"Driver distress signal active. Last known speed: 0 km/h. Lagos Zone Response on the way."},
        {"type":"warning","icon":"🟡","title":"Speed Violation — KAN-0091",
         "meta":"118 km/h in 80 km/h zone · Kano Bypass","time":"14 min ago",
         "detail":"3rd speed violation today. Persistent over-speeding. Owner notification sent."},
        {"type":"info","icon":"🔵","title":"Low Fuel Warning — LAG-0082",
         "meta":"Fuel level at 12% · Oshodi, Lagos","time":"21 min ago",
         "detail":"Tricycle fuel approaching critical level. Nearest station: 1.2 km away."},
        {"type":"info","icon":"🔵","title":"Idle Timeout — KAN-0055",
         "meta":"Stationary 45+ minutes · Sabon Gari, Kano","time":"48 min ago",
         "detail":"Vehicle idle beyond normal threshold. No active trip assigned."},
    ]

    for a in alerts:
        with st.expander(f"{a['icon']}  {a['title']}  ·  {a['time']}"):
            st.markdown(f"""
            <div style='font-size:12px;color:#8895bc;margin-bottom:6px'>{a['meta']}</div>
            <div style='font-size:13px;color:#e8ecf8'>{a['detail']}</div>
            """, unsafe_allow_html=True)
            ca, cb, cc = st.columns(3)
            ca.button("✅ Resolve",      key=f"resolve_{a['title']}")
            cb.button("📞 Contact Driver", key=f"contact_{a['title']}")
            cc.button("🗺 View on Map",   key=f"map_{a['title']}")

    st.markdown("<br><div class='section-header'>Incident Log — Today</div>", unsafe_allow_html=True)
    log_data = {
        "Time":    ["08:12","09:45","11:03","13:28","15:50","16:44","18:02"],
        "Vehicle": ["LAG-0017","ABJ-0042","KAN-0091","IBD-0003","LAG-0082","PHC-0022","ABJ-0031"],
        "Type":    ["SOS","Geofence","Speeding","Idle","Low Fuel","Geofence","Speeding"],
        "Location":["Lekki","Maitama","Kano Bypass","Ring Rd","Oshodi","GRA","Airport Rd"],
        "Status":  ["Active","Active","Resolved","Resolved","Pending","Resolved","Resolved"],
    }
    log_df = pd.DataFrame(log_data)
    st.dataframe(log_df, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
elif "ℹ" in page:
    st.markdown("""
    ## Smart Mobility Tracking & Analytics System (SMTAS)

    SMTAS is a unified platform that tracks and analyzes the movement of **vehicles** (cars, motorcycles, tricycles)
    and **individuals** via GPS devices and mobile phones.

    ### Key Features
    - 🛰 **Real-time GPS tracking** across Nigeria
    - 🗺 **Interactive map** with geofencing zones
    - 📊 **Analytics dashboard** — trips, speed, coverage
    - 🚨 **Instant alerts** — SOS, geofence breach, speeding
    - 🕐 **Route history replay** per vehicle
    - 📱 Mobile-ready interface

    ### Target Users
    | Segment | Use Case |
    |---|---|
    | Individuals | Personal vehicle security & stolen asset tracking |
    | Transport Operators | Fleet management & driver accountability |
    | Businesses | Logistics optimization & delivery tracking |
    | Security Agencies | Emergency response & location intelligence |

    ### Tech Stack
    - **Backend:** Python · Streamlit
    - **Mapping:** Folium · OpenStreetMap
    - **Charts:** Plotly
    - **GPS Simulation:** Randomized real-coordinate data
    - **Deployment:** Streamlit Cloud

    ---
    *Built for the Nigerian market. Project in active development.*
    """)
    st.markdown("""
    <div style='background:#161b27;border:1px solid #21293d;border-radius:8px;padding:16px;margin-top:8px;font-size:12px;color:#8895bc'>
      📌 <b style='color:#e8ecf8'>GitHub:</b> https://github.com/your-username/smart-mobility-tracking-system<br>
      🌐 <b style='color:#e8ecf8'>Live Demo:</b> https://your-username-smtas.streamlit.app
    </div>
    """, unsafe_allow_html=True)
