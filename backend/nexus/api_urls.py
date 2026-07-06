from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.core.views import UserViewSet, CompanyViewSet, BranchViewSet, WarehouseViewSet, PrintTemplateViewSet, ModuleViewSet
from apps.accounts.views import AccountViewSet, JournalEntryViewSet, CostCenterViewSet, BudgetViewSet
from apps.inventory.views import (
    ItemViewSet, ItemGroupViewSet, StockEntryViewSet,
    ItemSerialNumberViewSet, ItemBatchViewSet,
    StockReconciliationViewSet, StockReconciliationItemViewSet,
)
from apps.buying.views import (
    SupplierViewSet, PurchaseOrderViewSet, PurchaseOrderItemViewSet,
    PurchaseTaxChargeViewSet, PurchasePaymentViewSet,
)
from apps.selling.views import (
    CustomerViewSet, SalesOrderViewSet, SalesOrderItemViewSet,
    SalesTaxChargeViewSet, SalesPaymentViewSet,
)
from apps.manufacturing.views import WorkOrderViewSet, BOMViewSet
from apps.hr.views import (
    EmployeeViewSet, DepartmentViewSet, TeamViewSet,
    LeaveRequestViewSet, PayrollViewSet,
)
from apps.crm.views import LeadViewSet, OpportunityViewSet
from apps.projects.views import ProjectViewSet, TaskViewSet
from apps.assets.views import AssetViewSet, AssetCategoryViewSet
from apps.workflow.views import WorkflowViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'branches', BranchViewSet)
router.register(r'warehouses', WarehouseViewSet)
router.register(r'print-templates', PrintTemplateViewSet)
router.register(r'modules', ModuleViewSet)
router.register(r'accounts', AccountViewSet)
router.register(r'journal-entries', JournalEntryViewSet)
router.register(r'cost-centers', CostCenterViewSet)
router.register(r'budgets', BudgetViewSet)
router.register(r'items', ItemViewSet)
router.register(r'item-groups', ItemGroupViewSet)
router.register(r'item-serial-numbers', ItemSerialNumberViewSet)
router.register(r'item-batches', ItemBatchViewSet)
router.register(r'stock-reconciliations', StockReconciliationViewSet)
router.register(r'stock-reconciliation-items', StockReconciliationItemViewSet)
router.register(r'stock-entries', StockEntryViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'purchase-orders', PurchaseOrderViewSet)
router.register(r'purchase-order-items', PurchaseOrderItemViewSet)
router.register(r'purchase-tax-charges', PurchaseTaxChargeViewSet)
router.register(r'purchase-payments', PurchasePaymentViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'sales-orders', SalesOrderViewSet)
router.register(r'sales-order-items', SalesOrderItemViewSet)
router.register(r'sales-tax-charges', SalesTaxChargeViewSet)
router.register(r'sales-payments', SalesPaymentViewSet)
router.register(r'work-orders', WorkOrderViewSet)
router.register(r'boms', BOMViewSet)
router.register(r'employees', EmployeeViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'leave-requests', LeaveRequestViewSet)
router.register(r'payrolls', PayrollViewSet)
router.register(r'leads', LeadViewSet)
router.register(r'opportunities', OpportunityViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'assets', AssetViewSet)
router.register(r'asset-categories', AssetCategoryViewSet)
router.register(r'workflows', WorkflowViewSet)

from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('auth-token/', obtain_auth_token, name='api_token_auth'),
]
