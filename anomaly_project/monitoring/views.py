# All my modules
import traceback
import json
import secrets
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from datetime import timedelta
# Tables and function
from .models import Host, MetricSample, AnomalyEvent, WebsiteMonitor, WebsiteCheck
from .detection import run_detection


def safe_float(x, default=0.0):
    if x is None:
        return default
    return float(x)


@csrf_exempt
def ingest(request):
    try:
        if request.method != 'POST':
            return JsonResponse({"error": "POST only"}, status=405)

        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            return JsonResponse({"error": "Mising X-API-KEY"}, status=401)

        try:
            raw = request.body.decode("utf-8")
            data = json.loads(raw)
        except Exception as e:
            return JsonResponse({"error": "Invalid json", "exception": str(e), "raw": raw[:300]}, status=400)

        hostname = data.get("hostname")
        if not hostname:
            return JsonResponse({"error": "Missing hostname"}, status=400)
        try:
            host = Host.objects.get(hostname=hostname)
        except Host.DoesNotExist:
            return JsonResponse({"error": "Unknown host"}, status=403)

        if api_key != host.api_key:
            return JsonResponse({"error": "Bad API key"}, status=403)

        ts = parse_datetime(data.get("timestamp", ""))
        if ts is None:
            ts = timezone.now()

        top_procs = data.get("top_processes")
        if isinstance(top_procs, list):
            top_procs = json.dumps(top_procs)
            
        sample = MetricSample.objects.create(
            host=host,
            timestamp=ts,
            cpu=safe_float(data.get("cpu", 0)),
            ram=safe_float(data.get("ram", 0)),
            disk=safe_float(data.get("disk", 0)),
            net_sent=safe_float(data.get("net_sent", 0)),
            net_recv=safe_float(data.get("net_recv", 0)),
            ping_ms=safe_float(data.get("ping_ms", 0)),
            cpu_temp=data.get("cpu_temp"),
            cpu_freq=data.get("cpu_freq"),
            top_processes=top_procs,
            disk_read_kb=safe_float(data.get("disk_read_kb", 0)),
            disk_write_kb=safe_float(data.get("disk_write_kb", 0)),
        )

        host.last_seen = timezone.now()
        host.save(update_fields=["last_seen"])

        run_detection(host, sample)
        return JsonResponse({"status": "stored"})
    except Exception as e:
        print("Ingest crash:", repr(e))
        traceback.print_exc()
        return JsonResponse({"error": "server_crash", "exception": str(e)}, status=500)


# ─── Authentication ──────────────────────────────────────────────────

def user_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    error = None
    if request.method == 'POST':
        u = request.POST.get('username')
        p1 = request.POST.get('password')
        p2 = request.POST.get('confirm_password')
        
        if User.objects.filter(username=u).exists():
            error = "Username already taken."
        elif p1 != p2:
            error = "Passwords do not match."
        elif not u or not p1:
            error = "All fields required."
        else:
            user = User.objects.create_user(username=u, password=p1)
            login(request, user)
            return redirect('dashboard')
            
    return render(request, 'monitoring/register.html', {'error': error})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    error = None
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            error = "Invalid credentials."
            
    return render(request, 'monitoring/login.html', {'error': error})

def user_logout(request):
    logout(request)
    return redirect('login')


# ─── Dashboard (single page) ───────────────────────────────────────────

@login_required(login_url='login')
def dashboard(request):
    return render(request, 'monitoring/dashboard.html')


# ─── JSON API endpoints for AJAX polling ────────────────────────────────

