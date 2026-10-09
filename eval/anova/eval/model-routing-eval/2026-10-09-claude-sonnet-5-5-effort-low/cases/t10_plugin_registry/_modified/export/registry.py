class UnknownFormat(ValueError):
    pass


class Exporter:
    """Base class for export formats. Subclasses set name/extension and implement dump."""

    name = None
    extension = None

    def dump(self, records):
        """records: list of dicts with identical keys. Returns bytes."""
        raise NotImplementedError


_registry = {}


def register(exporter_cls):
    """Register an Exporter subclass under its name. Usable as a class decorator."""
    if not exporter_cls.name:
        raise ValueError(f"{exporter_cls.__name__} must define a name")
    _registry[exporter_cls.name] = exporter_cls()
    return exporter_cls


def get(name):
    try:
        return _registry[name]
    except KeyError:
        known = ", ".join(names())
        raise UnknownFormat(f"unknown format {name!r}; known formats: {known}") from None


def names():
    return sorted(_registry)
