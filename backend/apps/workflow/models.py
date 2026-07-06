from django.db import models
from django.contrib.contenttypes.models import ContentType

class Workflow(models.Model):
    name = models.CharField(max_length=255)
    document_type = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class WorkflowState(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='states')
    state_name = models.CharField(max_length=100)
    is_initial = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)

    def __str__(self):
        return self.state_name

class WorkflowTransition(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='transitions')
    from_state = models.ForeignKey(WorkflowState, on_delete=models.CASCADE, related_name='transitions_from')
    to_state = models.ForeignKey(WorkflowState, on_delete=models.CASCADE, related_name='transitions_to')
    action = models.CharField(max_length=100)
    allowed_roles = models.CharField(max_length=255, blank=True)


class ApprovalStep(models.Model):
    """A step in an approval chain within a workflow."""
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='approval_steps')
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0, help_text='Execution order in the chain')
    approver = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='approval_steps', null=True, blank=True)
    approver_role = models.CharField(max_length=50, blank=True, help_text='Role-based approver if no specific user')
    is_required = models.BooleanField(default=True)
    auto_approve_if = models.TextField(blank=True, help_text='Conditions for auto-approval (JSON logic)')
    timeout_hours = models.PositiveIntegerField(default=48, help_text='Hours before escalation')

    class Meta:
        ordering = ['order']
        unique_together = ['workflow', 'order']

    def __str__(self):
        return f"{self.workflow.name} - Step {self.order}: {self.name}"


class ApprovalRecord(models.Model):
    """Record of an approval action on a document."""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Escalated', 'Escalated'),
        ('Skipped', 'Skipped'),
    ]

    step = models.ForeignKey(ApprovalStep, on_delete=models.CASCADE, related_name='records')
    document_type = models.CharField(max_length=50)  # e.g., 'PurchaseOrder', 'SalesOrder'
    document_id = models.PositiveIntegerField()
    requested_by = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='approval_requests')
    approver = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='approval_actions', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    comments = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.document_type} #{self.document_id} - {self.status}"

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.status != 'Pending':
            return False
        deadline = self.requested_at + timezone.timedelta(hours=self.step.timeout_hours)
        return timezone.now() > deadline
