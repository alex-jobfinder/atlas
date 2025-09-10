from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

from . import Controller


@dataclass
class TabSpec:
    """Specification for a tab controller and its view factory."""

    name: str
    controller_factory: Callable[[], Controller]


class Registry:
    """Registry for managing tab specifications and plugins."""
    
    def __init__(self):
        self._registry: Dict[str, TabSpec] = {}
    
    def register(self, spec: TabSpec) -> None:
        """Register a new tab specification."""
        self._registry[spec.name] = spec
    
    def get(self, name: str) -> TabSpec:
        """Get a tab specification by name."""
        return self._registry[name]
    
    def all_specs(self) -> Dict[str, TabSpec]:
        """Get all registered tab specifications."""
        return dict(self._registry)
    
    def list_names(self) -> list[str]:
        """List all registered tab names."""
        return list(self._registry.keys())


# Global registry instance
_REGISTRY = Registry()

# Convenience functions for backward compatibility
def register(spec: TabSpec) -> None:
    """Register a new tab specification."""
    _REGISTRY.register(spec)


def get(name: str) -> TabSpec:
    """Get a tab specification by name."""
    return _REGISTRY.get(name)


def all_specs() -> Dict[str, TabSpec]:
    """Get all registered tab specifications."""
    return _REGISTRY.all_specs()