from django.db import models
from django.contrib.auth.models import User

class Host(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hostname = models.CharField(max_length=100)
    api_key = models.CharField(max_length=64)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.hostname

    @property
    def latest_sample(self):
        return self.metricsample_set.order_by("-timestamp").first()


class MetricSample(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    cpu = models.FloatField()
    ram = models.FloatField()
    disk = models.FloatField()
    net_sent = models.FloatField()
    net_recv = models.FloatField()
    ping_ms = models.FloatField(null=True, blank=True)
    cpu_temp = models.FloatField(null=True, blank=True)
    cpu_freq = models.FloatField(null=True, blank=True)
    top_processes = models.TextField(null=True, blank=True)
    disk_read_kb = models.FloatField(null=True, blank=True)
    disk_write_kb = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f'{self.host.hostname} @ {self.timestamp}'


class AnomalyEvent(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    metric_name = models.CharField(max_length=50)
    value = models.FloatField()
    severity = models.IntegerField()
    reason = models.TextField()
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.host.hostname} {self.timestamp} with sev:{self.severity}'


# ─── Website Monitoring ────────────────────────────────────────────────


class WebsiteMonitor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField(max_length=500)
    name = models.CharField(max_length=100)
    expected_keyword = models.CharField(max_length=100, blank=True, null=True, help_text="Keyword that must appear on the page")
    check_interval = models.IntegerField(default=30, help_text="seconds between checks")
    expected_status = models.IntegerField(default=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} ({self.url})'


class WebsiteCheck(models.Model):
    monitor = models.ForeignKey(WebsiteMonitor, on_delete=models.CASCADE, related_name='checks')
    timestamp = models.DateTimeField()
    status_code = models.IntegerField(null=True, blank=True)
    response_time_ms = models.FloatField(null=True, blank=True)
    is_up = models.BooleanField(default=True)
    ssl_valid = models.BooleanField(default=True)
    ssl_expiry_days = models.IntegerField(null=True, blank=True)
    error = models.TextField(blank=True, default='')

    def __str__(self):
        status = "UP" if self.is_up else "DOWN"
        return f'{self.monitor.name} {status} @ {self.timestamp}'


class WebhookIntegration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField(max_length=500, help_text="Discord or Slack Webhook URL")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Webhook for {self.user.username}"
