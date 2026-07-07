"""
Nexus Framework - Distributed Database Strategy
Supports: Multi-region Aurora PostgreSQL, MongoDB Atlas, CockroachDB, YugabyteDB
"""

import os
from django.conf import settings

# Database Router for multi-region distribution
class MultiRegionDBRouter:
    """
    Routes database operations based on:
    - Tenant region
    - Data locality requirements
    - Read/write splitting
    - Cross-region replication
    """

    def __init__(self):
        self.region_dbs = {
            'us-east-1': 'default',
            'us-west-2': 'us_west',
            'eu-west-1': 'eu_west',
            'eu-central-1': 'eu_central',
            'ap-southeast-1': 'apac',
            'me-south-1': 'me',
        }
        self.read_replicas = {
            'default': ['default_read_1', 'default_read_2'],
            'us_west': ['us_west_read_1'],
            'eu_west': ['eu_west_read_1'],
            'eu_central': ['eu_central_read_1'],
            'apac': ['apac_read_1'],
            'me': ['me_read_1'],
        }

    def _get_region(self, hints):
        """Extract region from query hints or thread-local"""
        from threading import local
        _local = local()
        return getattr(_local, 'region', 'us-east-1')

    def _get_tenant_db(self, model, hints):
        """Get database for tenant-scoped models"""
        region = self._get_region(hints)
        return self.region_dbs.get(region, 'default')

    def db_for_read(self, model, **hints):
        """Route read operations"""
        # Check if model supports read replicas
        if hasattr(model, '_use_read_replica') and model._use_read_replica:
            primary_db = self.db_for_write(model, **hints)
            replicas = self.read_replicas.get(primary_db, [primary_db])
            # Simple round-robin (in production use consistent hashing)
            import random
            return random.choice(replicas)
        return self.db_for_write(model, **hints)

    def db_for_write(self, model, **hints):
        """Route write operations"""
        # Tenant-scoped models go to tenant's region
        if hasattr(model, '_tenant_scoped') and model._tenant_scoped:
            return self._get_tenant_db(model, hints)

        # Global models stay in primary
        if hasattr(model, '_global_model') and model._global_model:
            return 'default'

        # Default to primary
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations within same region or with global models"""
        db1 = self.db_for_write(type(obj1))
        db2 = self.db_for_write(type(obj2))

        # Allow if same DB
        if db1 == db2:
            return True

        # Allow if one is global
        if hasattr(type(obj1), '_global_model') or hasattr(type(obj2), '_global_model'):
            return True

        return False

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Control migrations per database"""
        # Global models only in primary
        if app_label in ['tenants', 'plugins', 'billing']:
            return db == 'default'

        # Tenant apps migrate to all regional databases
        if app_label in ['core', 'accounts', 'inventory', 'buying', 'selling', 
                          'manufacturing', 'hr', 'crm', 'projects', 'assets', 
                          'workflow', 'industries', 'compliance', 'kpi', 'events']:
            return db in self.region_dbs.values() or db == 'default'

        return db == 'default'


# Sharding Strategy
class ShardingStrategy:
    """
    Horizontal partitioning strategy for large tables
    """

    @staticmethod
    def hash_shard(key, num_shards=16):
        """Consistent hash-based sharding"""
        import hashlib
        hash_val = int(hashlib.md5(str(key).encode()).hexdigest(), 16)
        return hash_val % num_shards

    @staticmethod
    def range_shard(key, ranges):
        """Range-based sharding"""
        for shard_id, (min_val, max_val) in enumerate(ranges):
            if min_val <= key < max_val:
                return shard_id
        return len(ranges) - 1

    @staticmethod
    def geo_shard(lat, lng, grid_size=10):
        """Geographic sharding"""
        lat_idx = int((lat + 90) / 180 * grid_size)
        lng_idx = int((lng + 180) / 360 * grid_size)
        return f"geo_{lat_idx}_{lng_idx}"

    @staticmethod
    def tenant_shard(tenant_id, num_shards=256):
        """Tenant-based sharding"""
        return ShardingStrategy.hash_shard(tenant_id, num_shards)


