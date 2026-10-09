import importlib
import pkgutil

# Auto-discover every module in this package so each registers itself on import.
for _info in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{_info.name}")
