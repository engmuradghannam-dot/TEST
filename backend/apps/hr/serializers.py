from rest_framework import serializers
from .models import Employee, Department, Team, LeaveRequest, Payroll

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'

class LeaveRequestSerializer(serializers.ModelSerializer):
    duration_days = serializers.ReadOnlyField()
    remaining_balance = serializers.ReadOnlyField()
    class Meta:
        model = LeaveRequest
        fields = '__all__'

    def validate(self, data):
        start = data.get('start_date', getattr(self.instance, 'start_date', None))
        end = data.get('end_date', getattr(self.instance, 'end_date', None))
        employee = data.get('employee', getattr(self.instance, 'employee', None))

        if start and end and end < start:
            raise serializers.ValidationError("End date cannot be before start date.")

        if employee and start and end:
            overlapping = LeaveRequest.objects.filter(
                employee=employee, status__in=['Pending', 'Approved'],
                start_date__lte=end, end_date__gte=start,
            )
            if self.instance:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise serializers.ValidationError(
                    "This employee already has a pending or approved leave request overlapping these dates."
                )
        return data

class PayrollSerializer(serializers.ModelSerializer):
    overtime_amount = serializers.ReadOnlyField()
    gross_salary = serializers.ReadOnlyField()
    net_salary = serializers.ReadOnlyField()
    class Meta:
        model = Payroll
        fields = '__all__'
