from rest_framework import serializers
from apps.core.workflow import validate_transition
from .models import Project, Task, Milestone, Stakeholder, RiskRegister, IssueLog, ChangeRequest

CR_TRANSITIONS = {
    'Pending': {'Approved', 'Rejected'},
    'Approved': {'Implemented'},
    'Rejected': set(),
    'Implemented': set(),
}


class ProjectSerializer(serializers.ModelSerializer):
    progress_percent = serializers.ReadOnlyField()
    budget_variance = serializers.ReadOnlyField()
    class Meta:
        model = Project
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class MilestoneSerializer(serializers.ModelSerializer):
    is_overdue = serializers.ReadOnlyField()
    class Meta:
        model = Milestone
        fields = '__all__'


class StakeholderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stakeholder
        fields = '__all__'


class RiskRegisterSerializer(serializers.ModelSerializer):
    risk_score = serializers.ReadOnlyField()
    risk_level = serializers.ReadOnlyField()
    class Meta:
        model = RiskRegister
        fields = '__all__'


class IssueLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueLog
        fields = '__all__'


class ChangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeRequest
        fields = '__all__'

    def validate(self, data):
        new_status = data.get('status')
        if self.instance and new_status and new_status != self.instance.status:
            validate_transition(CR_TRANSITIONS, self.instance.status, new_status)
        return data