def api_hosts(request):
    if not request.user.is_authenticated: return JsonResponse({'hosts': []})
    host_list = Host.objects.filter(user=request.user).order_by("hostname")
    rows = []
    for h in host_list:
        latest = MetricSample.objects.filter(host=h).order_by("-timestamp").first()
        recent_crit = AnomalyEvent.objects.filter(
            host=h, is_resolved=False, severity=3).exists()
        recent_warn = AnomalyEvent.objects.filter(
            host=h, is_resolved=False, severity__in=[1, 2]).exists()
        if recent_crit:
            status = 'CRIT'
        elif recent_warn:
            status = 'WARN'
        else:
            status = 'OK'
        rows.append({
            'id': h.id,
            'hostname': h.hostname,
            'last_seen': h.last_seen.isoformat() if h.last_seen else None,
            'status': status,
            'cpu': round(latest.cpu, 1) if latest else None,
            'ram': round(latest.ram, 1) if latest else None,
            'disk': round(latest.disk, 1) if latest else None,
        })
    return JsonResponse({'hosts': rows})


def api_host_detail(request, host_id):
    if not request.user.is_authenticated: return JsonResponse({'error': 'unauthorized'}, status=401)
    host = get_object_or_404(Host, id=host_id, user=request.user)
    samples = MetricSample.objects.filter(host=host).order_by('-timestamp')[:60]
    events = AnomalyEvent.objects.filter(host=host, is_resolved=False).order_by('-timestamp')[:30]

    sample_data = [{
        'timestamp': s.timestamp.isoformat(),
        'cpu': round(s.cpu, 1),
        'ram': round(s.ram, 1),
        'disk': round(s.disk, 1),
        'net_sent': round(s.net_sent, 1),
        'net_recv': round(s.net_recv, 1),
        'ping_ms': round(s.ping_ms, 1) if s.ping_ms else 0,
        'cpu_temp': round(s.cpu_temp, 1) if s.cpu_temp else None,
        'cpu_freq': round(s.cpu_freq, 0) if s.cpu_freq else None,
        'top_processes': json.loads(s.top_processes) if s.top_processes else [],
        'disk_read_kb': round(s.disk_read_kb, 1) if s.disk_read_kb else 0.0,
        'disk_write_kb': round(s.disk_write_kb, 1) if s.disk_write_kb else 0.0,
    } for s in samples]

    event_data = [{
        'timestamp': e.timestamp.isoformat(),
        'metric_name': e.metric_name,
        'value': round(e.value, 1),
        'severity': e.severity,
        'reason': e.reason,
    } for e in events]

    return JsonResponse({
        'host': {
            'id': host.id,
            'hostname': host.hostname,
            'last_seen': host.last_seen.isoformat() if host.last_seen else None,
        },
        'samples': sample_data,
        'events': event_data,
    })


def api_anomalies(request):
    if not request.user.is_authenticated: return JsonResponse({'events': []})
    events = AnomalyEvent.objects.filter(host__user=request.user).order_by('-timestamp')[:100]
    event_data = [{
        'host': e.host.hostname,
        'timestamp': e.timestamp.isoformat(),
        'metric_name': e.metric_name,
        'value': round(e.value, 1),
        'severity': e.severity,
        'reason': e.reason,
        'is_resolved': e.is_resolved,
    } for e in events]
    return JsonResponse({'events': event_data})


# ─── Advice Engine ──────────────────────────────────────────────────────

