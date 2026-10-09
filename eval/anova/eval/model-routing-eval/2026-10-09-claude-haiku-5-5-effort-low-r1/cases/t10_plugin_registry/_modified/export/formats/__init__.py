import importlib
import pkgutil

# Import every module in this package so its @register decorators run.
# Adding a format means adding a module here; nothing else needs to change.
for _info in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{_info.name}")
