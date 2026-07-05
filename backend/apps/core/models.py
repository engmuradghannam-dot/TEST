from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager

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
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class Company(models.Model):
    name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    currency = models.CharField(max_length=10, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Branch(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Warehouse(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='warehouses', null=True, blank=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


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
