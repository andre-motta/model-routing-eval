class UnknownFormat(ValueError):
    pass


_exporters = {}


def register(exporter_cls):
    """Class decorator that adds an Exporter subclass to the registry."""
    name = getattr(exporter_cls, "name", None)
    if not name:
        raise ValueError(f"{exporter_cls.__name__} must define a non-empty 'name'")
    if name in _exporters:
        raise ValueError(f"export format {name!r} is already registered")
    _exporters[name] = exporter_cls
    return exporter_cls


def names():
    """Sorted list of registered format names."""
    return sorted(_exporters)


def get(name):
    """Return a new exporter instance for ``name``; raise UnknownFormat if absent."""
    try:
        exporter_cls = _exporters[name]
    except KeyError:
        known = ", ".join(names())
        raise UnknownFormat(f"unknown format {name!r}; known formats: {known}") from None
    return exporter_cls()