# Connection Pool Manager
class ConnectionPoolManager:
    """
    Manages database connection pools with health checking
    """

    def __init__(self):
        self.pools = {}
        self.health_status = {}

    def get_pool(self, db_alias):
        """Get or create connection pool"""
        if db_alias not in self.pools:
            from django.db import connections
            conn = connections[db_alias]
            self.pools[db_alias] = {
                'connection': conn,
                'created_at': __import__('time').time(),
                'queries': 0
            }
        return self.pools[db_alias]

    def health_check(self, db_alias):
        """Check database health"""
        try:
            pool = self.get_pool(db_alias)
            with pool['connection'].cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self.health_status[db_alias] = {
                'healthy': True,
                'last_check': __import__('time').time()
            }
            return True
        except Exception as e:
            self.health_status[db_alias] = {
                'healthy': False,
                'last_check': __import__('time').time(),
                'error': str(e)
            }
            return False

    def get_healthy_dbs(self):
        """Get list of healthy databases"""
        healthy = []
        for alias in self.pools:
            if self.health_check(alias):
                healthy.append(alias)
        return healthy


# Caching Layer
class DistributedCache:
    """
    Multi-tier caching: L1 (local) -> L2 (Redis Cluster) -> L3 (CDN)
    """

    def __init__(self):
        self.l1_cache = {}  # Thread-local in-memory
        self.l2_cache = None  # Redis
        self.l3_cache = None  # CDN (CloudFront)

    def _get_redis(self):
        """Get Redis connection"""
        if self.l2_cache is None:
            import redis
            from django.conf import settings
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self.l2_cache = redis.from_url(redis_url, decode_responses=True)
        return self.l2_cache

    def get(self, key, tier='l2'):
        """Get value from cache"""
        # Try L1 first
        if tier in ['l1', 'l2', 'l3'] and key in self.l1_cache:
            return self.l1_cache[key]

        # Try L2 (Redis)
        if tier in ['l2', 'l3']:
            try:
                redis = self._get_redis()
                value = redis.get(key)
                if value:
                    # Populate L1
                    self.l1_cache[key] = value
                    return value
            except Exception:
                pass

        return None

    def set(self, key, value, ttl=300, tier='l2'):
        """Set value in cache"""
        # Set in L1
        self.l1_cache[key] = value

        # Set in L2
        if tier in ['l2', 'l3']:
            try:
                redis = self._get_redis()
                redis.setex(key, ttl, value)
            except Exception:
                pass

    def invalidate(self, key_pattern):
        """Invalidate cache entries matching pattern"""
        # Clear L1
        keys_to_remove = [k for k in self.l1_cache if key_pattern in k]
        for k in keys_to_remove:
            del self.l1_cache[k]

        # Clear L2
        try:
            redis = self._get_redis()
            for key in redis.scan_iter(match=f"*{key_pattern}*"):
                redis.delete(key)
        except Exception:
            pass

    def cache_aside(self, key, fetch_func, ttl=300):
        """Cache-aside pattern"""
        value = self.get(key)
        if value is None:
            value = fetch_func()
            self.set(key, value, ttl)
        return value


# Write-Ahead Log for Event Sourcing
class WriteAheadLog:
    """
    WAL for ensuring durability in distributed transactions
    """

    def __init__(self):
        self.log_entries = []

    def append(self, operation, data):
        """Append operation to WAL"""
        entry = {
            'id': str(__import__('uuid').uuid4()),
            'timestamp': __import__('time').time(),
            'operation': operation,
            'data': data,
            'committed': False
        }
        self.log_entries.append(entry)
        return entry['id']

    def commit(self, entry_id):
        """Mark entry as committed"""
        for entry in self.log_entries:
            if entry['id'] == entry_id:
                entry['committed'] = True
                return True
        return False

    def recover(self):
        """Recover uncommitted operations"""
        uncommitted = [e for e in self.log_entries if not e['committed']]
        return uncommitted


