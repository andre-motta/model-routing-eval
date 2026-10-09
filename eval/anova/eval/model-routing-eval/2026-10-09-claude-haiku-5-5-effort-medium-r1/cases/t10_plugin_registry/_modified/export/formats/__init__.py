"""Built-in export formats.

Every module in this package is imported on load, so any Exporter decorated
with ``@register`` is available without editing the registry or core.
"""

import importlib
import pkgutil

for _module in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{_module.name}")
