from django.db import models
from apps.core.models import Company
from apps.hr.models import Employee, Team

class Project(models.Model):
    STATUS_CHOICES = [('Open', 'Open'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled'), ('On Hold', 'On Hold')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    project_name = models.CharField(max_length=255)
    project_code = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Open')
    expected_start = models.DateField(null=True, blank=True)
    expected_end = models.DateField(null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project_name

class Task(models.Model):
    STATUS_CHOICES = [('Open', 'Open'), ('Working', 'Working'), ('Pending Review', 'Pending Review'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')]
    PRIORITY_CHOICES = [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Urgent', 'Urgent')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Open')
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='Medium')
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks',
        help_text='If set, every member of this team can see this task even if not personally assigned.'
    )
    expected_start = models.DateField(null=True, blank=True)
    expected_end = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject
