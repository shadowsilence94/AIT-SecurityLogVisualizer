import streamlit as st
import pandas as pd
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

LOG_FILE = "access.log"

st.set_page_config(page_title="Security Log Visualizer", layout="wide")

@st.cache_resource
def get_shared_state():
    return {
        "logs": [],
        "last_position": 0,
        "observer": None
    }

state = get_shared_state()

def read_new_logs():
    if not os.path.exists(LOG_FILE):
        return
    with open(LOG_FILE, "r") as f:
        f.seek(state["last_position"])
        lines = f.readlines()
        state["last_position"] = f.tell()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(" - ")
            if len(parts) >= 3:
                timestamp_str = parts[0]
                ip = parts[1]
                status = parts[2]
                
                try:
                    dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    hour = dt.hour
                    off_hours = hour < 9 or hour >= 18
                except Exception:
                    off_hours = False

                state["logs"].append({
                    "Timestamp": timestamp_str,
                    "IP Address": ip,
                    "Status": status,
                    "Off_Hours": off_hours
                })

class LogFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(LOG_FILE):
            read_new_logs()
    
    def on_created(self, event):
        if event.src_path.endswith(LOG_FILE):
            read_new_logs()

def start_observer():
    if state["observer"] is None:
        handler = LogFileHandler()
        observer = Observer()
        # Watch the current directory
        observer.schedule(handler, path=".", recursive=False)
        observer.start()
        state["observer"] = observer
        # Do an initial read
        read_new_logs()

@st.cache_resource
def start_background_simulator():
    import threading
    import logger_sim
    # Run the simulator's main block in a background daemon thread
    thread = threading.Thread(target=logger_sim.main, daemon=True)
    thread.start()
    return thread

# UI Setup
st.title("🛡️ Real-Time Security Log Visualizer")

# Sidebar for Deployment Controls
st.sidebar.header("Control Panel")
st.sidebar.write("If running on Streamlit Cloud, you need to start the simulator to generate mock logs.")
if st.sidebar.button("🚀 Start Log Simulator"):
    start_background_simulator()
    st.sidebar.success("Simulator started in the background!")

# Start background file observer
start_observer()

# Read logs immediately in case observer missed an event before starting
read_new_logs()

if not state["logs"]:
    st.info("No logs detected yet. Please ensure 'logger_sim.py' is running and 'access.log' is being populated.")
else:
    df = pd.DataFrame(state["logs"])
    
    # 1. Total Attacks Detected (Failed Logins)
    failed_logs = df[df["Status"] == "Failed Login"]
    total_attacks = len(failed_logs)
    
    # 2. Brute Force Detection (IP > 5 Failed logins)
    failed_counts = failed_logs["IP Address"].value_counts()
    brute_force_ips = failed_counts[failed_counts > 5].index.tolist()
    
    # 3. Off-Hours Detection
    off_hours_logs = df[df["Off_Hours"] == True]
    
    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Attacks (Failed Logins)", total_attacks)
    m2.metric("Brute Force IPs Detected", len(brute_force_ips))
    m3.metric("Off-Hours Logins", len(off_hours_logs))
    
    # Alerts
    if brute_force_ips:
        for ip in brute_force_ips:
            st.error(f"🚨 **Brute Force Alert:** IP address **{ip}** has more than 5 failed login attempts!")
            
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Chart: Login Status
        st.subheader("Login Status Distribution")
        status_counts = df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        st.bar_chart(data=status_counts, x="Status", y="Count", use_container_width=True)
    
    with col2:
        # Enhance DataFrame for display
        display_df = df.copy()
        display_df["Threat Level"] = "Normal"
        display_df.loc[display_df["Status"] == "Failed Login", "Threat Level"] = "Elevated (Failed Login)"
        display_df.loc[display_df["IP Address"].isin(brute_force_ips), "Threat Level"] = "Critical (Brute Force)"
        display_df.loc[display_df["Off_Hours"] == True, "Threat Level"] = display_df["Threat Level"] + " & Off-Hours"
        
        # Table
        st.subheader("Live Access Logs")
        # Sort descending by dropping index, just reversing
        st.dataframe(display_df.iloc[::-1], use_container_width=True, height=400)

# Auto-refresh interval (reruns the app every 2 seconds to pick up new logs)
time.sleep(2)
st.rerun()
