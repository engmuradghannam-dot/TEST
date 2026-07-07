from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import FileExtensionValidator
from apps.core.validators import validate_image_size, ALLOWED_IMAGE_EXTENSIONS

class Module(models.Model):
    """Represents a functional module of the ERP (e.g. Accounts, HR, Inventory)
    used to control which parts of the system a user can access."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=50, default='User', choices=[
        ('Admin', 'Admin'), ('Manager', 'Manager'), ('User', 'User'), ('Accountant', 'Accountant')
    ])
    company = models.ForeignKey(
        'Company', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='users',
        help_text='Tenant this login belongs to. Left null only for superusers.'
    )
    branch = models.ForeignKey(
        'Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='users'
    )
    department = models.ForeignKey('hr.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    time_zone = models.CharField(max_length=50, default='Asia/Riyadh')
    notifications_enabled = models.BooleanField(default=True)
    profile_photo = models.ImageField(
        upload_to='profile_photos/', blank=True, null=True,
        validators=[validate_image_size, FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS)]
    )
    notes = models.TextField(blank=True)
    accessible_modules = models.ManyToManyField(Module, blank=True, related_name='users')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='ar', choices=[('ar', 'Arabic'), ('en', 'English')])
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class Company(models.Model):
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    commercial_registration = models.CharField(max_length=100, blank=True)
    vat_number = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Saudi Arabia')
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(
        upload_to='logos/', blank=True, null=True,
        validators=[validate_image_size, FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS)]
    )
    currency = models.CharField(max_length=10, default='SAR')
    default_language = models.CharField(max_length=10, default='ar', choices=[('ar', 'Arabic'), ('en', 'English')])
    fiscal_year_start = models.DateField(null=True, blank=True)
    fiscal_year_end = models.DateField(null=True, blank=True)
    time_zone = models.CharField(max_length=50, default='Asia/Riyadh')
    date_format = models.CharField(max_length=20, default='DD-MM-YYYY')
    number_format = models.CharField(max_length=20, default='#,###.##')
    default_warehouse = models.ForeignKey('Warehouse', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    default_branch = models.ForeignKey('Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    a4_top_margin = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    a4_bottom_margin = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    a4_left_margin = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    a4_right_margin = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    page_header = models.TextField(blank=True)
    page_footer = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=100, blank=True)
    iban = models.CharField(max_length=50, blank=True)
    social_media_links = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Branch(models.Model):
    STATUS_CHOICES = [('Active', 'Active'), ('Inactive', 'Inactive')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    branch_code = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Saudi Arabia')
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    manager = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_branches')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    google_maps_link = models.URLField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Warehouse(models.Model):
    WAREHOUSE_TYPES = [
        ('Main', 'Main'), ('Transit', 'Transit'), ('Returns', 'Returns'), ('Damaged', 'Damaged'),
    ]
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='warehouses', null=True, blank=True)
    parent_warehouse = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_warehouses')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    warehouse_type = models.CharField(max_length=50, choices=WAREHOUSE_TYPES, default='Main')
    address = models.TextField(blank=True)
    manager = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_warehouses')
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    capacity = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    zones = models.TextField(blank=True, help_text='Comma-separated zone/aisle names within this warehouse')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name

    @property
    def current_stock(self):
        from apps.inventory.models import StockEntry
        total = 0
        for e in StockEntry.objects.filter(warehouse=self):
            total += e.quantity if e.entry_type == 'Receipt' else -e.quantity
        return total


class PrintTemplate(models.Model):
    DOCUMENT_TYPES = [
        ('Purchase Order', 'Purchase Order'), ('Sales Order', 'Sales Order'),
        ('Invoice', 'Invoice'), ('Payslip', 'Payslip'), ('Journal Entry', 'Journal Entry'),
    ]
    PAGE_SIZES = [('A4', 'A4'), ('A5', 'A5'), ('Letter', 'Letter')]
    ORIENTATIONS = [('Portrait', 'Portrait'), ('Landscape', 'Landscape')]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='print_templates')
    name = models.CharField(max_length=255)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    page_size = models.CharField(max_length=20, choices=PAGE_SIZES, default='A4')
    orientation = models.CharField(max_length=20, choices=ORIENTATIONS, default='Portrait')
    top_margin = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    bottom_margin = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    left_margin = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    right_margin = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    header = models.TextField(blank=True)
    footer = models.TextField(blank=True)
    show_logo = models.BooleanField(default=True)
    show_signature = models.BooleanField(default=False)
    show_stamp = models.BooleanField(default=False)
    font_family = models.CharField(max_length=100, default='Arial')
    font_size = models.PositiveIntegerField(default=12)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.document_type})"


class AuditLog(models.Model):
    """Immutable, append-only record of who changed what and when.
    Populated automatically via signals (see apps/core/audit.py) — never
    written to directly, and there is intentionally no update/delete API
    for it."""
    ACTION_CHOICES = [('Create', 'Create'), ('Update', 'Update'), ('Delete', 'Delete')]
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_entries')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    app_label = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100, db_index=True)
    object_id = models.CharField(max_length=50, db_index=True)
    object_repr = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict, blank=True, help_text='For Update: {field: [old, new]}. For Create: {field: new}.')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} {self.model_name}#{self.object_id} @ {self.timestamp}"


class UIScreen(models.Model):
    """Low-code screen definition: a JSON schema the frontend FormEngine
    renders into a working data-entry screen without code changes."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE,
                                related_name='ui_screens')
    slug = models.SlugField(max_length=80)
    title = models.CharField(max_length=120)
    title_ar = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    schema = models.JSONField(
        default=dict,
        help_text='{"fields": [{"name","type","label","label_ar",'
                  '"required","options","default"}], "layout": "single|two-col"}')
    target_endpoint = models.CharField(
        max_length=200, blank=True,
        help_text='API path form submissions POST to, e.g. /api/v1/crm/leads/')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('company', 'slug')]
        ordering = ['title']

    def __str__(self):
        return self.title


