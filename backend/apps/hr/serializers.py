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
    class Meta:
        model = LeaveRequest
        fields = '__all__'

class PayrollSerializer(serializers.ModelSerializer):
    overtime_amount = serializers.ReadOnlyField()
    gross_salary = serializers.ReadOnlyField()
    net_salary = serializers.ReadOnlyField()
    class Meta:
        model = Payroll
        fields = '__all__'
