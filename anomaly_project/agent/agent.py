import time
import requests
import psutil
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
SERVER_URL = "http://127.0.0.1:8000/api/ingest/"
HOSTNAME = 'laptop-1'
API_KEY = 'test123'
INTERVAL = 5

prev_sent = None
prev_recv = None
prev_time = None


def bytes_per_sec(curr, prev, dt):
    if prev is None or dt <= 0:
        return 0.0
    return (curr-prev)/dt


while True:
    now = time.time()
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("C:\\").percent
    net = psutil.net_io_counters()
    sent = net.bytes_sent
    recv = net.bytes_recv

    if prev_time is None:
        sent_per_sec = 0.0
        recv_per_sec = 0.0
        dt = 1.0
    else:
        dt = now - prev_time
        sent_per_sec = bytes_per_sec(sent, prev_sent, dt)
        recv_per_sec = bytes_per_sec(recv, prev_recv, dt)

    prev_sent = sent
    prev_recv = recv
    prev_time = now

    # Try to get CPU temperature
    cpu_temp = None
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            # Try common sensor names
            for name in ['coretemp', 'cpu_thermal', 'k10temp', 'acpitz']:
                if name in temps and temps[name]:
                    cpu_temp = temps[name][0].current
                    break
            # Fallback: use first available sensor
            if cpu_temp is None:
                for sensor_list in temps.values():
                    if sensor_list:
                        cpu_temp = sensor_list[0].current
                        break
    except Exception:
        pass

    # CPU frequency
    cpu_freq = None
    try:
        freq = psutil.cpu_freq()
        if freq:
            cpu_freq = round(freq.current, 0)
    except Exception:
        pass

    payload = {
        "hostname": HOSTNAME,
        "timestamp": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
        "cpu": cpu,
        "ram": ram,
        "disk": disk,
        "net_sent": sent_per_sec,
        "net_recv": recv_per_sec,
        "ping_ms": None,
        "cpu_temp": cpu_temp,
        "cpu_freq": cpu_freq,
    }
    print(type(payload))
    print(payload)
    try:
        r = requests.post(
            SERVER_URL,
            json=payload,
            headers={"X-API-KEY": API_KEY},
            timeout=3
        )
        print("Sent:", r.status_code, r.text)
    except Exception as e:
        print("Error occured!:", e)
    time.sleep(INTERVAL)
