from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import (
    IndustryCatalog, IndustryControl, AIAgentRegistry,
    CompanyIndustryProfile, ControlExecutionLog
)
from .serializers import (
    IndustryCatalogSerializer, IndustryControlSerializer,
    IndustryControlSummarySerializer, AIAgentRegistrySerializer,
    CompanyIndustryProfileSerializer, ControlExecutionLogSerializer
)
from apps.core.mixins import CompanyScopedMixin, AuditUserMixin


class IndustryCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    """Public read-only catalog of all supported industries"""
    queryset = IndustryCatalog.objects.filter(is_active=True).annotate(
        control_count=Count('controls', filter=Q(controls__is_active=True)),
        agent_count=Count('ai_agents', filter=Q(ai_agents__is_active=True))
    )
    serializer_class = IndustryCatalogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_premium', 'required_license_tier']
    search_fields = ['name', 'name_ar', 'description', 'industry_id']
    ordering_fields = ['name', 'sort_order', 'control_count']
    lookup_field = 'industry_id'

    @action(detail=True, methods=['get'])
    def controls(self, request, industry_id=None):
        """Get all controls for a specific industry"""
        industry = self.get_object()
        controls = industry.controls.filter(is_active=True)
        serializer = IndustryControlSerializer(controls, many=True)
        return Response({
            'industry': industry.name,
            'control_count': controls.count(),
            'controls': serializer.data
        })

    @action(detail=True, methods=['get'])
    def controls_summary(self, request, industry_id=None):
        """Get control summary for an industry"""
        industry = self.get_object()
        controls = industry.controls.filter(is_active=True)
        serializer = IndustryControlSummarySerializer(controls, many=True)
        return Response({
            'industry': industry.name,
            'total_controls': controls.count(),
            'required_controls': controls.filter(is_required=True).count(),
            'by_type': dict(controls.values('control_type').annotate(count=Count('id')).values_list('control_type', 'count')),
            'controls': serializer.data
        })

    @action(detail=True, methods=['get'])
    def ai_agents(self, request, industry_id=None):
        """Get AI agents for an industry"""
        industry = self.get_object()
        agents = industry.ai_agents.filter(is_active=True)
        serializer = AIAgentRegistrySerializer(agents, many=True)
        return Response({
            'industry': industry.name,
            'agent_count': agents.count(),
            'agents': serializer.data
        })

    @action(detail=True, methods=['post'])
    def deploy(self, request, industry_id=None):
        """Deploy industry template to current company"""
        industry = self.get_object()
        company = getattr(request.user, 'company', None)
        if not company:
            return Response({'error': 'User must belong to a company'}, status=status.HTTP_400_BAD_REQUEST)

        profile, created = CompanyIndustryProfile.objects.get_or_create(
            company=company, industry=industry,
            defaults={'is_active': True, 'is_primary': not company.industry_profiles.exists()}
        )
        if not created:
            profile.is_active = True
            profile.save()

        # Auto-activate all required controls
        required_controls = industry.controls.filter(is_required=True, is_active=True)
        profile.activated_controls.add(*required_controls)

        # Auto-activate all AI agents
        agents = industry.ai_agents.filter(is_active=True)
        profile.activated_agents.add(*agents)

        return Response({
            'success': True,
            'message': f'Industry {industry.name} deployed successfully',
            'profile_id': profile.id,
            'activated_controls': required_controls.count(),
            'activated_agents': agents.count()
        })


class IndustryControlViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of industry controls"""
    queryset = IndustryControl.objects.filter(is_active=True).select_related('industry')
    serializer_class = IndustryControlSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['industry', 'control_type', 'is_required', 'severity', 'compliance_framework']
    search_fields = ['control_id', 'control_name', 'description', 'module']
    ordering_fields = ['control_id', 'control_name', 'severity', 'sort_order']
    lookup_field = 'control_id'

    @action(detail=False, methods=['get'])
    def by_industry(self, request):
        """Group controls by industry"""
        industry_id = request.query_params.get('industry_id')
        if industry_id:
            controls = self.queryset.filter(industry__industry_id=industry_id)
        else:
            controls = self.queryset
        return Response({
            'count': controls.count(),
            'results': IndustryControlSerializer(controls, many=True).data
        })

    @action(detail=True, methods=['post'])
    def execute(self, request, control_id=None):
        """Execute a control check"""
        control = self.get_object()
        company = getattr(request.user, 'company', None)
        if not company:
            return Response({'error': 'No company context'}, status=400)

        log = ControlExecutionLog.objects.create(
            company=company,
            control=control,
            executed_by=request.user,
            status='running',
            result_data=request.data.get('params', {})
        )
        # In real implementation, this would trigger async task
        log.status = 'passed'
        log.completed_at = __import__('django.utils.timezone').utils.timezone.now()
        log.save()

        return Response({
            'success': True,
            'log_id': log.id,
            'status': log.status
        })


class AIAgentRegistryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only AI agent registry"""
    queryset = AIAgentRegistry.objects.filter(is_active=True).select_related('industry')
    serializer_class = AIAgentRegistrySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['industry', 'agent_type']
    search_fields = ['name', 'description', 'agent_id']
    lookup_field = 'agent_id'

    @action(detail=True, methods=['post'])
    def invoke(self, request, agent_id=None):
        """Invoke an AI agent"""
        agent = self.get_object()
        agent.usage_count += 1
        from django.utils import timezone
        agent.last_used = timezone.now()
        agent.save()

        return Response({
            'success': True,
            'agent': AIAgentRegistrySerializer(agent).data,
            'result': {
                'message': f'Agent {agent.name} invoked successfully',
                'timestamp': str(timezone.now())
            }
        })


class CompanyIndustryProfileViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """Manage company industry profiles"""
    queryset = CompanyIndustryProfile.objects.all().select_related('industry', 'company')
    serializer_class = CompanyIndustryProfileSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['industry', 'is_primary', 'is_active', 'maturity_level']
    ordering_fields = ['created_at', 'compliance_score']
    company_field = 'company'

    @action(detail=True, methods=['post'])
    def activate_control(self, request, pk=None):
        """Activate a specific control for this profile"""
        profile = self.get_object()
        control_id = request.data.get('control_id')
        if not control_id:
            return Response({'error': 'control_id required'}, status=400)
        try:
            control = IndustryControl.objects.get(control_id=control_id, industry=profile.industry)
            profile.activated_controls.add(control)
            return Response({'success': True, 'message': f'Control {control_id} activated'})
        except IndustryControl.DoesNotExist:
            return Response({'error': 'Control not found'}, status=404)

    @action(detail=True, methods=['post'])
    def deactivate_control(self, request, pk=None):
        profile = self.get_object()
        control_id = request.data.get('control_id')
        if not control_id:
            return Response({'error': 'control_id required'}, status=400)
        try:
            control = IndustryControl.objects.get(control_id=control_id, industry=profile.industry)
            profile.activated_controls.remove(control)
            return Response({'success': True, 'message': f'Control {control_id} deactivated'})
        except IndustryControl.DoesNotExist:
            return Response({'error': 'Control not found'}, status=404)

    @action(detail=True, methods=['post'])
    def run_compliance_check(self, request, pk=None):
        """Run compliance check for all activated controls"""
        profile = self.get_object()
        controls = profile.activated_controls.filter(is_required=True)
        passed = 0
        failed = 0
        for control in controls:
            log = ControlExecutionLog.objects.create(
                company=profile.company,
                control=control,
                executed_by=request.user,
                status='passed'  # Simplified - real would run actual checks
            )
            passed += 1

        total = controls.count()
        score = (passed / total * 100) if total > 0 else 0
        profile.compliance_score = score
        profile.save()

        return Response({
            'success': True,
            'total_controls': total,
            'passed': passed,
            'failed': failed,
            'compliance_score': score
        })


class ControlExecutionLogViewSet(CompanyScopedMixin, viewsets.ReadOnlyModelViewSet):
    """View control execution history"""
    queryset = ControlExecutionLog.objects.all().select_related('control', 'executed_by')
    serializer_class = ControlExecutionLogSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'control', 'risk_level']
    ordering_fields = ['executed_at', 'completed_at']
    company_field = 'company'
