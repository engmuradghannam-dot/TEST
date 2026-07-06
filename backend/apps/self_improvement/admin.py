from django.contrib import admin
from .models import ImprovementSuggestion


@admin.register(ImprovementSuggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ("title", "area", "confidence", "status", "created_at")
    list_filter = ("area", "status")
