"""app.controllers package

Changelog:
- 2026-01-29: Export `TestController` so FQN `app.controllers.TestController` resolves.
"""

from .routes.TestController import TestController

__all__ = ["TestController"]