ADVICE_DB = {
    'cpu': {
        'what': 'CPU usage spiked to {value}%, far above the normal baseline',
        'why': 'Sustained high CPU usage causes system slowdowns, application freezes, and potential service crashes. It may indicate a runaway process, malware, or insufficient processing power.',
        'actions': [
            'Open Task Manager (Ctrl+Shift+Esc) and sort by CPU — identify the top process',
            'Close unnecessary browser tabs and background applications',
            'Check for Windows Update running in the background',
            'Scan for malware using Windows Defender or your antivirus',
            'If recurring, consider upgrading CPU or optimizing workload distribution',
        ],
        'urgency_high': 'Act immediately — system may become unresponsive',
        'urgency_med': 'Investigate within 10 minutes',
        'urgency_low': 'Monitor — may resolve on its own',
    },
    'ram': {
        'what': 'RAM usage reached {value}%, indicating heavy memory consumption',
        'why': 'High RAM usage forces the system to use disk swap space, dramatically slowing performance. Applications may crash with "out of memory" errors.',
        'actions': [
            'Check Task Manager → Memory tab — find which apps consume the most RAM',
            'Close unused applications, especially Chrome tabs (each tab uses 100-300 MB)',
            'Restart the system to clear memory leaks',
            'Disable startup programs you don\'t need (Task Manager → Startup tab)',
            'If frequent, consider adding more physical RAM to the system',
        ],
        'urgency_high': 'Critical — system may start crashing applications',
        'urgency_med': 'Close some programs within the next few minutes',
        'urgency_low': 'Normal fluctuation — monitor for trends',
    },
    'disk': {
        'what': 'Disk usage reached {value}%, which deviates from its normal pattern',
        'why': 'Abnormal disk activity can indicate heavy file operations, failing disk, or malware writing excessive data. High disk utilization can cause I/O bottlenecks.',
        'actions': [
            'Check disk space — run Disk Cleanup (cleanmgr) if space is low',
            'Look for large temporary files or recent downloads',
            'Check if Windows Update or antivirus is performing a full scan',
            'Monitor disk health using CrystalDiskInfo for SMART data',
            'If persistent, check for disk fragmentation or consider SSD upgrade',
        ],
        'urgency_high': 'Investigate immediately — possible disk failure',
        'urgency_med': 'Check disk health within the hour',
        'urgency_low': 'Likely a routine operation — monitor over time',
    },
    'net_sent': {
        'what': 'Network upload surged to {value_kb} KB/s, well above normal levels',
        'why': 'Unusual upload spikes could indicate data exfiltration (malware sending your data), a large file sync (OneDrive/Dropbox), or P2P software running in the background.',
        'actions': [
            'Open Resource Monitor (resmon) → Network tab — see which process is uploading',
            'Check if cloud sync services (OneDrive, Google Drive) are backing up',
            'Verify no unauthorized software is sending data externally',
            'Temporarily disable sharing or P2P programs and check if usage drops',
            'If suspicious, disconnect from network and run a full security scan',
        ],
        'urgency_high': 'Investigate immediately — potential data breach',
        'urgency_med': 'Check which process is uploading within 5 minutes',
        'urgency_low': 'Likely a cloud sync — verify and monitor',
    },
    'net_recv': {
        'what': 'Network download surged to {value_kb} KB/s, unusually high traffic',
        'why': 'Large download spikes may be system updates, streaming, or potentially unwanted downloads. They consume bandwidth and may impact network performance for others.',
        'actions': [
            'Check Resource Monitor → Network tab — identify the downloading process',
            'Verify if Windows Update or software updates are downloading',
            'Check browser download manager for large file downloads',
            'Ensure no unauthorized downloads are occurring',
            'If bandwidth is shared, consider implementing QoS rules on your router',
        ],
        'urgency_high': 'Check for unauthorized downloads immediately',
        'urgency_med': 'Identify the source within a few minutes',
        'urgency_low': 'Likely a system update — let it complete',
    },
    'ping_ms': {
        'what': 'Network latency spiked to {value}ms, indicating connectivity issues',
        'why': 'High ping means packets are taking too long to reach the destination, causing lag in online services, video calls, and remote connections.',
        'actions': [
            'Test your connection — try speed test at speedtest.net',
            'Restart your router/modem by unplugging for 30 seconds',
            'Switch from Wi-Fi to a wired Ethernet connection if possible',
            'Check if other devices on your network are consuming bandwidth',
            'Contact your ISP if the issue persists beyond 15 minutes',
        ],
        'urgency_high': 'Network connectivity severely impacted',
        'urgency_med': 'May affect real-time applications — investigate',
        'urgency_low': 'Minor latency increase — likely temporary',
    },
}


