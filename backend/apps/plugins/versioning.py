"""
Plugin Versioning, Dependency Resolution, and Sandboxing
"""
import re
import hashlib
import importlib.util
import sys
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from packaging import version as pkg_version
from packaging.specifiers import SpecifierSet
import logging

logger = logging.getLogger(__name__)


@dataclass
class PluginVersion:
    """Semantic versioning for plugins"""
    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build: str = ""

    @classmethod
    def parse(cls, version_str: str) -> 'PluginVersion':
        """Parse semantic version string"""
        pattern = r'^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<pre>[a-zA-Z0-9.]+))?(?:\+(?P<build>[a-zA-Z0-9.]+))?$'
        match = re.match(pattern, version_str)
        if not match:
            raise ValueError(f"Invalid version string: {version_str}")

        return cls(
            major=int(match.group('major')),
            minor=int(match.group('minor')),
            patch=int(match.group('patch')),
            prerelease=match.group('pre') or "",
            build=match.group('build') or ""
        )

    def __str__(self):
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            v += f"-{self.prerelease}"
        if self.build:
            v += f"+{self.build}"
        return v

    def __lt__(self, other):
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        return self.prerelease < other.prerelease

    def __eq__(self, other):
        return (self.major, self.minor, self.patch, self.prerelease) ==                (other.major, other.minor, other.patch, other.prerelease)


class DependencyResolver:
    """Resolve plugin dependencies with version constraints"""

    def __init__(self):
        self.installed: Dict[str, PluginVersion] = {}
        self.available: Dict[str, List[PluginVersion]] = {}

    def add_installed(self, name: str, version: str):
        """Add an installed plugin"""
        self.installed[name] = PluginVersion.parse(version)

    def add_available(self, name: str, versions: List[str]):
        """Add available versions for a plugin"""
        self.available[name] = [PluginVersion.parse(v) for v in versions]

    def resolve(self, requirements: Dict[str, str]) -> Dict[str, PluginVersion]:
        """
        Resolve dependencies using simplified SAT solver
        Returns: {plugin_name: resolved_version}
        """
        resolved = {}
        pending = list(requirements.items())
        visited = set()

        while pending:
            name, constraint = pending.pop(0)

            if name in visited:
                continue
            visited.add(name)

            # Parse constraint (e.g., ">=1.0.0,<2.0.0")
            specifier = SpecifierSet(constraint)

            # Find matching versions
            available = self.available.get(name, [])
            matching = [v for v in available if specifier.contains(str(v))]

            if not matching:
                if name in self.installed and specifier.contains(str(self.installed[name])):
                    resolved[name] = self.installed[name]
                else:
                    raise DependencyResolutionError(f"No version found for {name} matching {constraint}")
            else:
                # Pick latest stable version
                stable = [v for v in matching if not v.prerelease]
                resolved[name] = max(stable if stable else matching)

            # Add transitive dependencies (would be loaded from plugin manifest)
            # This is a simplified version

        return resolved

    def check_conflicts(self, resolved: Dict[str, PluginVersion]) -> List[str]:
        """Check for version conflicts"""
        conflicts = []
        for name, version in resolved.items():
            if name in self.installed and self.installed[name] != version:
                conflicts.append(
                    f"{name}: installed={self.installed[name]}, required={version}"
                )
        return conflicts


class DependencyResolutionError(Exception):
    pass


class PluginSandbox:
    """
    Sandboxed plugin execution environment
    Restricts file system, network, and module access
    """

    ALLOWED_MODULES = {
        'json', 're', 'datetime', 'math', 'random', 'string', 'hashlib',
        'collections', 'itertools', 'functools', 'typing', 'dataclasses',
        'decimal', 'fractions', 'statistics', 'uuid', 'time', 'calendar',
    }

    def __init__(self, plugin_id: str, plugin_path: str):
        self.plugin_id = plugin_id
        self.plugin_path = plugin_path
        self.allowed_dirs = [plugin_path]

    def create_restricted_environment(self):
        """Create a restricted execution environment"""

        def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
            """Restricted import that only allows safe modules"""
            base_module = name.split('.')[0]

            if base_module in self.ALLOWED_MODULES:
                return __import__(name, globals, locals, fromlist, level)

            # Allow plugin's own modules
            if base_module == self.plugin_id:
                return __import__(name, globals, locals, fromlist, level)

            raise ImportError(f"Module '{name}' is not allowed in plugin sandbox")

        def restricted_open(path, mode='r', *args, **kwargs):
            """Restricted file open"""
            abs_path = os.path.abspath(path)

            # Only allow access to plugin directory and temp
            allowed = any(abs_path.startswith(d) for d in self.allowed_dirs)
            allowed = allowed or abs_path.startswith('/tmp')

            if not allowed:
                raise PermissionError(f"Access denied: {path}")

            # Prevent write in certain modes
            if 'w' in mode or 'a' in mode:
                if not abs_path.startswith('/tmp'):
                    raise PermissionError(f"Write access denied: {path}")

            return open(path, mode, *args, **kwargs)

        return {
            '__builtins__': {
                'True': True, 'False': False, 'None': None,
                'abs': abs, 'all': all, 'any': any, 'ascii': ascii,
                'bin': bin, 'bool': bool, 'bytearray': bytearray,
                'bytes': bytes, 'callable': callable, 'chr': chr,
                'classmethod': classmethod, 'complex': complex,
                'delattr': delattr, 'dict': dict, 'dir': dir,
                'divmod': divmod, 'enumerate': enumerate, 'filter': filter,
                'float': float, 'format': format, 'frozenset': frozenset,
                'getattr': getattr, 'globals': globals, 'hasattr': hasattr,
                'hash': hash, 'hex': hex, 'id': id, 'input': input,
                'int': int, 'isinstance': isinstance, 'issubclass': issubclass,
                'iter': iter, 'len': len, 'list': list, 'locals': locals,
                'map': map, 'max': max, 'memoryview': memoryview, 'min': min,
                'next': next, 'object': object, 'oct': oct, 'ord': ord,
                'pow': pow, 'print': print, 'property': property,
                'range': range, 'repr': repr, 'reversed': reversed,
                'round': round, 'set': set, 'setattr': setattr,
                'slice': slice, 'sorted': sorted, 'staticmethod': staticmethod,
                'str': str, 'sum': sum, 'super': super, 'tuple': tuple,
                'type': type, 'vars': vars, 'zip': zip,
                '__import__': restricted_import,
                'open': restricted_open,
            }
        }

    def execute(self, code: str, local_vars: dict = None):
        """Execute code in sandboxed environment"""
        env = self.create_restricted_environment()
        local = local_vars or {}

        try:
            exec(code, env, local)
            return local
        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            raise


class PluginManifest:
    """Plugin manifest with metadata and dependencies"""

    def __init__(self, data: dict):
        self.name = data.get('name', '')
        self.version = data.get('version', '1.0.0')
        self.description = data.get('description', '')
        self.author = data.get('author', '')
        self.license = data.get('license', 'MIT')
        self.dependencies = data.get('dependencies', {})
        self.permissions = data.get('permissions', [])
        self.entry_point = data.get('entry_point', 'plugin')
        self.min_platform_version = data.get('min_platform_version', '1.0.0')
        self.max_platform_version = data.get('max_platform_version', '')
        self.hooks = data.get('hooks', [])
        self.config_schema = data.get('config_schema', {})

    def validate(self) -> List[str]:
        """Validate manifest"""
        errors = []
        if not self.name:
            errors.append("Plugin name is required")
        if not re.match(r'^\d+\.\d+\.\d+', self.version):
            errors.append("Invalid version format")
        return errors
