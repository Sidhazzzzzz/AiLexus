import math
import requests
from django.utils import timezone
from .models import MetricSample, AnomalyEvent, WebhookIntegration
METRICS = ["cpu", "ram", "disk", "net_sent", "net_recv", "ping_ms"]
N = 30
Z_THRESHOLD = 3.0


def mean(values):
    return sum(values)/len(values)


def std(values, m):
    var = sum((x-m)**2 for x in values)/len(values)
    return math.sqrt(var)


def severity_from_z(z):
    if z > 6:
        return 3
    if z > 2:
        return 2
    return 1


def run_detection(host, current_sample):
    # fetch the samples
    for metric in METRICS:
        qs = MetricSample.objects.filter(host=host).order_by("-timestamp")[:30]
        samples = list(qs)
        # Not enough samples
        if len(samples) < 10:
            continue
            
        values = [getattr(s, metric) for s in samples]
        m = mean(values)
        s = std(values, m)
        if s < 1e-6:
            continue
            
        current_value = getattr(current_sample, metric)
        z = (current_value - m) / s
        is_abnormal = abs(z) > Z_THRESHOLD
        
        # Noise filter: require at least 2 of the last 3 samples to be abnormal
        count_abnormal = 0
        last3 = samples[:3]
        for smp in last3:
            v = getattr(smp, metric)
            z3 = (v - m) / s
            if abs(z3) > Z_THRESHOLD:
                count_abnormal += 1
                
        # Find any currently active (unresolved) alert for this metric
        active_event = AnomalyEvent.objects.filter(host=host, metric_name=metric, is_resolved=False).first()

        if is_abnormal and count_abnormal >= 2:
            # We have an ongoing anomaly.
            sev = severity_from_z(z)
            reason = f"z={z:.2f}, mean = {m:.2f}, last3_abnormal={count_abnormal}"
            
            if active_event:
                # 🚀 AUTO-UPDATE: The issue persists, so we update the existing alert seamlessly
                active_event.value = current_value
                active_event.severity = sev
                active_event.reason = reason
                active_event.timestamp = timezone.now()
                active_event.save(update_fields=['value', 'severity', 'reason', 'timestamp'])
            else:
                # 🚀 NOVEL ANOMALY: The issue is new, so we create a fresh alert
                AnomalyEvent.objects.create(
                    host=host,
                    timestamp=timezone.now(),
                    metric_name=metric,
                    value=current_value,
                    severity=sev,
                    reason=reason
                )
                
                # 🔔 TRIGGER WEBHOOK FOR SEVERITY 3
                if sev == 3:
                    webhooks = WebhookIntegration.objects.filter(user=host.user, is_active=True)
                    for wh in webhooks:
                        try:
                            payload = {
                                "content": f"🚨 **CRITICAL ALERT** 🚨\n**Host:** `{host.hostname}`\n**Metric:** `{metric}` spiked to `{current_value}`\n**Reason:** {reason}"
                            }
                            requests.post(wh.url, json=payload, timeout=2)
                        except Exception:
                            pass
        else:
            # We are back to normal operations.
            if active_event:
                # 🚀 AUTO-RESOLVE: The system has recovered, clear the alert automatically
                active_event.is_resolved = True
                active_event.save(update_fields=['is_resolved'])
