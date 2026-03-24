# 🛰 SMTAS — Smart Mobility Tracking & Analytics System

> **Live demo:** https://your-username-smtas.streamlit.app  
> "Live demo available via Streamlit Cloud showcasing real-time tracking simulation and analytics dashboard."

---

## Overview

SMTAS is a unified platform that tracks and analyzes the movement of vehicles (cars, motorcycles, tricycles) and individuals via GPS devices and mobile phones across Nigeria.

It provides:
- 🗺 **Real-time location monitoring** on an interactive Nigeria map
- 📈 **Route history** & movement replay per vehicle
- 🚨 **Safety alerts** — SOS triggers, geofence breaches, speed violations
- 📊 **Behavior insights** — speed distribution, trip analytics, coverage stats
- 🏙 **City coverage** — Lagos, Abuja, Kano, Enugu, Ibadan, Kaduna, Port Harcourt

---

## Features

| Feature | Description |
|---|---|
| Live Map | GPS dots on Nigeria map, color-coded by vehicle type & status |
| Geofencing | Zone perimeters with breach detection & alerts |
| Fleet Sidebar | Per-vehicle status, speed, trips, fuel |
| Analytics | Hourly trips, type breakdown, speed histogram, city coverage |
| Route History | Waypoint trail with speed profile chart |
| Alert Panel | Critical/warning/info incidents with resolve actions |
| Auto-refresh | Data refreshes every 5 seconds (simulated GPS movement) |

---

## Tech Stack

- **Python 3.11+**
- **Streamlit** — web framework
- **Folium + streamlit-folium** — interactive maps
- **Plotly** — charts and analytics
- **Pandas / NumPy** — data processing

---

## Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-username/smart-mobility-tracking-system
cd smart-mobility-tracking-system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

---

## Deploy to Streamlit Cloud (Free, 5 minutes)

1. Push this repo to GitHub (public)
2. Go to https://share.streamlit.io
3. Click **"New app"**
4. Select your repo → branch `main` → file `app.py`
5. Click **Deploy** ✅

Your live URL will be:  
`https://your-username-smtas.streamlit.app`

---

## Project Status

> 🚧 **In active development** — core demo complete, production GPS integration in progress.

### Roadmap
- [ ] Real GPS device integration (MQTT / REST API)
- [ ] Mobile app companion (React Native)
- [ ] SMS/WhatsApp alert notifications
- [ ] User authentication & multi-tenant fleet management
- [ ] Machine learning for driver behaviour scoring
- [ ] Integration with Nigerian security agencies API

---

## Use Cases

- **Individuals** — Personal vehicle security, stolen asset tracking
- **Transport Operators** — Fleet management, driver accountability
- **Businesses** — Logistics optimization, delivery tracking
- **Security Agencies** — Emergency response, location intelligence

---

*Built for Nigeria 🇳🇬 · SMTAS © 2025*
