from django.contrib import admin
from .models import Host, MetricSample, AnomalyEvent, WebsiteMonitor, WebsiteCheck

admin.site.register(Host)
admin.site.register(MetricSample)
admin.site.register(AnomalyEvent)
admin.site.register(WebsiteMonitor)
admin.site.register(WebsiteCheck)
