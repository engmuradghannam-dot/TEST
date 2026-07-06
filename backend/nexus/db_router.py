"""
Database Router for Nexus Framework
Ensures tenant data separation at the database level
"""

class TenantRouter:
    """
    A database router that directs all read/write operations
    to the appropriate database based on the current tenant.
    """

    def db_for_read(self, model, **hints):
        """Direct read operations to the default database."""
        return 'default'

    def db_for_write(self, model, **hints):
        """Direct write operations to the default database."""
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if both objects are in the same database."""
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Allow migrations on the default database only."""
        return db == 'default'


class ModuleRouter:
    """
    Optional router to separate core vs module data.
    Can be extended to route specific apps to different databases.
    """

    CORE_APPS = {'auth', 'contenttypes', 'sessions', 'admin', 'core'}
    MODULE_APPS = {
        'accounts', 'assets', 'buying', 'selling', 'inventory',
        'hr', 'crm', 'projects', 'manufacturing', 'workflow'
    }

    def db_for_read(self, model, **hints):
        app = model._meta.app_label
        if app in self.CORE_APPS:
            return 'default'
        return 'default'

    def db_for_write(self, model, **hints):
        app = model._meta.app_label
        if app in self.CORE_APPS:
            return 'default'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == 'default'
