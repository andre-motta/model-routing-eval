"""Built-in formats. Every module in this package is imported on package
import, so decorating an Exporter with @register is enough to add a format."""
import importlib
import pkgutil

for _mod in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{_mod.name}")
