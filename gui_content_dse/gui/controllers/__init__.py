from __future__ import annotations

from typing import Protocol

# TODO: remove - These Protocol definitions should be moved to a separate base.py file
# to avoid confusion with actual implementations
class View(Protocol):
    def show(self) -> None:
        """Render the view using Dear PyGui."""


class Controller(Protocol):
    view: View

# Import actual controller implementations
__all__ = ["View", "Controller"]