def api_advice(request):
    """Generate actionable advice for recent anomalies + website issues."""
    if not request.user.is_authenticated: return JsonResponse({'advice': []})
    events = AnomalyEvent.objects.filter(host__user=request.user, is_resolved=False).order_by('-timestamp')[:50]
    advice_list = []

    for e in events:
        template = ADVICE_DB.get(e.metric_name, {})
        if not template:
            continue

        value_kb = round(e.value / 1024, 1) if e.metric_name in ('net_sent', 'net_recv') else e.value

        if e.severity >= 3:
            urgency = template.get('urgency_high', 'Act immediately')
        elif e.severity >= 2:
            urgency = template.get('urgency_med', 'Investigate soon')
        else:
            urgency = template.get('urgency_low', 'Monitor')

        advice_list.append({
            'source': 'device',
            'host': e.host.hostname,
            'timestamp': e.timestamp.isoformat(),
            'metric': e.metric_name,
            'value': round(e.value, 1),
            'severity': e.severity,
            'what_happened': template['what'].format(value=round(e.value, 1), value_kb=value_kb),
            'why_it_matters': template['why'],
            'recommended_actions': template['actions'],
            'urgency': urgency,
        })

    # Website advice
    monitors = WebsiteMonitor.objects.filter(user=request.user, is_active=True)
    for m in monitors:
        latest = WebsiteCheck.objects.filter(monitor=m).order_by('-timestamp').first()
        if not latest:
            continue

        if not latest.is_up:
            advice_list.insert(0, {
                'source': 'website',
                'host': m.name,
                'timestamp': latest.timestamp.isoformat(),
                'metric': 'website_down',
                'value': latest.status_code or 0,
                'severity': 3,
                'what_happened': f'{m.name} ({m.url}) is currently unreachable',
                'why_it_matters': 'Users cannot access this website. This could mean lost revenue, broken user flows, and damage to your service reputation.',
                'recommended_actions': [
                    'Check if the server hosting the website is running',
                    'Verify DNS records are pointing to the correct IP',
                    'Check if the domain registration has expired',
                    'Look at server logs for crash errors or out-of-memory issues',
                    'Contact your hosting provider if the issue persists',
                ],
                'urgency': 'Immediate — website is down for users',
            })
        elif latest.ssl_expiry_days is not None and latest.ssl_expiry_days < 14:
            advice_list.insert(0, {
                'source': 'website',
                'host': m.name,
                'timestamp': latest.timestamp.isoformat(),
                'metric': 'ssl_expiring',
                'value': latest.ssl_expiry_days,
                'severity': 2,
                'what_happened': f'SSL certificate for {m.name} expires in {latest.ssl_expiry_days} days',
                'why_it_matters': 'An expired SSL certificate will cause browsers to show security warnings, blocking user access and damaging trust.',
                'recommended_actions': [
                    'Renew the certificate through your Certificate Authority (CA) or Let\'s Encrypt',
                    'Ensure auto-renewal is configured correctly to prevent future expirations',
                    'Verify the certificate chain is properly installed on your server',
                ],
                'urgency': 'High — renew immediately to avoid downtime',
            })
        elif latest.response_time_ms and latest.response_time_ms > 3000:
            advice_list.insert(0, {
                'source': 'website',
                'host': m.name,
                'timestamp': latest.timestamp.isoformat(),
                'metric': 'website_slow',
                'value': round(latest.response_time_ms, 0),
                'severity': 2,
                'what_happened': f'{m.name} is responding slowly ({round(latest.response_time_ms)}ms)',
                'why_it_matters': 'Slow response times frustrate users and can hurt SEO rankings. Google recommends pages load within 2.5 seconds.',
                'recommended_actions': [
                    'Check server CPU and memory usage — it may be overloaded',
                    'Review database queries for slow or unoptimized operations',
                    'Enable caching (Redis, CDN) to reduce server load',
                    'Optimize images and static assets for faster delivery',
                    'Consider scaling up server resources or adding a load balancer',
                ],
                'urgency': 'Investigate within 15 minutes',
            })
        if not latest.ssl_valid:
            advice_list.insert(0, {
                'source': 'website',
                'host': m.name,
                'timestamp': latest.timestamp.isoformat(),
                'metric': 'ssl_invalid',
                'value': 0,
                'severity': 3,
                'what_happened': f'SSL certificate for {m.name} is invalid or expired',
                'why_it_matters': 'Browsers will show security warnings to users, blocking access. This destroys user trust and is a critical security issue.',
                'recommended_actions': [
                    'Check certificate expiry date using ssllabs.com',
                    'Renew the certificate through your CA (e.g., Let\'s Encrypt)',
                    'Verify the certificate chain is properly configured',
                    'Ensure auto-renewal is set up to prevent future expiry',
                ],
                'urgency': 'Critical — users see security warnings',
            })

    return JsonResponse({'advice': advice_list})


