"""
Enhanced Plugin System for Nexus CE-ERP OS
Features: Registry, Lifecycle, Versioning, Dependency Resolution, Tenant-based, Sandboxing
"""
import os
import sys
import json
import logging
import hashlib
import importlib
import importlib.util
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import uuid

from apps.core.event_bus import event_bus, DomainEvent, EventTypes, EventPriority

logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPRECATED = "deprecated"
    UNINSTALLED = "uninstalled"


class PluginLifecycleAction(Enum):
    INSTALL = "install"
    UPDATE = "update"
    UNINSTALL = "uninstall"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"


@dataclass
class PluginManifest:
    """Plugin manifest definition"""
    name: str
    slug: str
    version: str
    description: str = ""
    author: str = ""
    author_email: str = ""
    license: str = "MIT"
    min_nexus_version: str = "1.0.0"
    max_nexus_version: str = ""
    dependencies: List[Dict] = None
    permissions: List[str] = None
    hooks: List[str] = None
    models: List[str] = None
    views: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.permissions is None:
            self.permissions = []
        if self.hooks is None:
            self.hooks = []
        if self.models is None:
            self.models = []
        if self.views is None:
            self.views = []

    @classmethod
    def from_dict(cls, data: Dict) -> 'PluginManifest':
        return cls(**data)

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'slug': self.slug,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'author_email': self.author_email,
            'license': self.license,
            'min_nexus_version': self.min_nexus_version,
            'max_nexus_version': self.max_nexus_version,
            'dependencies': self.dependencies,
            'permissions': self.permissions,
            'hooks': self.hooks,
            'models': self.models,
            'views': self.views
        }


# ============================================================
# Models
# ============================================================

class PluginRegistry(models.Model):
    """Central plugin registry"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Manifest data
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    version = models.CharField(max_length=20, default='1.0.0', verbose_name=_('Version'))
    author = models.CharField(max_length=200, blank=True, verbose_name=_('Author'))
    author_email = models.EmailField(blank=True, verbose_name=_('Author Email'))

    # Code
    module_path = models.CharField(max_length=500, verbose_name=_('Module Path'))
    entry_point = models.CharField(max_length=200, default='plugin', verbose_name=_('Entry Point'))
    source_code_hash = models.CharField(max_length=64, blank=True, verbose_name=_('Source Hash'))

    # Status
    status = models.CharField(max_length=20, choices=[
        (s.value, s.value.title()) for s in PluginStatus
    ], default=PluginStatus.PENDING.value)

    # Marketplace
    is_published = models.BooleanField(default=False, verbose_name=_('Is Published'))
    is_premium = models.BooleanField(default=False, verbose_name=_('Is Premium'))
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_('Price'))
    category = models.CharField(max_length=100, blank=True, verbose_name=_('Category'))
    tags = models.JSONField(default=list, blank=True)
    icon = models.CharField(max_length=200, blank=True, verbose_name=_('Icon URL'))
    screenshots = models.JSONField(default=list, blank=True)

    # Stats
    download_count = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0.0)
    review_count = models.PositiveIntegerField(default=0)

    # Manifest
    manifest = models.JSONField(default=dict, verbose_name=_('Manifest'))
    dependencies = models.JSONField(default=list, verbose_name=_('Dependencies'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-download_count', '-rating']
        indexes = [
            models.Index(fields=['status', 'is_published']),
            models.Index(fields=['category']),
            models.Index(fields=['slug', 'version']),
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"

    def get_manifest(self) -> PluginManifest:
        return PluginManifest.from_dict(self.manifest)


class TenantPlugin(models.Model):
    """Plugin activated for a specific tenant"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='plugins')
    plugin = models.ForeignKey(PluginRegistry, on_delete=models.CASCADE, related_name='tenant_installations')

    status = models.CharField(max_length=20, choices=[
        (s.value, s.value.title()) for s in PluginStatus
    ], default=PluginStatus.PENDING.value)

    # Configuration
    config = models.JSONField(default=dict, blank=True)

    # Lifecycle
    installed_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    uninstalled_at = models.DateTimeField(null=True, blank=True)

    # Version management
    installed_version = models.CharField(max_length=20)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['tenant', 'plugin']]
        indexes = [
            models.Index(fields=['tenant', 'status']),
        ]

    def __str__(self):
        return f"{self.plugin.name} on {self.tenant.name}"


