# NexJam — Network Anomaly Detection & Monitoring

NexJam is a self-hosted network monitoring tool built with Django. It tracks device health (CPU, RAM, disk, network), detects anomalies using z-score analysis, monitors website uptime/SSL, and sends alerts via Discord/Slack webhooks.

Built this for my college project to learn about real-time system monitoring and anomaly detection.

## What it does

- **Device Monitoring** — Deploy a lightweight Python agent on any machine. It sends CPU, RAM, disk, network, and temperature metrics every 5 seconds.
- **Anomaly Detection** — Uses z-score based statistical analysis. If a metric deviates significantly from its rolling average, it flags an alert (severity 1–3).
- **Website Monitoring** — Tracks uptime, response time, SSL certificate validity, and content keyword checks for any URL you add.
- **Webhook Alerts** — Connects to Discord or Slack. Severity 3 (critical) events trigger instant notifications.
- **Dashboard** — Single-page dashboard with live polling, charts, and an advice engine that tells you *what happened*, *why it matters*, and *what to do*.

## Tech Stack

- **Backend** — Django 5.2, SQLite (local) / PostgreSQL (production)
- **Frontend** — Vanilla HTML/CSS/JS with Chart.js, served from Django templates
- **Deployment** — Render (free tier), Gunicorn, WhiteNoise for static files
- **Agent** — Python script using psutil, runs on monitored machines

## Project Structure

```
NexJam/
├── anomaly_project/
│   ├── anomaly_project/    # Django project settings
│   │   ├── settings.py     # Config (uses env vars in production)
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── monitoring/         # Main app
│   │   ├── models.py       # Host, MetricSample, AnomalyEvent, WebsiteMonitor, etc.
│   │   ├── views.py        # All API endpoints + auth + dashboard
│   │   ├── detection.py    # Z-score anomaly detection engine
│   │   ├── website_checker.py  # Background website monitoring script
│   │   ├── urls.py
│   │   ├── templates/      # HTML templates (login, register, dashboard)
│   │   └── static/         # CSS + JS
│   └── agent/
│       └── agent.py        # Sample monitoring agent (runs on client machines)
├── requirements.txt
├── Procfile                # Render process config
├── build.sh                # Render build script
└── .gitignore
```

## Running Locally

1. **Clone and set up the virtual environment**

```bash
git clone https://github.com/YOUR_USERNAME/NexJam.git
cd NexJam
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

2. **Run migrations and start the server**

```bash
cd anomaly_project
python manage.py migrate
python manage.py createsuperuser   # optional, for admin panel
python manage.py runserver
```

3. **Open the dashboard** — go to `http://127.0.0.1:8000`

4. **Add a device** — click "Add Device" on the dashboard, copy the generated agent script, and run it on whatever machine you want to monitor.

5. **Start website monitoring** (optional)

```bash
# In a separate terminal
cd anomaly_project
python -m monitoring.website_checker
```

## Deploying to Render

1. Push the repo to GitHub

2. Go to [render.com](https://render.com) → **New Web Service** → connect your GitHub repo

3. Set the following:
   - **Build Command:** `./build.sh`
   - **Start Command:** `cd anomaly_project && gunicorn anomaly_project.wsgi:application --bind 0.0.0.0:$PORT`

4. Add these **environment variables** on Render:

| Variable | Value |
|---|---|
| `SECRET_KEY` | Generate one: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `your-app-name.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://your-app-name.onrender.com` |
| `DATABASE_URL` | Auto-filled if you create a Render PostgreSQL database |
| `PYTHON_VERSION` | `3.11.6` |

5. Create a **PostgreSQL** database on Render (free tier) and link it to the web service. Render auto-sets `DATABASE_URL`.

6. Deploy. That's it.

## How the Agent Works

The agent is a small Python script that runs on each machine you want to monitor. It collects system metrics using `psutil` and POSTs them to the NexJam server every 5 seconds.

When you add a device through the dashboard, NexJam generates a ready-to-run agent script with the server URL and API key pre-filled. Just copy, save as `agent.py`, and run it:

```bash
pip install requests psutil
python agent.py
```

Each device gets its own API key. No device can see another device's data.

## How Anomaly Detection Works

NexJam uses a z-score approach:

1. Collects the last 30 metric samples for each metric (CPU, RAM, disk, net sent/recv, ping)
2. Calculates the rolling mean and standard deviation
3. If the current value deviates by more than 3 standard deviations (z > 3), it's flagged as anomalous
4. Noise filter: requires at least 2 of the last 3 readings to be anomalous before creating an alert
5. Alerts auto-resolve when the metric returns to normal range

Severity levels:
- **1** — Minor anomaly (z > 3)
- **2** — Moderate (z > 2, sustained)
- **3** — Critical (z > 6) — triggers webhook alerts

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/ingest/` | POST | Receive metrics from agents (requires X-API-KEY header) |
| `/api/hosts/` | GET | List all monitored hosts |
| `/api/hosts/<id>/` | GET | Get host details + recent metrics |
| `/api/anomalies/` | GET | List recent anomaly events |
| `/api/advice/` | GET | Get actionable advice for active alerts |
| `/api/websites/` | GET | List monitored websites |
| `/api/add-host/` | POST | Register a new host |
| `/api/add-website/` | POST | Add a website to monitor |
| `/api/set-webhook/` | POST | Set Discord/Slack webhook URL |

## License

MIT — do whatever you want with it.
