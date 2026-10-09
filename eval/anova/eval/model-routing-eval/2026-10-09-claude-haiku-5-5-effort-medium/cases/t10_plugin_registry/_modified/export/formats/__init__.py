import importlib
import pkgutil


# Import every module in this package so its @register decorators run.
# Dropping a new module here is enough to add a format.
for _module in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{_module.name}")