class PluginReview(models.Model):
    """User reviews for marketplace plugins"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plugin = models.ForeignKey(PluginRegistry, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('core.User', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=200, blank=True)
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['plugin', 'user']]


class PluginSandbox(models.Model):
    """Sandbox execution environment for plugins"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plugin = models.ForeignKey(PluginRegistry, on_delete=models.CASCADE, related_name='sandboxes')
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='plugin_sandboxes')

    # Security
    allowed_modules = models.JSONField(default=list, help_text="Allowed Python modules")
    allowed_apis = models.JSONField(default=list, help_text="Allowed API endpoints")
    max_execution_time = models.PositiveIntegerField(default=30, help_text="Max execution time in seconds")
    max_memory_mb = models.PositiveIntegerField(default=128)

    # Execution log
    execution_log = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)


# ============================================================
# Dependency Resolver
# ============================================================

class DependencyResolver:
    """Resolves plugin dependencies"""

    def __init__(self):
        self._cache = {}

    def resolve_dependencies(self, plugin: PluginRegistry, tenant) -> Tuple[bool, List[str]]:
        """Check if all dependencies are satisfied"""
        dependencies = plugin.dependencies
        missing = []

        for dep in dependencies:
            dep_slug = dep.get('slug')
            dep_version = dep.get('version', '*')
            dep_required = dep.get('required', True)

            if not dep_required:
                continue

            # Check if dependency is installed for tenant
            installed = TenantPlugin.objects.filter(
                tenant=tenant,
                plugin__slug=dep_slug,
                status__in=[PluginStatus.ACTIVE.value, PluginStatus.PENDING.value]
            ).exists()

            if not installed:
                missing.append(f"{dep_slug} ({dep_version})")

        return len(missing) == 0, missing

    def get_installation_order(self, plugins: List[PluginRegistry]) -> List[PluginRegistry]:
        """Get installation order respecting dependencies"""
        # Build dependency graph
        graph = {}
        for p in plugins:
            graph[p.slug] = [d.get('slug') for d in p.dependencies if d.get('required', True)]

        # Topological sort
        visited = set()
        order = []

        def visit(slug):
            if slug in visited:
                return
            visited.add(slug)
            for dep in graph.get(slug, []):
                visit(dep)
            plugin = next((p for p in plugins if p.slug == slug), None)
            if plugin:
                order.append(plugin)

        for slug in graph:
            visit(slug)

        return order

    def check_conflicts(self, plugin: PluginRegistry, tenant) -> List[str]:
        """Check for conflicts with existing plugins"""
        conflicts = []

        # Check for duplicate functionality
        installed = TenantPlugin.objects.filter(
            tenant=tenant,
            status=PluginStatus.ACTIVE.value
        ).select_related('plugin')

        for tp in installed:
            if tp.plugin.category == plugin.category and tp.plugin.slug != plugin.slug:
                conflicts.append(f"Category conflict with {tp.plugin.name}")

        return conflicts


# ============================================================
# Plugin Lifecycle Manager
# ============================================================

