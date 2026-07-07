"""Health check endpoint for load balancers and monitoring."""
from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.utils import timezone


class HealthView(View):
    def get(self, request):
        checks = {}
        status = 200

        # Database
        try:
            connection.ensure_connection()
            with connection.cursor() as c:
                c.execute("SELECT 1")
            checks['database'] = 'ok'
        except Exception as e:
            checks['database'] = f'error: {e}'
            status = 503

        # Cache/Redis
        try:
            from django.core.cache import cache
            cache.set('health_check', '1', 5)
            assert cache.get('health_check') == '1'
            checks['cache'] = 'ok'
        except Exception as e:
            checks['cache'] = f'warning: {e}'

        # Celery
        try:
            from nexus.celery import app as celery_app
            i = celery_app.control.inspect(timeout=1)
            checks['celery'] = 'ok' if i.ping() else 'no workers'
        except Exception:
            checks['celery'] = 'unknown'

        return JsonResponse({
            'status': 'healthy' if status == 200 else 'degraded',
            'timestamp': timezone.now().isoformat(),
            'version': '2.0.0',
            'checks': checks,
        }, status=status)


class ReadyView(View):
    """Kubernetes readiness probe — fails until migrations are done."""
    def get(self, request):
        try:
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            if plan:
                return JsonResponse({'ready': False, 'pending': len(plan)}, status=503)
            return JsonResponse({'ready': True})
        except Exception as e:
            return JsonResponse({'ready': False, 'error': str(e)}, status=503)