# ── Enterprise security & AI-core models (kept in core app_label) ──
from apps.core.security.immutable_audit import AuditLedgerEntry  # noqa: E402,F401
from apps.core.intelligence.knowledge_graph import (  # noqa: E402,F401
    GraphNode, GraphEdge,
)
# === Event Sourcing & Distributed Architecture Models ===
from django.db import models
import uuid
from django.utils import timezone

class EventStore(models.Model):
    """Event Store for Event Sourcing Pattern"""
    EVENT_TYPES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('command', 'Command'),
        ('snapshot', 'Snapshot'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    aggregate_id = models.UUIDField(db_index=True)
    aggregate_type = models.CharField(max_length=100, db_index=True)
    version = models.PositiveIntegerField(db_index=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    event_data = models.JSONField()
    metadata = models.JSONField(default=dict, blank=True)
    region = models.CharField(max_length=50, default='us-east-1')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    correlation_id = models.UUIDField(null=True, blank=True, db_index=True)
    causation_id = models.UUIDField(null=True, blank=True)
    user_id = models.UUIDField(null=True, blank=True)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['aggregate_id', 'version']
        unique_together = ['aggregate_id', 'version']
        indexes = [
            models.Index(fields=['aggregate_type', 'timestamp']),
            models.Index(fields=['tenant_id', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['region', 'timestamp']),
        ]
        db_table = 'event_store'

class AggregateSnapshot(models.Model):
    """Snapshots for performance optimization"""
    aggregate_id = models.UUIDField(primary_key=True)
    aggregate_type = models.CharField(max_length=100)
    version = models.PositiveIntegerField()
    state = models.JSONField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    region = models.CharField(max_length=50, default='us-east-1')

    class Meta:
        indexes = [
            models.Index(fields=['aggregate_type', 'updated_at']),
        ]
        db_table = 'aggregate_snapshots'

class Projection(models.Model):
    """CQRS Read Model Projections"""
    projection_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    projection_name = models.CharField(max_length=255, db_index=True)
    projection_type = models.CharField(max_length=100)
    aggregate_id = models.UUIDField(db_index=True)
    aggregate_type = models.CharField(max_length=100)
    data = models.JSONField()
    version = models.PositiveIntegerField(default=0)
    is_stale = models.BooleanField(default=False)
    last_event_timestamp = models.DateTimeField(null=True, blank=True)
    region = models.CharField(max_length=50, default='us-east-1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['projection_name', 'aggregate_type']),
            models.Index(fields=['aggregate_id', 'projection_name']),
            models.Index(fields=['is_stale', 'updated_at']),
        ]
        db_table = 'projections'

class SagaInstance(models.Model):
    """Saga Orchestrator for Distributed Transactions"""
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('compensating', 'Compensating'),
        ('compensated', 'Compensated'),
        ('failed', 'Failed'),
    ]

    saga_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    saga_type = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='started')
    current_step = models.PositiveIntegerField(default=0)
    total_steps = models.PositiveIntegerField(default=0)
    steps_data = models.JSONField(default=list)
    compensation_data = models.JSONField(default=list)
    context = models.JSONField(default=dict)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    region = models.CharField(max_length=50, default='us-east-1')
    tenant_id = models.UUIDField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['saga_type', 'status']),
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['started_at']),
        ]
        db_table = 'saga_instances'

class OutboxEvent(models.Model):
    """Outbox Pattern for Reliable Event Publishing"""
    id = models.BigAutoField(primary_key=True)
    aggregate_type = models.CharField(max_length=100)
    aggregate_id = models.UUIDField()
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    headers = models.JSONField(default=dict)
    destination_topic = models.CharField(max_length=255)
    partition_key = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    region = models.CharField(max_length=50, default='us-east-1')

    class Meta:
        indexes = [
            models.Index(fields=['processed_at', 'created_at']),
            models.Index(fields=['destination_topic', 'processed_at']),
        ]
        ordering = ['created_at']
        db_table = 'outbox_events'

class MultiRegionSync(models.Model):
    """Track cross-region data synchronization"""
    SYNC_TYPES = [
        ('full', 'Full Sync'),
        ('incremental', 'Incremental'),
        ('conflict_resolution', 'Conflict Resolution'),
    ]

    sync_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    source_region = models.CharField(max_length=50)
    target_region = models.CharField(max_length=50)
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    entity_type = models.CharField(max_length=100)
    entity_id = models.UUIDField()
    data_hash = models.CharField(max_length=64)
    status = models.CharField(max_length=20, default='pending')
    conflict_detected = models.BooleanField(default=False)
    conflict_resolution = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['source_region', 'target_region']),
            models.Index(fields=['entity_type', 'status']),
            models.Index(fields=['synced_at']),
        ]
        db_table = 'multi_region_sync'

class DistributedLock(models.Model):
    """Distributed Lock for Multi-Region Coordination"""
    lock_key = models.CharField(max_length=255, primary_key=True)
    owner = models.CharField(max_length=255)
    region = models.CharField(max_length=50)
    acquired_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_released = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['expires_at', 'is_released']),
        ]
        db_table = 'distributed_locks'