class PluginLifecycleManager:
    """Manages plugin lifecycle: install, update, uninstall, activate, deactivate"""

    def __init__(self):
        self.dependency_resolver = DependencyResolver()
        self.sandbox_manager = PluginSandboxManager()

    def install(self, plugin: PluginRegistry, tenant, config: Dict = None, user=None) -> Dict:
        """Install a plugin for a tenant"""
        # Check if already installed
        existing = TenantPlugin.objects.filter(tenant=tenant, plugin=plugin).first()
        if existing:
            return {'success': False, 'error': 'Plugin already installed'}

        # Check dependencies
        deps_ok, missing = self.dependency_resolver.resolve_dependencies(plugin, tenant)
        if not deps_ok:
            return {'success': False, 'error': f'Missing dependencies: {", ".join(missing)}'}

        # Check conflicts
        conflicts = self.dependency_resolver.check_conflicts(plugin, tenant)
        if conflicts:
            return {'success': False, 'error': f'Conflicts: {", ".join(conflicts)}'}

        # Create tenant plugin
        tenant_plugin = TenantPlugin.objects.create(
            tenant=tenant,
            plugin=plugin,
            status=PluginStatus.PENDING.value,
            config=config or {},
            installed_version=plugin.version
        )

        # Run installation hook
        try:
            self._run_hook(plugin, 'install', tenant, config)
            tenant_plugin.status = PluginStatus.ACTIVE.value
            tenant_plugin.activated_at = datetime.now()
            tenant_plugin.save()

            # Publish event
            event = DomainEvent.create(
                event_type=EventTypes.PLUGIN_INSTALLED,
                aggregate_type="plugin",
                aggregate_id=str(plugin.id),
                tenant_id=str(tenant.id),
                payload={'plugin_slug': plugin.slug, 'version': plugin.version}
            )
            event_bus.publish(event)

            return {'success': True, 'tenant_plugin_id': str(tenant_plugin.id)}
        except Exception as e:
            tenant_plugin.status = PluginStatus.ERROR.value
            tenant_plugin.save()
            return {'success': False, 'error': str(e)}

    def update(self, tenant_plugin: TenantPlugin, new_plugin: PluginRegistry, user=None) -> Dict:
        """Update a plugin to a new version"""
        if tenant_plugin.plugin == new_plugin:
            return {'success': False, 'error': 'Already on this version'}

        # Run pre-update hook
        try:
            self._run_hook(tenant_plugin.plugin, 'pre_update', tenant_plugin.tenant, tenant_plugin.config)
        except Exception as e:
            return {'success': False, 'error': f'Pre-update hook failed: {e}'}

        # Backup current config
        old_config = tenant_plugin.config.copy()

        # Update
        tenant_plugin.plugin = new_plugin
        tenant_plugin.installed_version = new_plugin.version
        tenant_plugin.status = PluginStatus.PENDING.value
        tenant_plugin.save()

        # Run post-update hook
        try:
            self._run_hook(new_plugin, 'post_update', tenant_plugin.tenant, old_config)
            tenant_plugin.status = PluginStatus.ACTIVE.value
            tenant_plugin.save()

            event = DomainEvent.create(
                event_type=EventTypes.PLUGIN_UPDATED,
                aggregate_type="plugin",
                aggregate_id=str(new_plugin.id),
                tenant_id=str(tenant_plugin.tenant.id),
                payload={'from_version': tenant_plugin.installed_version, 'to_version': new_plugin.version}
            )
            event_bus.publish(event)

            return {'success': True}
        except Exception as e:
            tenant_plugin.status = PluginStatus.ERROR.value
            tenant_plugin.save()
            return {'success': False, 'error': str(e)}

    def uninstall(self, tenant_plugin: TenantPlugin, user=None) -> Dict:
        """Uninstall a plugin from a tenant"""
        # Check if other plugins depend on this
        dependents = self._get_dependents(tenant_plugin.plugin, tenant_plugin.tenant)
        if dependents:
            return {'success': False, 'error': f'Other plugins depend on this: {", ".join(dependents)}'}

        # Run uninstall hook
        try:
            self._run_hook(tenant_plugin.plugin, 'uninstall', tenant_plugin.tenant, tenant_plugin.config)
        except Exception as e:
            logger.warning(f"Uninstall hook failed: {e}")

        tenant_plugin.status = PluginStatus.UNINSTALLED.value
        tenant_plugin.uninstalled_at = datetime.now()
        tenant_plugin.save()

        event = DomainEvent.create(
            event_type=EventTypes.PLUGIN_UNINSTALLED,
            aggregate_type="plugin",
            aggregate_id=str(tenant_plugin.plugin.id),
            tenant_id=str(tenant_plugin.tenant.id),
            payload={'plugin_slug': tenant_plugin.plugin.slug}
        )
        event_bus.publish(event)

        return {'success': True}

    def activate(self, tenant_plugin: TenantPlugin, user=None) -> Dict:
        """Activate a plugin"""
        tenant_plugin.status = PluginStatus.ACTIVE.value
        tenant_plugin.activated_at = datetime.now()
        tenant_plugin.save()

        event = DomainEvent.create(
            event_type=EventTypes.PLUGIN_ACTIVATED,
            aggregate_type="plugin",
            aggregate_id=str(tenant_plugin.plugin.id),
            tenant_id=str(tenant_plugin.tenant.id)
        )
        event_bus.publish(event)

        return {'success': True}

    def deactivate(self, tenant_plugin: TenantPlugin, user=None) -> Dict:
        """Deactivate a plugin"""
        tenant_plugin.status = PluginStatus.INACTIVE.value
        tenant_plugin.deactivated_at = datetime.now()
        tenant_plugin.save()
        return {'success': True}

    def _run_hook(self, plugin: PluginRegistry, hook_name: str, tenant, config: Dict):
        """Run a plugin hook"""
        # This would dynamically load and execute plugin code
        # For security, this runs in sandbox
        logger.info(f"Running hook {hook_name} for plugin {plugin.slug}")

    def _get_dependents(self, plugin: PluginRegistry, tenant) -> List[str]:
        """Get plugins that depend on this plugin"""
        dependents = []
        installed = TenantPlugin.objects.filter(
            tenant=tenant,
            status__in=[PluginStatus.ACTIVE.value, PluginStatus.PENDING.value]
        ).select_related('plugin')

        for tp in installed:
            for dep in tp.plugin.dependencies:
                if dep.get('slug') == plugin.slug and dep.get('required', True):
                    dependents.append(tp.plugin.name)

        return dependents


