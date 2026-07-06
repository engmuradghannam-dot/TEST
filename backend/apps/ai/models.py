"""
AI Layer for Nexus SaaS
Predictive analytics, automation, and intelligent recommendations
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import JSONField
import logging

logger = logging.getLogger(__name__)


class AIModel(models.Model):
    """Registered AI/ML Models"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))

    class ModelType(models.TextChoices):
        PREDICTIVE = 'predictive', _('Predictive')
        CLASSIFICATION = 'classification', _('Classification')
        FORECASTING = 'forecasting', _('Forecasting')
        ANOMALY_DETECTION = 'anomaly_detection', _('Anomaly Detection')
        NLP = 'nlp', _('Natural Language Processing')
        RECOMMENDATION = 'recommendation', _('Recommendation')
        OPTIMIZATION = 'optimization', _('Optimization')
        GENERATIVE = 'generative', _('Generative AI')

    model_type = models.CharField(max_length=30, choices=ModelType.choices, verbose_name=_('Model Type'))

    # Model source
    class SourceType(models.TextChoices):
        BUILT_IN = 'built_in', _('Built-in')
        CUSTOM = 'custom', _('Custom')
        EXTERNAL_API = 'external_api', _('External API')
        HUGGINGFACE = 'huggingface', _('Hugging Face')
        OPENAI = 'openai', _('OpenAI')
        ANTHROPIC = 'anthropic', _('Anthropic')

    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.BUILT_IN)

    # Configuration
    config = models.JSONField(default=dict, verbose_name=_('Configuration'))
    api_endpoint = models.URLField(blank=True, verbose_name=_('API Endpoint'))
    api_key_env = models.CharField(max_length=100, blank=True, verbose_name=_('API Key Environment Variable'))

    # Model file (for custom models)
    model_file = models.FileField(upload_to='ai_models/', blank=True, verbose_name=_('Model File'))

    # Performance metrics
    accuracy = models.FloatField(null=True, blank=True, verbose_name=_('Accuracy'))
    last_trained = models.DateTimeField(null=True, blank=True, verbose_name=_('Last Trained'))
    training_data_size = models.PositiveIntegerField(default=0, verbose_name=_('Training Data Size'))

    # Status
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    is_default = models.BooleanField(default=False, verbose_name=_('Is Default'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('AI Model')
        verbose_name_plural = _('AI Models')

    def __str__(self):
        return f"{self.name} ({self.model_type})"


class AIPrediction(models.Model):
    """AI Predictions and Recommendations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='predictions')

    # Input/Output
    input_data = models.JSONField(verbose_name=_('Input Data'))
    output_data = models.JSONField(verbose_name=_('Output Data'))
    confidence = models.FloatField(null=True, blank=True, verbose_name=_('Confidence Score'))

    # Context
    entity_type = models.CharField(max_length=100, verbose_name=_('Entity Type'))
    entity_id = models.CharField(max_length=100, verbose_name=_('Entity ID'))

    # Feedback
    class FeedbackStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        REJECTED = 'rejected', _('Rejected')
        PARTIAL = 'partial', _('Partial')

    feedback_status = models.CharField(max_length=20, choices=FeedbackStatus.choices, default=FeedbackStatus.PENDING)
    feedback_notes = models.TextField(blank=True, verbose_name=_('Feedback Notes'))

    # Performance
    execution_time_ms = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Execution Time (ms)'))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('AI Prediction')
        verbose_name_plural = _('AI Predictions')


class AIAutomationRule(models.Model):
    """AI-powered Automation Rules"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))

    # Trigger
    trigger_event = models.CharField(max_length=200, verbose_name=_('Trigger Event'))
    trigger_conditions = models.JSONField(default=dict, verbose_name=_('Trigger Conditions'))

    # AI Action
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, related_name='automation_rules')
    action_config = models.JSONField(default=dict, verbose_name=_('Action Configuration'))

    # Execution
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    execution_count = models.PositiveIntegerField(default=0, verbose_name=_('Execution Count'))
    last_executed = models.DateTimeField(null=True, blank=True, verbose_name=_('Last Executed'))

    # Limits
    max_executions_per_hour = models.PositiveIntegerField(default=100, verbose_name=_('Max Executions/Hour'))
    cooldown_minutes = models.PositiveIntegerField(default=0, verbose_name=_('Cooldown (Minutes)'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('AI Automation Rule')
        verbose_name_plural = _('AI Automation Rules')


class InventoryForecast(models.Model):
    """AI Inventory Forecasting"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey('inventory.InventoryItem', on_delete=models.CASCADE, related_name='forecasts')

    # Forecast data
    forecast_date = models.DateField(verbose_name=_('Forecast Date'))
    predicted_demand = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_('Predicted Demand'))
    predicted_stock_level = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_('Predicted Stock Level'))
    confidence_interval_lower = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_('Confidence Lower'))
    confidence_interval_upper = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_('Confidence Upper'))

    # Model used
    model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)

    # Actual (for validation)
    actual_demand = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-forecast_date']
        unique_together = ['product', 'forecast_date']
        verbose_name = _('Inventory Forecast')
        verbose_name_plural = _('Inventory Forecasts')


class SmartAccountingSuggestion(models.Model):
    """AI Smart Accounting Suggestions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Source transaction
    transaction_type = models.CharField(max_length=100, verbose_name=_('Transaction Type'))
    transaction_data = models.JSONField(verbose_name=_('Transaction Data'))

    # AI Suggestion
    suggested_account = models.CharField(max_length=200, verbose_name=_('Suggested Account'))
    suggested_category = models.CharField(max_length=200, verbose_name=_('Suggested Category'))
    suggested_tags = models.JSONField(default=list, verbose_name=_('Suggested Tags'))
    confidence = models.FloatField(verbose_name=_('Confidence'))

    # User action
    is_applied = models.BooleanField(default=False, verbose_name=_('Is Applied'))
    applied_by = models.ForeignKey('tenants.TenantUser', on_delete=models.SET_NULL, null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    # Model
    model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Smart Accounting Suggestion')
        verbose_name_plural = _('Smart Accounting Suggestions')
