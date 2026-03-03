"""
Website Monitor Checker — run alongside agent.py.

Usage:
    cd anomaly_project
    ..\venv\Scripts\python.exe -m monitoring.website_checker

Or to run standalone:
    set DJANGO_SETTINGS_MODULE=anomaly_project.settings
    python monitoring/website_checker.py
"""
import os
import sys
import time
import ssl
import socket
import requests
from datetime import datetime

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anomaly_project.settings')

# Add parent directory to path so Django can find the project
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

if __name__ == '__main__':
    django.setup()

from django.utils import timezone
from monitoring.models import WebsiteMonitor, WebsiteCheck, AnomalyEvent
from monitoring import detection


def check_ssl(hostname, port=443, timeout=5):
    """Check if SSL certificate is valid and return days until expiry."""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                # Parse expiration date
                cert_expires = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_left = (cert_expires - datetime.now()).days
                return True, days_left
    except Exception:
        return False, None


def check_website(monitor):
    """Perform a single check on a website."""
    start = time.time()
    status_code = None
    is_up = False
    ssl_valid = True
    ssl_expiry_days = None
    error = ''
    response_time_ms = None

    # Auto-prefix URL if missing protocol
    url = monitor.url
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AILEXUS-Monitor/1.0'}
        r = requests.get(url, timeout=10, allow_redirects=True, headers=headers)
        response_time_ms = round((time.time() - start) * 1000, 1)
        status_code = r.status_code
        # Site is UP if we got any HTTP response (server is reachable)
        is_up = (status_code < 500) or (status_code == 503)  # 503 = bot protection, still "up"

        # Content Matching / Defacement Check
        if is_up and monitor.expected_keyword:
            if monitor.expected_keyword.lower() not in r.text.lower():
                is_up = False
                error = f'Missing expected keyword: "{monitor.expected_keyword}"'

        # Check SSL if HTTPS
        if url.startswith('https://'):
            from urllib.parse import urlparse
            hostname = urlparse(url).hostname
            ssl_valid, ssl_expiry_days = check_ssl(hostname)

    except requests.exceptions.Timeout:
        error = 'Connection timed out (>10s)'
        response_time_ms = round((time.time() - start) * 1000, 1)
    except requests.exceptions.ConnectionError as e:
        error = f'Connection failed: {str(e)[:200]}'
        response_time_ms = round((time.time() - start) * 1000, 1)
    except Exception as e:
        error = f'Error: {str(e)[:200]}'
        response_time_ms = round((time.time() - start) * 1000, 1)

    pass

    return WebsiteCheck.objects.create(
        monitor=monitor,
        timestamp=timezone.now(),
        status_code=status_code,
        response_time_ms=response_time_ms,
        is_up=is_up,
        ssl_valid=ssl_valid,
        ssl_expiry_days=ssl_expiry_days,
        error=error,
    )


def run():
    print("=" * 42)
    print("   AILEXUS Website Monitor - Running")
    print("=" * 42)

    while True:
        monitors = WebsiteMonitor.objects.filter(is_active=True)
        if not monitors.exists():
            print("[*] No websites to monitor. Add them via Django admin.")
            time.sleep(10)
            continue

        for m in monitors:
            result = check_website(m)
            status = "[UP]" if result.is_up else "[DOWN]"
            rt = f"{result.response_time_ms}ms" if result.response_time_ms else "N/A"
            print(f"  {status} {m.name} ({m.url}) - {rt} - code:{result.status_code or 'N/A'}")

        # Wait for the shortest interval
        min_interval = min(m.check_interval for m in monitors)
        time.sleep(max(min_interval, 10))


if __name__ == '__main__':
    run()
