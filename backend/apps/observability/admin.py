from django.contrib import admin
from .models import Metric, Alert


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "company", "recorded_at")
    list_filter = ("name",)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "severity", "status", "fired_at")
    list_filter = ("category", "severity", "status")