# ─── Website Monitor API ───────────────────────────────────────────────

def api_websites(request):
    """List all monitored websites with latest status."""
    if not request.user.is_authenticated: return JsonResponse({'websites': []})
    monitors = WebsiteMonitor.objects.filter(user=request.user, is_active=True)
    rows = []
    for m in monitors:
        latest = WebsiteCheck.objects.filter(monitor=m).order_by('-timestamp').first()
        checks_24h = WebsiteCheck.objects.filter(
            monitor=m,
            timestamp__gte=timezone.now() - timedelta(hours=24)
        )
        total = checks_24h.count()
        up_count = checks_24h.filter(is_up=True).count()
        uptime_pct = round((up_count / total * 100), 1) if total > 0 else 100.0

        # Avg response time over last 24h
        recent_checks = list(checks_24h.filter(response_time_ms__isnull=False).values_list('response_time_ms', flat=True))
        avg_rt = round(sum(recent_checks) / len(recent_checks), 1) if recent_checks else 0

        rows.append({
            'id': m.id,
            'name': m.name,
            'url': m.url,
            'is_up': latest.is_up if latest else None,
            'status_code': latest.status_code if latest else None,
            'response_time_ms': round(latest.response_time_ms, 1) if latest and latest.response_time_ms else None,
            'ssl_valid': latest.ssl_valid if latest else True,
            'ssl_expiry_days': latest.ssl_expiry_days if latest else None,
            'last_checked': latest.timestamp.isoformat() if latest else None,
            'uptime_24h': uptime_pct,
            'avg_response_ms': avg_rt,
            'error': latest.error if latest else '',
        })

    return JsonResponse({'websites': rows})


def api_website_detail(request, monitor_id):
    """Get response time history for a specific website."""
    if not request.user.is_authenticated: return JsonResponse({'error': 'unauthorized'}, status=401)
    monitor = get_object_or_404(WebsiteMonitor, id=monitor_id, user=request.user)
    checks = WebsiteCheck.objects.filter(monitor=monitor).order_by('-timestamp')[:100]

    check_data = [{
        'timestamp': c.timestamp.isoformat(),
        'status': c.status_code,
        'time_ms': c.response_time_ms,
        'up': c.is_up,
        'ssl': c.ssl_valid,
        'ssl_days': c.ssl_expiry_days,
        'error': c.error
    } for c in checks]

    return JsonResponse({
        'monitor': {
            'id': monitor.id,
            'name': monitor.name,
            'url': monitor.url,
            'keyword': monitor.expected_keyword,
        },
        'checks': check_data,
    })


# ─── Add Host API ──────────────────────────────────────────────────────

