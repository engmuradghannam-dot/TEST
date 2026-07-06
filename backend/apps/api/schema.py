"""
GraphQL API for Nexus SaaS
Public API with developer SDK support
"""
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


# ── Types ─────────────────────────────────

class TenantType(DjangoObjectType):
    class Meta:
        model = 'apps.tenants.Tenant'
        fields = ('id', 'name', 'slug', 'status', 'created_at')
        filter_fields = {
            'name': ['exact', 'icontains'],
            'status': ['exact', 'in'],
            'created_at': ['date', 'date__gte', 'date__lte'],
        }
        interfaces = (graphene.relay.Node,)


class UserType(DjangoObjectType):
    full_name = graphene.String()
    initials = graphene.String()

    class Meta:
        model = 'apps.tenants.TenantUser'
        fields = ('id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined')
        filter_fields = {
            'email': ['exact', 'icontains'],
            'is_active': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

    def resolve_full_name(self, info):
        return f"{self.first_name} {self.last_name}".strip()

    def resolve_initials(self, info):
        return f"{self.first_name[0]}{self.last_name[0]}".upper() if self.first_name and self.last_name else "U"


class ProductType(DjangoObjectType):
    stock_status = graphene.String()

    class Meta:
        model = 'apps.inventory.InventoryItem'
        fields = '__all__'
        filter_fields = {
            'name': ['exact', 'icontains'],
            'sku': ['exact'],
            'quantity': ['gte', 'lte'],
        }
        interfaces = (graphene.relay.Node,)

    def resolve_stock_status(self, info):
        if self.quantity == 0:
            return 'OUT_OF_STOCK'
        elif self.quantity <= self.reorder_level:
            return 'LOW_STOCK'
        return 'IN_STOCK'


class InvoiceType(DjangoObjectType):
    class Meta:
        model = 'apps.billing.Invoice'
        fields = '__all__'
        filter_fields = {
            'status': ['exact', 'in'],
            'total': ['gte', 'lte'],
            'invoice_date': ['date', 'date__gte', 'date__lte'],
        }
        interfaces = (graphene.relay.Node,)


class WorkflowType(DjangoObjectType):
    class Meta:
        model = 'apps.workflow.WorkflowDefinition'
        fields = '__all__'
        interfaces = (graphene.relay.Node,)


class WorkflowInstanceType(DjangoObjectType):
    progress = graphene.Float()

    class Meta:
        model = 'apps.workflow.WorkflowInstance'
        fields = '__all__'
        interfaces = (graphene.relay.Node,)

    def resolve_progress(self, info):
        total = len(self.definition.nodes) if self.definition else 1
        completed = len(self.completed_nodes) if self.completed_nodes else 0
        return (completed / total) * 100 if total > 0 else 0


# ── Queries ───────────────────────────────

class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()

    # Tenant queries
    tenants = DjangoFilterConnectionField(TenantType)
    tenant = graphene.relay.Node.Field(TenantType)

    # User queries
    users = DjangoFilterConnectionField(UserType)
    me = graphene.Field(UserType)

    # Product queries
    products = DjangoFilterConnectionField(ProductType)
    product = graphene.relay.Node.Field(ProductType)
    low_stock_products = DjangoFilterConnectionField(ProductType)

    # Invoice queries
    invoices = DjangoFilterConnectionField(InvoiceType)
    invoice = graphene.relay.Node.Field(InvoiceType)

    # Workflow queries
    workflows = DjangoFilterConnectionField(WorkflowType)
    workflow_instances = DjangoFilterConnectionField(WorkflowInstanceType)

    # Analytics
    dashboard_stats = graphene.Field(graphene.JSONString)

    def resolve_me(self, info):
        if info.context.user.is_authenticated:
            return info.context.user
        return None

    def resolve_low_stock_products(self, info, **kwargs):
        from apps.inventory.models import InventoryItem
        return InventoryItem.objects.filter(
            Q(quantity__lte=models.F('reorder_level')) | Q(quantity=0)
        )

    def resolve_dashboard_stats(self, info):
        from apps.bi.services import FinancialAnalyticsEngine
        if info.context.user.is_authenticated:
            tenant = getattr(info.context, 'tenant', None)
            if tenant:
                engine = FinancialAnalyticsEngine()
                return engine.get_kpi_dashboard(tenant)
        return {}


# ── Mutations ─────────────────────────────

class CreateTenant(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        slug = graphene.String(required=True)
        owner_email = graphene.String(required=True)
        owner_password = graphene.String(required=True)

    tenant = graphene.Field(TenantType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, name, slug, owner_email, owner_password):
        from apps.tenants.models import Tenant, TenantUser, TenantMembership

        try:
            tenant = Tenant.objects.create(
                name=name,
                slug=slug,
                schema_name=slug,
                status=Tenant.Status.TRIAL
            )

            owner = TenantUser.objects.create_user(
                email=owner_email,
                password=owner_password,
                first_name='Admin',
                last_name='User'
            )

            TenantMembership.objects.create(
                user=owner,
                tenant=tenant,
                role=TenantMembership.Role.OWNER
            )

            return CreateTenant(tenant=tenant, success=True, errors=[])
        except Exception as e:
            return CreateTenant(tenant=None, success=False, errors=[str(e)])


class UpdateProductStock(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        quantity = graphene.Int(required=True)
        reason = graphene.String()

    product = graphene.Field(ProductType)
    success = graphene.Boolean()

    def mutate(self, info, id, quantity, reason=None):
        from apps.inventory.models import InventoryItem

        try:
            product = InventoryItem.objects.get(pk=id)
            old_qty = product.quantity
            product.quantity = quantity
            product.save()

            # Log movement
            # InventoryMovement.objects.create(...)

            return UpdateProductStock(product=product, success=True)
        except InventoryItem.DoesNotExist:
            return UpdateProductStock(product=None, success=False)


class StartWorkflow(graphene.Mutation):
    class Arguments:
        workflow_id = graphene.ID(required=True)
        variables = graphene.JSONString()

    instance = graphene.Field(WorkflowInstanceType)
    success = graphene.Boolean()

    def mutate(self, info, workflow_id, variables=None):
        from apps.workflow.models import WorkflowDefinition
        from apps.workflow.bpmn_engine import workflow_engine

        try:
            definition = WorkflowDefinition.objects.get(pk=workflow_id)
            instance = workflow_engine.start_instance(
                definition=definition,
                variables=variables or {},
                user=info.context.user
            )
            return StartWorkflow(instance=instance, success=True)
        except Exception as e:
            return StartWorkflow(instance=None, success=False)


class Mutation(graphene.ObjectType):
    create_tenant = CreateTenant.Field()
    update_product_stock = UpdateProductStock.Field()
    start_workflow = StartWorkflow.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
