"""
MongoDB Models for Nexus Framework
Used for: Logs, Analytics, Unstructured Data, Time-Series
"""
from mongoengine import (
    Document, EmbeddedDocument, StringField, IntField, 
    FloatField, DateTimeField, ListField, DictField,
    EmbeddedDocumentField, ReferenceField, BooleanField,
    connect, disconnect
)
from datetime import datetime
import uuid

# Connect to MongoDB Atlas
# connect(
#     db='nexus_analytics',
#     host='mongodb+srv://user:pass@cluster.mongodb.net/nexus_analytics',
#     retryWrites=True,
#     w='majority'
# )

class ActivityLog(Document):
    """High-volume activity logs stored in MongoDB"""
    meta = {
        'collection': 'activity_logs',
        'indexes': [
            {'fields': ['timestamp']},
            {'fields': ['user_id']},
            {'fields': ['tenant_id']},
            {'fields': ['event_type']},
            {'fields': ['timestamp', 'tenant_id']},
        ],
        'ordering': ['-timestamp']
    }

    log_id = StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = DateTimeField(default=datetime.utcnow)
    user_id = StringField(required=True)
    tenant_id = StringField(required=True)
    session_id = StringField()

    event_type = StringField(required=True)  # page_view, click, api_call, etc.
    event_name = StringField()

    # Request details
    method = StringField()  # GET, POST, etc.
    path = StringField()
    status_code = IntField()
    duration_ms = FloatField()

    # Context
    ip_address = StringField()
    user_agent = StringField()
    referer = StringField()

    # Custom properties
    properties = DictField()

    # Geo info
    country = StringField()
    city = StringField()
    region = StringField()

    def __str__(self):
        return f"{self.event_type} - {self.path} ({self.user_id})"


class TimeSeriesMetric(Document):
    """Time-series metrics for analytics"""
    meta = {
        'collection': 'time_series_metrics',
        'indexes': [
            {'fields': ['timestamp']},
            {'fields': ['metric_name', 'timestamp']},
            {'fields': ['tenant_id', 'metric_name', 'timestamp']},
        ],
        'ordering': ['-timestamp']
    }

    metric_id = StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = DateTimeField(default=datetime.utcnow)
    tenant_id = StringField(required=True)

    metric_name = StringField(required=True)
    metric_type = StringField()  # gauge, counter, histogram

    value = FloatField(required=True)
    unit = StringField()

    # Dimensions/Tags
    dimensions = DictField()

    # Aggregation
    min_value = FloatField()
    max_value = FloatField()
    avg_value = FloatField()
    count = IntField(default=1)

    # Source
    source = StringField()  # application, infrastructure, business
    region = StringField()


class AuditTrail(Document):
    """Immutable audit trail"""
    meta = {
        'collection': 'audit_trail',
        'indexes': [
            {'fields': ['timestamp']},
            {'fields': ['entity_type', 'entity_id']},
            {'fields': ['user_id']},
            {'fields': ['action']},
        ],
        'ordering': ['-timestamp']
    }

    audit_id = StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = DateTimeField(default=datetime.utcnow)

    user_id = StringField(required=True)
    user_email = StringField()
    tenant_id = StringField()

    action = StringField(required=True)  # CREATE, READ, UPDATE, DELETE
    entity_type = StringField(required=True)
    entity_id = StringField(required=True)

    # Change details
    before_state = DictField()
    after_state = DictField()
    changes = ListField(DictField())

    # Context
    ip_address = StringField()
    user_agent = StringField()
    request_id = StringField()
    correlation_id = StringField()

    # Compliance
    compliance_framework = StringField()
    retention_until = DateTimeField()

    def __str__(self):
        return f"{self.action} {self.entity_type}:{self.entity_id} by {self.user_id}"


class SearchIndex(Document):
    """Full-text search index"""
    meta = {
        'collection': 'search_index',
        'indexes': [
            {'fields': ['$search_text']},  # Text index
            {'fields': ['entity_type']},
            {'fields': ['tenant_id']},
            {'fields': ['updated_at']},
        ],
        'ordering': ['-updated_at']
    }

    index_id = StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = StringField(required=True)

    entity_type = StringField(required=True)
    entity_id = StringField(required=True)

    title = StringField()
    content = StringField()
    search_text = StringField()

    # Facets
    tags = ListField(StringField())
    categories = ListField(StringField())

    # Metadata
    metadata = DictField()

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.search_text = f"{self.title} {self.content} {' '.join(self.tags)}"
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class AnalyticsDashboard(Document):
    """User-created analytics dashboards"""
    meta = {
        'collection': 'analytics_dashboards',
        'indexes': [
            {'fields': ['tenant_id']},
            {'fields': ['created_by']},
        ]
    }

    dashboard_id = StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = StringField(required=True)
    created_by = StringField(required=True)

    name = StringField(required=True)
    description = StringField()

    # Widgets
    widgets = ListField(DictField())

    # Layout
    layout = DictField()

    # Filters
    default_filters = DictField()

    # Sharing
    is_shared = BooleanField(default=False)
    shared_with = ListField(StringField())

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)


class MLModelStore(Document):
    """Store ML model artifacts"""
    meta = {
        'collection': 'ml_models',
        'indexes': [
            {'fields': ['model_name']},
            {'fields': ['version']},
            {'fields': ['tenant_id']},
        ]
    }

    model_id = StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = StringField()

    model_name = StringField(required=True)
    version = StringField(required=True)

    # Model metadata
    framework = StringField()  # tensorflow, pytorch, sklearn
    architecture = StringField()

    # Performance
    metrics = DictField()  # accuracy, precision, recall, etc.
    training_data_stats = DictField()

    # Storage
    artifact_path = StringField()  # S3 path
    artifact_size_mb = FloatField()

    # Status
    status = StringField(default='draft')  # draft, staging, production, archived

    created_at = DateTimeField(default=datetime.utcnow)
    deployed_at = DateTimeField()
