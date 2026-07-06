#!/bin/bash
set -e

# Nexus SaaS - Entrypoint Script
# Supports: dev, staging, production

ENV=${ENVIRONMENT:-development}
echo "Starting Nexus SaaS in $ENV mode..."

# Wait for database
wait_for_db() {
    echo "Waiting for PostgreSQL..."
    while ! pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-nexus}" > /dev/null 2>&1; do
        sleep 1
    done
    echo "PostgreSQL is ready!"
}

# Wait for Redis
wait_for_redis() {
    echo "Waiting for Redis..."
    while ! redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; do
        sleep 1
    done
    echo "Redis is ready!"
}

# Run migrations
run_migrations() {
    echo "Running migrations..."
    python manage.py migrate --run-syncdb
    python manage.py migrate_schemas --shared
    echo "Migrations complete!"
}

# Collect static files
collect_static() {
    if [ "$ENV" != "development" ]; then
        echo "Collecting static files..."
        python manage.py collectstatic --noinput
        echo "Static files collected!"
    fi
}

# Create superuser if not exists
create_superuser() {
    if [ "$CREATE_SUPERUSER" = "true" ]; then
        echo "Creating superuser..."
        python manage.py shell -c "
from apps.tenants.models import TenantUser
if not TenantUser.objects.filter(email='${SUPERUSER_EMAIL:-admin@nexus.com}').exists():
    TenantUser.objects.create_superuser(
        email='${SUPERUSER_EMAIL:-admin@nexus.com}',
        password='${SUPERUSER_PASSWORD:-admin123}',
        first_name='Admin',
        last_name='User'
    )
    print('Superuser created!')
else:
    print('Superuser already exists.')
"
    fi
}

# Main execution
case "$1" in
    web)
        wait_for_db
        run_migrations
        collect_static
        create_superuser

        if [ "$ENV" = "development" ]; then
            echo "Starting Django development server..."
            exec python manage.py runserver 0.0.0.0:8000
        else
            echo "Starting Gunicorn with $ENV configuration..."
            exec gunicorn nexus.wsgi:application -c gunicorn.conf.py "$@"
        fi
        ;;

    worker)
        wait_for_db
        wait_for_redis
        echo "Starting Celery Worker..."
        exec celery -A nexus worker -l info -c 4 --prefetch-multiplier 1
        ;;

    beat)
        wait_for_db
        wait_for_redis
        echo "Starting Celery Beat Scheduler..."
        exec celery -A nexus beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
        ;;

    flower)
        wait_for_redis
        echo "Starting Flower (Celery Monitor)..."
        exec celery -A nexus flower --port=5555 --basic-auth="${FLOWER_USER:-admin}:${FLOWER_PASSWORD:-admin}"
        ;;

    migrate)
        wait_for_db
        run_migrations
        ;;

    shell)
        exec python manage.py shell
        ;;

    test)
        echo "Running tests..."
        exec pytest --cov=apps --cov-report=term-missing -xvs
        ;;

    *)
        echo "Usage: $0 {web|worker|beat|flower|migrate|shell|test}"
        echo ""
        echo "Commands:"
        echo "  web     - Start web server (Django dev or Gunicorn)"
        echo "  worker  - Start Celery worker"
        echo "  beat    - Start Celery beat scheduler"
        echo "  flower  - Start Flower monitoring"
        echo "  migrate - Run database migrations"
        echo "  shell   - Open Django shell"
        echo "  test    - Run test suite"
        exit 1
        ;;
esac
