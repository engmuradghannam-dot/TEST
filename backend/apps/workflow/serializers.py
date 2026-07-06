from rest_framework import serializers
from .models import Workflow, WorkflowState, WorkflowTransition, ApprovalStep, ApprovalRecord

class WorkflowStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowState
        fields = '__all__'

class WorkflowTransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTransition
        fields = '__all__'

class WorkflowSerializer(serializers.ModelSerializer):
    states = WorkflowStateSerializer(many=True, read_only=True)
    transitions = WorkflowTransitionSerializer(many=True, read_only=True)
    class Meta:
        model = Workflow
        fields = '__all__'


class ApprovalStepSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source='approver.email', read_only=True, default=None)

    class Meta:
        model = ApprovalStep
        fields = '__all__'


class ApprovalRecordSerializer(serializers.ModelSerializer):
    step_name = serializers.CharField(source='step.name', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.email', read_only=True)
    approver_name = serializers.CharField(source='approver.email', read_only=True, default=None)
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = ApprovalRecord
        fields = '__all__'