# Cross-Region Replication Manager
class ReplicationManager:
    """
    Manages async replication between regions
    """

    def __init__(self):
        self.replication_lag = {}

    def replicate_event(self, event, target_regions):
        """Replicate event to target regions"""
        from apps.events.consumers import EventBus

        bus = EventBus()
        for region in target_regions:
            try:
                bus.publish(
                    f'nexus.replication.{region}',
                    {
                        'event_id': str(event.event_id),
                        'event_name': event.event_name,
                        'payload': event.payload,
                        'source_region': event.region,
                        'timestamp': str(event.timestamp)
                    },
                    key=event.aggregate_id
                )
                self.replication_lag[region] = 0
            except Exception as e:
                self.replication_lag[region] = -1
                __import__('logging').getLogger(__name__).error(f"Replication to {region} failed: {e}")

    def get_replication_status(self):
        """Get replication status for all regions"""
        return self.replication_lag


# Database Migration Strategy
class MigrationStrategy:
    """
    Zero-downtime migration strategies
    """

    @staticmethod
    def expand_contract_migration(model, new_field, old_field):
        """
        Expand-Contract pattern for schema changes
        Phase 1: Expand (add new field, dual-write)
        Phase 2: Migrate (backfill data)
        Phase 3: Contract (remove old field)
        """
        return {
            'phase': 'expand',
            'new_field': new_field,
            'old_field': old_field,
            'dual_write': True,
            'backfill_required': True
        }

    @staticmethod
    def blue_green_migration(db_alias):
        """
        Blue-Green deployment for major migrations
        """
        return {
            'strategy': 'blue_green',
            'blue_db': db_alias,
            'green_db': f'{db_alias}_green',
            'cutover_steps': [
                '1. Sync green from blue',
                '2. Verify green',
                '3. Switch traffic to green',
                '4. Monitor',
                '5. Decommission blue'
            ]
        }

    @staticmethod
    def shadow_migration(model, shadow_table):
        """
        Shadow table migration for large tables
        """
        return {
            'strategy': 'shadow',
            'main_table': model._meta.db_table,
            'shadow_table': shadow_table,
            'steps': [
                '1. Create shadow table with new schema',
                '2. Set up triggers to sync shadow',
                '3. Backfill shadow table',
                '4. Verify consistency',
                '5. Atomic rename'
            ]
        }


# Usage in settings.py:
"""
DATABASE_ROUTERS = ['apps.core.db_strategy.MultiRegionDBRouter']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nexus',
        'HOST': 'nexus-primary.cluster-xxx.us-east-1.rds.amazonaws.com',
        'PORT': '5432',
        'USER': 'nexus_admin',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    },
    'default_read_1': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nexus',
        'HOST': 'nexus-replica-1.xxx.us-east-1.rds.amazonaws.com',
        'PORT': '5432',
        'USER': 'nexus_read',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'OPTIONS': {'connect_timeout': 10},
    },
    'default_read_2': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nexus',
        'HOST': 'nexus-replica-2.xxx.us-east-1.rds.amazonaws.com',
        'PORT': '5432',
        'USER': 'nexus_read',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'OPTIONS': {'connect_timeout': 10},
    },
    'eu_west': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nexus',
        'HOST': 'nexus-eu.cluster-xxx.eu-west-1.rds.amazonaws.com',
        'PORT': '5432',
        'USER': 'nexus_admin',
        'PASSWORD': os.getenv('DB_PASSWORD'),
    },
    'eu_west_read_1': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nexus',
        'HOST': 'nexus-eu-replica.xxx.eu-west-1.rds.amazonaws.com',
        'PORT': '5432',
        'USER': 'nexus_read',
        'PASSWORD': os.getenv('DB_PASSWORD'),
    },
    # ... more regions
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://nexus-cache.xxx.cache.amazonaws.com:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        }
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://nexus-cache.xxx.cache.amazonaws.com:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
"""
