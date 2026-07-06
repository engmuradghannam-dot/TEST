"""
Nexus SaaS - Module Registry
Central registry for all ERP modules with dependency management.
"""

MODULES = {
    'core': {
        'name': 'Core',
        'version': '1.0.0',
        'dependencies': [],
        'description': 'Core utilities, permissions, and shared components',
        'enabled': True,
    },
    'tenants': {
        'name': 'Tenants',
        'version': '1.0.0',
        'dependencies': ['core'],
        'description': 'Multi-tenancy management',
        'enabled': True,
    },
    'billing': {
        'name': 'Billing',
        'version': '1.0.0',
        'dependencies': ['core', 'tenants'],
        'description': 'Stripe billing and subscriptions',
        'enabled': True,
    },
    'plugins': {
        'name': 'Plugins',
        'version': '1.0.0',
        'dependencies': ['core', 'tenants'],
        'description': 'Plugin marketplace and dynamic loading',
        'enabled': True,
    },
    'accounts': {
        'name': 'Accounting',
        'version': '1.0.0',
        'dependencies': ['core', 'tenants'],
        'description': 'Financial accounting and general ledger',
        'enabled': True,
    },
    'inventory': {
        'name': 'Inventory',
        'version': '1.0.0',
        'dependencies': ['core', 'tenants'],
        'description': 'Inventory and warehouse management',
        'enabled': True,
    },
    'buying': {
        'name': 'Purchasing',
        'version': '1.0.0',
        'dependencies': ['core', 'tenants', 'inventory'],
        'description': 'Purchase orders and supplier management',
        'enabled': True,
    },
    'selling': {
        'name': 'Sales',
        'version': '1.0.0',
        'dependencies': ['core', 'tenants', 'inventory'],
        'description': 'Sales orders and customer management',
        'enabled': True,
    },
    'manufacturing': {
        'name': 'Manufacturing',
        'version': '1.0.0',
        'dependencies': ['core', 'tenants', 'inventory'],
        'description': 'Production and BOM management',
        'enabled': True,
    },
    'hr': {
        'name': 'Human Resources',
        'version': '1.0.0',
        'dependencies': ['core', 'tenants'],
        'description': 'Employee management and payroll',
        'enabled': True,
    },
    'crm': {
        'name': 'CRM',
        'version': '1.0.0',
        'dependencies': ['core', 'tenants'],
        'description': 'Customer relationship management',
        'enabled': True,
    },
    'projects': {
        'name': 'Projects',
        'version': '1.0.0',
        'dependencies': ['core', 'tenants'],
        'description': 'Project management and PMO',
        'enabled': True,
    },
    'assets': {
        'name': 'Fixed Assets',
        'version': '1.0.0',
        'dependencies': ['core', 'tenants'],
        'description': 'Fixed asset tracking and depreciation',
        'enabled': True,
    },
    'workflow': {
        'name': 'Workflow',
        'version': '1.0.0',
        'dependencies': ['core', 'tenants'],
        'description': 'Business process automation',
        'enabled': True,
    },
}


def get_module_dependencies(module_name):
    """Get all dependencies for a module (recursive)."""
    if module_name not in MODULES:
        return []

    deps = set()
    stack = list(MODULES[module_name]['dependencies'])

    while stack:
        dep = stack.pop()
        if dep not in deps:
            deps.add(dep)
            if dep in MODULES:
                stack.extend(MODULES[dep]['dependencies'])

    return list(deps)


def check_module_enabled(module_name):
    """Check if a module and all its dependencies are enabled."""
    if module_name not in MODULES:
        return False

    if not MODULES[module_name]['enabled']:
        return False

    for dep in MODULES[module_name]['dependencies']:
        if not check_module_enabled(dep):
            return False

    return True


def get_enabled_modules():
    """Get all enabled modules."""
    return {name: info for name, info in MODULES.items() if check_module_enabled(name)}