@csrf_exempt
def api_add_host(request):
    """Create a new host and return its API key + agent config."""
    if not request.user.is_authenticated: return JsonResponse({"error": "unauthorized"}, status=401)
    if request.method != 'POST':
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    hostname = data.get('hostname', '').strip()
    if not hostname:
        return JsonResponse({"error": "hostname is required"}, status=400)

    if Host.objects.filter(hostname=hostname, user=request.user).exists():
        return JsonResponse({"error": "Host already exists"}, status=409)

    api_key = secrets.token_hex(16)
    host = Host.objects.create(user=request.user, hostname=hostname, api_key=api_key)

    server_url = request.build_absolute_uri('/api/ingest/')
    agent_config = f"""import time
import requests
import psutil
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:
    pass

SERVER_URL = "{server_url}"
HOSTNAME = "{hostname}"
API_KEY = "{api_key}"
INTERVAL = 5

prev_sent = None
prev_recv = None
prev_disk_read = None
prev_disk_write = None
prev_time = None

def bytes_per_sec(curr, prev, dt):
    if prev is None or dt <= 0:
        return 0.0
    return (curr-prev)/dt

while True:
    now = time.time()
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("C:\\\\").percent if hasattr(psutil, 'disk_usage') else 0
    net = psutil.net_io_counters()
    disk_io = psutil.disk_io_counters()

    if prev_time is None:
        sent_per_sec = 0.0
        recv_per_sec = 0.0
        disk_read_kb = 0.0
        disk_write_kb = 0.0
        dt = 1.0
    else:
        dt = now - prev_time
        sent_per_sec = bytes_per_sec(net.bytes_sent, prev_sent, dt)
        recv_per_sec = bytes_per_sec(net.bytes_recv, prev_recv, dt)
        disk_read_kb = bytes_per_sec(disk_io.read_bytes, prev_disk_read, dt) / 1024.0 if disk_io else 0.0
        disk_write_kb = bytes_per_sec(disk_io.write_bytes, prev_disk_write, dt) / 1024.0 if disk_io else 0.0

    prev_sent = net.bytes_sent
    prev_recv = net.bytes_recv
    prev_disk_read = disk_io.read_bytes if disk_io else 0
    prev_disk_write = disk_io.write_bytes if disk_io else 0
    prev_time = now

    top_processes = []
    try:
        procs = []
        for p in psutil.process_iter(['name', 'memory_percent']):
            try:
                mem = p.info['memory_percent'] or 0.0
                procs.append((p.info['name'], mem))
            except Exception:
                pass
        procs.sort(key=lambda x: x[1], reverse=True)
        top_processes = [{{"name": n, "mem": round(m, 1)}} for n, m in procs[:3]]
    except Exception:
        pass

    cpu_temp = None
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for name in ['coretemp', 'cpu_thermal', 'k10temp', 'acpitz']:
                if name in temps and temps[name]:
                    cpu_temp = temps[name][0].current
                    break
            if cpu_temp is None:
                for sensor_list in temps.values():
                    if sensor_list:
                        cpu_temp = sensor_list[0].current
                        break
    except Exception: pass

    cpu_freq = None
    try:
        freq = psutil.cpu_freq()
        if freq: cpu_freq = round(freq.current, 0)
    except Exception: pass

    try:
        tz = ZoneInfo("Asia/Kolkata")
    except Exception:
        tz = timezone.utc
        
    payload = {{
        "hostname": HOSTNAME,
        "timestamp": datetime.now(tz).isoformat(),
        "cpu": cpu,
        "ram": ram,
        "disk": disk,
        "net_sent": sent_per_sec,
        "net_recv": recv_per_sec,
        "ping_ms": None,
        "cpu_temp": cpu_temp,
        "cpu_freq": cpu_freq,
        "top_processes": top_processes,
        "disk_read_kb": disk_read_kb,
        "disk_write_kb": disk_write_kb,
    }}
    
    try:
        r = requests.post(SERVER_URL, json=payload, headers={{"X-API-KEY": API_KEY}}, timeout=3)
        print("Sent:", r.status_code, r.text)
    except Exception as e:
        print("Error occured!:", e)
    time.sleep(INTERVAL)
"""

    return JsonResponse({
        "status": "created",
        "host_id": host.id,
        "hostname": hostname,
        "api_key": api_key,
        "agent_config": agent_config,
    })


# ─── Add Website Monitor API ──────────────────────────────────────────

