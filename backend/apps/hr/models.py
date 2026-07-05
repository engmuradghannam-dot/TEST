from django.db import models
from apps.core.models import Company, Branch, User

class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)
    parent_department = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class Employee(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    STATUS_CHOICES = [('Active', 'Active'), ('Inactive', 'Inactive'), ('On Leave', 'On Leave')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='employee_profile',
        help_text='Login account for this employee, used to scope "my tasks".'
    )
    employee_id = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    national_id = models.CharField(max_length=100, blank=True)
    passport = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    designation = models.CharField(max_length=255, blank=True)
    salary = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    bank_account = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    iban = models.CharField(max_length=50, blank=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"


class Team(models.Model):
    """A working team within a company. Tasks assigned to a team are
    visible to every member of that team."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=255)
    lead = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='led_teams'
    )
    members = models.ManyToManyField(Employee, related_name='teams', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('Annual', 'Annual'), ('Sick', 'Sick'), ('Unpaid', 'Unpaid'),
        ('Maternity', 'Maternity'), ('Paternity', 'Paternity'), ('Emergency', 'Emergency'),
    ]
    STATUS_CHOICES = [('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Cancelled', 'Cancelled')]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approval_date = models.DateField(null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    def save(self, *args, **kwargs):
        if not self.year and self.start_date:
            self.year = self.start_date.year
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date} to {self.end_date})"


class Payroll(models.Model):
    PAYMENT_METHODS = [('Bank Transfer', 'Bank Transfer'), ('Cash', 'Cash'), ('Cheque', 'Cheque')]
    STATUS_CHOICES = [('Draft', 'Draft'), ('Approved', 'Approved'), ('Paid', 'Paid'), ('Cancelled', 'Cancelled')]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    basic_salary = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    housing_allowance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    bonuses = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='Bank Transfer')
    bank_account = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    currency = models.CharField(max_length=10, default='SAR')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def overtime_amount(self):
        return (self.overtime_hours or 0) * (self.overtime_rate or 0)

    @property
    def gross_salary(self):
        return (self.basic_salary + self.housing_allowance + self.transport_allowance
                + self.overtime_amount + self.bonuses)

    @property
    def net_salary(self):
        return self.gross_salary - self.deductions - self.tax

    def __str__(self):
        return f"{self.employee} - {self.pay_period_start} to {self.pay_period_end}"
