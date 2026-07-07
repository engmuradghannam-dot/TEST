import pytest
from datetime import date, timedelta


@pytest.mark.django_db
class TestLeaveRequestLogic:
    def test_end_date_before_start_date_rejected(self, authenticated_client, employee):
        resp = authenticated_client.post('/api/v1/hr/leave-requests/', {
            'employee': employee.id, 'leave_type': 'Annual',
            'start_date': '2026-08-10', 'end_date': '2026-08-05',
        })
        assert resp.status_code == 400

    def test_overlapping_leave_rejected(self, authenticated_client, employee):
        resp1 = authenticated_client.post('/api/v1/hr/leave-requests/', {
            'employee': employee.id, 'leave_type': 'Annual',
            'start_date': '2026-08-01', 'end_date': '2026-08-05',
        })
        assert resp1.status_code == 201

        resp2 = authenticated_client.post('/api/v1/hr/leave-requests/', {
            'employee': employee.id, 'leave_type': 'Annual',
            'start_date': '2026-08-03', 'end_date': '2026-08-07',
        })
        assert resp2.status_code == 400

    def test_non_overlapping_leave_allowed(self, authenticated_client, employee):
        authenticated_client.post('/api/v1/hr/leave-requests/', {
            'employee': employee.id, 'leave_type': 'Annual',
            'start_date': '2026-08-01', 'end_date': '2026-08-05',
        })
        resp = authenticated_client.post('/api/v1/hr/leave-requests/', {
            'employee': employee.id, 'leave_type': 'Sick',
            'start_date': '2026-09-01', 'end_date': '2026-09-02',
        })
        assert resp.status_code == 201

    def test_cannot_skip_pending_to_paid_like_invalid_status(self, authenticated_client, employee):
        leave = authenticated_client.post('/api/v1/hr/leave-requests/', {
            'employee': employee.id, 'leave_type': 'Annual',
            'start_date': '2026-08-01', 'end_date': '2026-08-05',
        }).data
        resp = authenticated_client.patch(f'/api/v1/hr/leave-requests/{leave["id"]}/', {'status': 'Rejected'})
        # Pending -> Rejected is allowed
        assert resp.status_code == 200
        # Rejected -> Approved should NOT be allowed (final state)
        resp2 = authenticated_client.patch(f'/api/v1/hr/leave-requests/{leave["id"]}/', {'status': 'Approved'})
        assert resp2.status_code == 400


@pytest.mark.django_db
class TestPayrollLogic:
    def test_net_salary_computed_correctly(self, authenticated_client, employee):
        resp = authenticated_client.post('/api/v1/hr/payrolls/', {
            'employee': employee.id, 'pay_period_start': '2026-07-01', 'pay_period_end': '2026-07-31',
            'basic_salary': 8000, 'housing_allowance': 2000, 'overtime_hours': 10,
            'overtime_rate': 50, 'deductions': 300, 'tax': 0,
        })
        assert resp.status_code == 201
        assert float(resp.data['gross_salary']) == 10500.0  # 8000+2000+500 overtime
        assert float(resp.data['net_salary']) == 10200.0  # -300 deductions

    def test_overlapping_payroll_period_rejected(self, authenticated_client, employee):
        authenticated_client.post('/api/v1/hr/payrolls/', {
            'employee': employee.id, 'pay_period_start': '2026-07-01', 'pay_period_end': '2026-07-31',
            'basic_salary': 8000,
        })
        resp = authenticated_client.post('/api/v1/hr/payrolls/', {
            'employee': employee.id, 'pay_period_start': '2026-07-15', 'pay_period_end': '2026-08-15',
            'basic_salary': 8000,
        })
        assert resp.status_code == 400
