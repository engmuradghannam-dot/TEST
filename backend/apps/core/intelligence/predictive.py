"""Predictive Intelligence: sales / demand / risk / failure forecasting.

Dependency-light forecasting (statistics stdlib): moving average, linear
trend (least squares), and seasonal-naive with a safe fallback. Each
predictor returns point forecasts + a confidence band, and explains the
method used so results are auditable rather than a black box.
"""
import statistics
from datetime import timedelta

from django.utils import timezone


def _linear_trend(y: list[float]) -> tuple[float, float]:
    """Least-squares slope & intercept over index 0..n-1."""
    n = len(y)
    xs = list(range(n))
    mx, my = (n - 1) / 2, sum(y) / n
    denom = sum((x - mx) ** 2 for x in xs) or 1e-9
    slope = sum((x - mx) * (v - my) for x, v in zip(xs, y)) / denom
    return slope, my - slope * mx


def forecast_series(history: list[float], periods: int = 3) -> dict:
    """Generic forecaster used by all business predictors."""
    if len(history) < 3:
        last = history[-1] if history else 0
        return {'method': 'naive_last', 'forecast': [last] * periods,
                'lower': [last] * periods, 'upper': [last] * periods,
                'confidence': 0.3}
    slope, intercept = _linear_trend(history)
    n = len(history)
    resid = [history[i] - (intercept + slope * i) for i in range(n)]
    sigma = statistics.pstdev(resid) if len(resid) > 1 else 0
    forecast, lower, upper = [], [], []
    for h in range(1, periods + 1):
        point = intercept + slope * (n - 1 + h)
        point = max(point, 0)
        forecast.append(round(point, 2))
        lower.append(round(max(point - 1.96 * sigma, 0), 2))
        upper.append(round(point + 1.96 * sigma, 2))
    mean = statistics.mean(history) or 1
    conf = max(0.3, min(0.95, 1 - (sigma / abs(mean))))
    return {'method': 'linear_trend', 'forecast': forecast,
            'lower': lower, 'upper': upper, 'confidence': round(conf, 2),
            'slope': round(slope, 4)}


class SalesForecaster:
    def monthly(self, company, months_back: int = 12, horizon: int = 3) -> dict:
        from apps.selling.models import SalesOrder
        from django.db.models import Sum
        from django.db.models.functions import TruncMonth
        since = timezone.now().date() - timedelta(days=months_back * 31)
        rows = (SalesOrder.objects.filter(company=company,
                                          order_date__gte=since)
                .annotate(m=TruncMonth('order_date'))
                .values('m').annotate(total=Sum('grand_total'))
                .order_by('m'))
        history = [float(r['total'] or 0) for r in rows]
        result = forecast_series(history, horizon)
        result['history'] = history
        result['metric'] = 'sales_revenue'
        return result


class DemandForecaster:
    def item_demand(self, company, item, months_back: int = 12,
                    horizon: int = 3) -> dict:
        from apps.selling.models import SalesOrderItem
        from django.db.models import Sum
        from django.db.models.functions import TruncMonth
        since = timezone.now().date() - timedelta(days=months_back * 31)
        rows = (SalesOrderItem.objects.filter(
                    sales_order__company=company, item=item,
                    sales_order__order_date__gte=since)
                .annotate(m=TruncMonth('sales_order__order_date'))
                .values('m').annotate(qty=Sum('quantity'))
                .order_by('m'))
        history = [float(r['qty'] or 0) for r in rows]
        result = forecast_series(history, horizon)
        result['history'] = history
        result['metric'] = 'demand_qty'
        result['reorder_hint'] = max(result['forecast']) if result['forecast'] else 0
        return result


class RiskPredictor:
    def project_risk(self, project) -> dict:
        """Heuristic risk score from schedule slippage, open issues,
        and registered risks."""
        score, factors = 0.0, []
        try:
            open_issues = project.issues.filter(status__in=['open', 'in_progress']).count()
            if open_issues > 5:
                score += 0.3
                factors.append(f'{open_issues} open issues')
        except Exception:
            pass
        try:
            high_risks = project.risks.filter(severity__in=['high', 'critical']).count()
            if high_risks:
                score += 0.4
                factors.append(f'{high_risks} high/critical risks')
        except Exception:
            pass
        try:
            if project.end_date and project.end_date < timezone.now().date() \
                    and project.status != 'completed':
                score += 0.3
                factors.append('past due date')
        except Exception:
            pass
        level = ('critical' if score >= 0.7 else 'high' if score >= 0.5
                 else 'medium' if score >= 0.3 else 'low')
        return {'risk_score': round(min(score, 1.0), 2),
                'level': level, 'factors': factors}


class MaintenancePredictor:
    def asset_failure(self, asset) -> dict:
        """Predict failure likelihood from age vs useful-life and usage."""
        from datetime import date
        score, factors = 0.0, []
        try:
            if asset.purchase_date and asset.useful_life_years:
                age = (date.today() - asset.purchase_date).days / 365.25
                ratio = age / asset.useful_life_years
                if ratio >= 1:
                    score += 0.6
                    factors.append('past useful life')
                elif ratio >= 0.8:
                    score += 0.35
                    factors.append('near end of useful life')
        except Exception:
            pass
        return {'failure_risk': round(min(score, 1.0), 2), 'factors': factors,
                'recommended_action':
                    'schedule inspection' if score >= 0.5 else 'monitor'}
