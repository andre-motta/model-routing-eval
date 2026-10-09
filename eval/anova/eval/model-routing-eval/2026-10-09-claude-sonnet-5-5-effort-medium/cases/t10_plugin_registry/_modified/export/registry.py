from .base import Exporter


class UnknownFormat(ValueError):
    pass


_registry = {}


def register(exporter_cls):
    """Register an Exporter subclass by its `name`. Usable as a class decorator."""
    if not (isinstance(exporter_cls, type) and issubclass(exporter_cls, Exporter)):
        raise TypeError(f"{exporter_cls!r} is not an Exporter subclass")
    if not exporter_cls.name or not exporter_cls.extension:
        raise ValueError(f"{exporter_cls.__name__} must define name and extension")
    _registry[exporter_cls.name] = exporter_cls
    return exporter_cls


def get(name):
    try:
        return _registry[name]
    except (KeyError, TypeError):
        known = ", ".join(names())
        raise UnknownFormat(f"unknown format {name!r}; known formats: {known}") from None


def names():
    return sorted(_registry)
