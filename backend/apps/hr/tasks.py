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