@csrf_exempt
def api_add_website(request):
    """Add a new website to monitor."""
    if not request.user.is_authenticated: return JsonResponse({"error": "unauthorized"}, status=401)
    if request.method != 'POST':
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    url = data.get('url', '').strip()
    name = data.get('name', '').strip()

    if not url or not name:
        return JsonResponse({"error": "url and name are required"}, status=400)

    if WebsiteMonitor.objects.filter(url=url, user=request.user).exists():
        return JsonResponse({"error": "Website already being monitored"}, status=409)

    monitor = WebsiteMonitor.objects.create(
        user=request.user,
        url=url,
        name=name,
        expected_keyword=data.get('keyword', '').strip(),
        check_interval=data.get('interval', 30),
        expected_status=data.get('expected_status', 200),
    )

    return JsonResponse({
        "status": "created",
        "id": monitor.id,
        "name": monitor.name,
        "url": monitor.url,
    })


# ─── Delete Website Monitor API ──────────────────────────────────────

@csrf_exempt
def api_delete_website(request, monitor_id):
    """Delete a website monitor and all its checks."""
    if not request.user.is_authenticated: return JsonResponse({"error": "unauthorized"}, status=401)
    if request.method != 'POST':
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        monitor = WebsiteMonitor.objects.get(id=monitor_id, user=request.user)
    except WebsiteMonitor.DoesNotExist:
        return JsonResponse({"error": "Website not found"}, status=404)

    monitor.delete()
    return JsonResponse({"status": "deleted"})


# ─── Edit Website Monitor API ────────────────────────────────────────

@csrf_exempt
def api_edit_website(request, monitor_id):
    """Edit a website monitor's name or URL."""
    if not request.user.is_authenticated: return JsonResponse({"error": "unauthorized"}, status=401)
    if request.method != 'POST':
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        monitor = WebsiteMonitor.objects.get(id=monitor_id, user=request.user)
    except WebsiteMonitor.DoesNotExist:
        return JsonResponse({"error": "Website not found"}, status=404)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if 'name' in data and data['name'].strip():
        monitor.name = data['name'].strip()
    if 'url' in data and data['url'].strip():
        monitor.url = data['url'].strip()

    monitor.save()
    return JsonResponse({"status": "updated", "name": monitor.name, "url": monitor.url})


# ─── Rename Host API ─────────────────────────────────────────────────

@csrf_exempt
def api_rename_host(request, host_id):
    """Rename a host device."""
    if not request.user.is_authenticated: return JsonResponse({"error": "unauthorized"}, status=401)
    if request.method != 'POST':
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        host = Host.objects.get(id=host_id, user=request.user)
    except Host.DoesNotExist:
        return JsonResponse({"error": "Host not found"}, status=404)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    new_name = data.get('hostname', '').strip()
    if not new_name:
        return JsonResponse({"error": "hostname is required"}, status=400)

    if Host.objects.filter(hostname=new_name, user=request.user).exclude(id=host_id).exists():
        return JsonResponse({"error": "Hostname already in use"}, status=409)

    host.hostname = new_name
    host.save()
    return JsonResponse({"status": "renamed", "hostname": host.hostname})

# ─── Delete Host API ─────────────────────────────────────────────────

@csrf_exempt
def api_delete_host(request, host_id):
    """Delete a host device and all its history."""
    if not request.user.is_authenticated: return JsonResponse({"error": "unauthorized"}, status=401)
    if request.method != 'POST':
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        host = Host.objects.get(id=host_id, user=request.user)
    except Host.DoesNotExist:
        return JsonResponse({"error": "Host not found"}, status=404)

    host.delete()
    return JsonResponse({"status": "deleted"})

# ─── Set Webhook API ───────────────────────────────────────────────────

@csrf_exempt
def api_set_webhook(request):
    """Set Discord/Slack webhook for the user."""
    if not request.user.is_authenticated: return JsonResponse({"error": "unauthorized"}, status=401)
    if request.method != 'POST':
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    url = data.get('url', '').strip()
    
    # Delete any existing
    from .models import WebhookIntegration
    WebhookIntegration.objects.filter(user=request.user).delete()
    
    if url:
        WebhookIntegration.objects.create(user=request.user, url=url)
        return JsonResponse({"status": "updated", "msg": "Webhook linked effectively."})
    return JsonResponse({"status": "deleted", "msg": "Webhook removed successfully."})
