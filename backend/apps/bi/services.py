"""
BI Services - OLAP Engine, Financial Analytics
"""
import logging
from typing import Dict, List, Any
from django.db.models import Sum, Avg, Count, F, Q
from django.utils import timezone
from decimal import Decimal
from .models import OLAPCube, BIReport, FinancialAnalytics

logger = logging.getLogger(__name__)


class OLAPQueryEngine:
    """OLAP Query Engine for multi-dimensional analysis"""

    def __init__(self, cube: OLAPCube):
        self.cube = cube

    def query(self, dimensions: List[str], measures: List[str], 
              filters: Dict = None, drilldown: Dict = None) -> List[Dict]:
        """
        Execute OLAP query

        Args:
            dimensions: List of dimension fields to group by
            measures: List of measures to aggregate
            filters: Dict of filter conditions
            drilldown: Dict for drill-down analysis
        """
        # This is a simplified implementation
        # In production, this would use a real OLAP engine like Apache Druid or ClickHouse

        results = []

        # Parse source model
        model_path = self.cube.source_model
        try:
            app_label, model_name = model_path.split('.')
            from django.apps import apps
            Model = apps.get_model(app_label, model_name)
        except:
            logger.error(f"Could not load model: {model_path}")
            return results

        # Build query
        queryset = Model.objects.all()

        # Apply filters
        if filters:
            for field, value in filters.items():
                queryset = queryset.filter(**{field: value})

        # Group by dimensions
        if dimensions:
            queryset = queryset.values(*dimensions)

        # Aggregate measures
        if measures:
            annotations = {}
            for measure in measures:
                annotations[f'{measure}_total'] = Sum(measure)
                annotations[f'{measure}_avg'] = Avg(measure)
                annotations[f'{measure}_count'] = Count(measure)
            queryset = queryset.annotate(**annotations)

        # Convert to list
        results = list(queryset[:1000])  # Limit for safety

        return results

    def pivot(self, rows: str, columns: str, values: str) -> Dict:
        """Create pivot table"""
        data = self.query(
            dimensions=[rows, columns],
            measures=[values]
        )

        # Transform to pivot format
        pivot_data = {}
        for row in data:
            row_key = row.get(rows, 'Unknown')
            col_key = row.get(columns, 'Unknown')
            val = row.get(f'{values}_total', 0)

            if row_key not in pivot_data:
                pivot_data[row_key] = {}
            pivot_data[row_key][col_key] = val

        return {
            'rows': list(pivot_data.keys()),
            'columns': list(set(c for r in pivot_data.values() for c in r.keys())),
            'data': pivot_data
        }

    def drill_down(self, dimension: str, value: Any, sub_dimension: str) -> List[Dict]:
        """Drill down into a dimension"""
        return self.query(
            dimensions=[sub_dimension],
            measures=[m['field'] for m in self.cube.measures],
            filters={dimension: value}
        )


class FinancialAnalyticsEngine:
    """Financial Analytics & KPI Engine"""

    def calculate_mrr(self, tenant) -> Decimal:
        """Calculate Monthly Recurring Revenue"""
        from apps.billing.models import Subscription

        active_subs = Subscription.objects.filter(
            tenant=tenant,
            status='active'
        )

        mrr = sum(sub.plan.price for sub in active_subs if sub.plan)
        return Decimal(str(mrr))

    def calculate_arr(self, tenant) -> Decimal:
        """Calculate Annual Recurring Revenue"""
        return self.calculate_mrr(tenant) * 12

    def calculate_churn_rate(self, tenant, period_days: int = 30) -> float:
        """Calculate churn rate"""
        from apps.billing.models import Subscription
        from apps.tenants.models import Tenant

        start_date = timezone.now() - timezone.timedelta(days=period_days)

        starting_subs = Subscription.objects.filter(
            tenant=tenant,
            created_at__lt=start_date,
            status='active'
        ).count()

        churned = Subscription.objects.filter(
            tenant=tenant,
            status='cancelled',
            cancelled_at__gte=start_date
        ).count()

        if starting_subs == 0:
            return 0.0

        return (churned / starting_subs) * 100

    def calculate_ltv(self, tenant) -> Decimal:
        """Calculate Customer Lifetime Value"""
        from apps.billing.models import Subscription

        avg_revenue = Subscription.objects.filter(
            tenant=tenant,
            status='active'
        ).aggregate(avg=Avg('plan__price'))['avg'] or 0

        churn_rate = self.calculate_churn_rate(tenant) / 100
        if churn_rate == 0:
            churn_rate = 0.01  # Prevent division by zero

        ltv = Decimal(str(avg_revenue)) / Decimal(str(churn_rate))
        return ltv

    def calculate_cac(self, tenant, period_days: int = 30) -> Decimal:
        """Calculate Customer Acquisition Cost"""
        # Simplified calculation
        # In reality, this would track marketing spend vs new customers
        return Decimal('100.00')  # Placeholder

    def generate_financial_report(self, tenant, period_start, period_end) -> Dict:
        """Generate comprehensive financial report"""

        mrr = self.calculate_mrr(tenant)
        arr = self.calculate_arr(tenant)
        churn = self.calculate_churn_rate(tenant)
        ltv = self.calculate_ltv(tenant)
        cac = self.calculate_cac(tenant)

        ltv_cac = float(ltv) / float(cac) if cac > 0 else 0

        # Create analytics record
        analytics = FinancialAnalytics.objects.create(
            period_start=period_start,
            period_end=period_end,
            period_type='monthly',
            mrr=mrr,
            arr=arr,
            churn_rate=churn,
            ltv=ltv,
            cac=cac,
            ltv_cac_ratio=ltv_cac
        )

        return {
            'mrr': float(mrr),
            'arr': float(arr),
            'churn_rate': churn,
            'ltv': float(ltv),
            'cac': float(cac),
            'ltv_cac_ratio': ltv_cac,
            'period': f"{period_start} to {period_end}"
        }

    def get_kpi_dashboard(self, tenant) -> Dict:
        """Get KPI dashboard data"""
        return {
            'mrr': float(self.calculate_mrr(tenant)),
            'arr': float(self.calculate_arr(tenant)),
            'churn_rate': self.calculate_churn_rate(tenant),
            'ltv': float(self.calculate_ltv(tenant)),
            'cac': float(self.calculate_cac(tenant)),
            'ltv_cac_ratio': float(self.calculate_ltv(tenant)) / float(self.calculate_cac(tenant)) if self.calculate_cac(tenant) > 0 else 0,
            'active_customers': self._get_active_customer_count(tenant),
            'new_customers_this_month': self._get_new_customers(tenant, 30),
        }

    def _get_active_customer_count(self, tenant) -> int:
        from apps.billing.models import Subscription
        return Subscription.objects.filter(tenant=tenant, status='active').count()

    def _get_new_customers(self, tenant, days: int) -> int:
        from apps.billing.models import Subscription
        from django.utils import timezone
        return Subscription.objects.filter(
            tenant=tenant,
            created_at__gte=timezone.now() - timezone.timedelta(days=days)
        ).count()
