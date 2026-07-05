from rest_framework import viewsets
from .models import Lead, Opportunity
from .serializers import LeadSerializer, OpportunitySerializer
from apps.core.mixins import CompanyScopedMixin


class LeadViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    company_field = 'company'


class OpportunityViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer
    company_field = 'company'
