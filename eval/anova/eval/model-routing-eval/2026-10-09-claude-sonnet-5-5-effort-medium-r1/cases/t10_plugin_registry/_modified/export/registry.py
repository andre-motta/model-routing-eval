class UnknownFormat(ValueError):
    pass


class Exporter:
    """Base class for export formats. Subclasses set name and extension."""

    name = None
    extension = None

    def dump(self, records):
        """records: list of dicts with identical keys. Returns bytes."""
        raise NotImplementedError


_registry = {}


def register(exporter_cls):
    """Register an Exporter subclass. Usable as a class decorator."""
    if not exporter_cls.name or not exporter_cls.extension:
        raise ValueError(f"{exporter_cls.__name__} must define name and extension")
    _registry[exporter_cls.name] = exporter_cls
    return exporter_cls


def names():
    return sorted(_registry)


def get(name):
    try:
        return _registry[name]()
    except KeyError:
        raise UnknownFormat(
            f"unknown format {name!r}; known formats: {', '.join(names())}"
        ) from None
