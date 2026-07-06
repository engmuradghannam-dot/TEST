
from django.contrib import admin
from .models import AIModel, AIPrediction, AIAutomationRule, InventoryForecast, SmartAccountingSuggestion

@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_type', 'source_type', 'accuracy', 'is_active', 'is_default']
    list_filter = ['model_type', 'source_type', 'is_active']
    search_fields = ['name', 'slug']

@admin.register(AIPrediction)
class AIPredictionAdmin(admin.ModelAdmin):
    list_display = ['model', 'entity_type', 'confidence', 'feedback_status', 'created_at']
    list_filter = ['feedback_status', 'model__model_type']

@admin.register(AIAutomationRule)
class AIAutomationRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'ai_model', 'is_active', 'execution_count', 'last_executed']
    list_filter = ['is_active', 'ai_model']

@admin.register(InventoryForecast)
class InventoryForecastAdmin(admin.ModelAdmin):
    list_display = ['product', 'forecast_date', 'predicted_demand', 'accuracy']
    list_filter = ['forecast_date']

@admin.register(SmartAccountingSuggestion)
class SmartAccountingSuggestionAdmin(admin.ModelAdmin):
    list_display = ['transaction_type', 'suggested_account', 'confidence', 'is_applied']
    list_filter = ['is_applied', 'confidence']