# ============================================================
# Plugin Sandbox Manager
# ============================================================

class PluginSandboxManager:
    """Manages sandboxed execution of plugin code"""

    ALLOWED_BUILTINS = {
        'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'filter',
        'float', 'int', 'isinstance', 'issubclass', 'len', 'list',
        'map', 'max', 'min', 'pow', 'range', 'round', 'set', 'str',
        'sum', 'tuple', 'zip', 'json', 'datetime'
    }

    def __init__(self):
        self._sandboxes = {}

    def create_sandbox(self, plugin: PluginRegistry, tenant) -> PluginSandbox:
        """Create a sandbox for a plugin"""
        sandbox = PluginSandbox.objects.create(
            plugin=plugin,
            tenant=tenant,
            allowed_modules=['json', 'datetime', 'math', 're', 'collections'],
            allowed_apis=['/api/core/', '/api/accounts/'],
            max_execution_time=30,
            max_memory_mb=128
        )
        return sandbox

    def execute_in_sandbox(self, sandbox: PluginSandbox, code: str, context: Dict = None) -> Dict:
        """Execute code in sandboxed environment"""
        import signal
        import resource

        result = {'success': False, 'output': None, 'error': None}

        def timeout_handler(signum, frame):
            raise TimeoutError("Plugin execution timed out")

        # Set resource limits
        try:
            resource.setrlimit(resource.RLIMIT_AS, (sandbox.max_memory_mb * 1024 * 1024, -1))
        except:
            pass

        # Set timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(sandbox.max_execution_time)

        try:
            # Create restricted globals
            restricted_globals = {
                '__builtins__': {name: __builtins__[name] for name in self.ALLOWED_BUILTINS if name in __builtins__},
                'json': __import__('json'),
                'datetime': __import__('datetime'),
                'math': __import__('math'),
                're': __import__('re'),
            }

            local_vars = context or {}

            # Execute
            exec(code, restricted_globals, local_vars)

            result['success'] = True
            result['output'] = local_vars.get('result')

        except TimeoutError as e:
            result['error'] = f"Execution timeout after {sandbox.max_execution_time}s"
        except Exception as e:
            result['error'] = str(e)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

        # Log execution
        sandbox.execution_log.append({
            'timestamp': datetime.now().isoformat(),
            'success': result['success'],
            'error': result['error']
        })
        sandbox.save()

        return result


# ============================================================
# Plugin Hook System
# ============================================================

class PluginHookRegistry:
    """Registry for plugin hooks"""

    _hooks: Dict[str, List[Dict]] = {}

    @classmethod
    def register_hook(cls, hook_name: str, plugin_slug: str, callback: str, priority: int = 10):
        """Register a hook"""
        if hook_name not in cls._hooks:
            cls._hooks[hook_name] = []
        cls._hooks[hook_name].append({
            'plugin': plugin_slug,
            'callback': callback,
            'priority': priority
        })
        cls._hooks[hook_name].sort(key=lambda x: x['priority'])

    @classmethod
    def execute_hooks(cls, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all registered hooks for a hook name"""
        results = []
        for hook in cls._hooks.get(hook_name, []):
            try:
                # Would dynamically call plugin callback
                logger.info(f"Executing hook {hook_name} from {hook['plugin']}")
            except Exception as e:
                logger.error(f"Hook execution failed: {e}")
        return results

    @classmethod
    def get_hooks(cls, hook_name: str) -> List[Dict]:
        return cls._hooks.get(hook_name, [])


# ============================================================
# Global Instances
# ============================================================

plugin_lifecycle_manager = PluginLifecycleManager()
plugin_sandbox_manager = PluginSandboxManager()
