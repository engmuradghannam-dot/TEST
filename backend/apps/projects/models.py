from django.db import models
from apps.core.models import Company
from apps.hr.models import Employee, Team

class Project(models.Model):
    STATUS_CHOICES = [('Open', 'Open'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled'), ('On Hold', 'On Hold')]
    PRIORITY_CHOICES = [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Urgent', 'Urgent')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    project_name = models.CharField(max_length=255)
    project_code = models.CharField(max_length=100, unique=True)
    owner = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_projects', help_text='Project Manager')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Open')
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='Medium')
    expected_start = models.DateField(null=True, blank=True)
    expected_end = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    estimated_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    business_case = models.TextField(blank=True, help_text='Why this project exists: justification, expected benefits')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def progress_percent(self):
        total = self.tasks.count()
        if not total:
            return 0
        done = self.tasks.filter(status='Completed').count()
        return round((done / total) * 100, 1)

    @property
    def budget_variance(self):
        return self.budget - self.actual_cost

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
    depends_on = models.ManyToManyField(
        'self', symmetrical=False, blank=True, related_name='blocks',
        help_text='Tasks that must be completed before this one can start.'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject


class Milestone(models.Model):
    STATUS_CHOICES = [('Pending', 'Pending'), ('Achieved', 'Achieved'), ('Missed', 'Missed')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=255)
    due_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    description = models.TextField(blank=True)

    @property
    def is_overdue(self):
        import datetime
        return self.status == 'Pending' and self.due_date < datetime.date.today()

    def __str__(self):
        return f"{self.project.project_name} - {self.name}"


class Stakeholder(models.Model):
    INFLUENCE_CHOICES = [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')]
    INTEREST_CHOICES = [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='stakeholders')
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, blank=True)
    organization = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    influence = models.CharField(max_length=20, choices=INFLUENCE_CHOICES, default='Medium')
    interest = models.CharField(max_length=20, choices=INTEREST_CHOICES, default='Medium')
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class RiskRegister(models.Model):
    STATUS_CHOICES = [('Open', 'Open'), ('Mitigated', 'Mitigated'), ('Closed', 'Closed'), ('Occurred', 'Occurred')]
    CATEGORY_CHOICES = [
        ('Technical', 'Technical'), ('Financial', 'Financial'), ('Schedule', 'Schedule'),
        ('Resource', 'Resource'), ('External', 'External'), ('Legal', 'Legal'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='risks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Technical')
    probability = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)], help_text='1 (rare) to 5 (almost certain)')
    impact = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)], help_text='1 (negligible) to 5 (severe)')
    owner = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_risks')
    mitigation_plan = models.TextField(blank=True)
    contingency_plan = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Open')
    identified_date = models.DateField(auto_now_add=True)

    @property
    def risk_score(self):
        return self.probability * self.impact

    @property
    def risk_level(self):
        score = self.risk_score
        if score >= 15:
            return 'Critical'
        if score >= 8:
            return 'High'
        if score >= 4:
            return 'Medium'
        return 'Low'

    def __str__(self):
        return self.title


class IssueLog(models.Model):
    SEVERITY_CHOICES = [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Critical', 'Critical')]
    STATUS_CHOICES = [('Open', 'Open'), ('In Progress', 'In Progress'), ('Resolved', 'Resolved'), ('Closed', 'Closed')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='issues')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='Medium')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Open')
    raised_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='raised_issues')
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_issues')
    raised_date = models.DateField(auto_now_add=True)
    resolution = models.TextField(blank=True)
    resolved_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title


class ChangeRequest(models.Model):
    STATUS_CHOICES = [('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Implemented', 'Implemented')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='change_requests')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    reason = models.TextField(blank=True)
    impact_on_budget = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    impact_on_schedule_days = models.IntegerField(default=0, help_text='Positive = delay, negative = acceleration')
    requested_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='requested_changes')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_changes')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    requested_date = models.DateField(auto_now_add=True)
    decision_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title
