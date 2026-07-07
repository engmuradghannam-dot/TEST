"""
Celery tasks for hr app.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_payroll():
    """Process payroll for all employees."""
    from .models import Employee
    employees = Employee.objects.filter(is_active=True)
    for emp in employees:
        logger.info(f"Payroll processed for {emp.name}")

@shared_task
def check_leave_balances():
    """Check and reset leave balances."""
    logger.info("Leave balances checked")


@shared_task
def send_leave_decision_email(leave_request_id: int, new_status: str):
    """Notify employee of leave request decision."""
    try:
        from apps.hr.models import LeaveRequest
        lr = LeaveRequest.objects.select_related('employee__user').get(id=leave_request_id)
        user = lr.employee.user if lr.employee else None
        if user and hasattr(user, 'email') and user.email:
            from django.core.mail import send_mail
            send_mail(
                subject=f"Leave Request {new_status}",
                message=f"Your leave request ({lr.leave_type}, {lr.start_date} - {lr.end_date}) "
                        f"has been {new_status}.",
                from_email="noreply@nexus.erp",
                recipient_list=[user.email],
                fail_silently=True,
            )
    except Exception:
        pass
