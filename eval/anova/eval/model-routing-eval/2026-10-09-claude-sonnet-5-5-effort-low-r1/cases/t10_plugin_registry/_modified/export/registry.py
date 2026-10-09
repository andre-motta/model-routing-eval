class UnknownFormat(ValueError):
    pass


_exporters = {}


def register(exporter_cls):
    """Register an Exporter subclass; usable as a class decorator."""
    if not exporter_cls.name:
        raise ValueError(f"{exporter_cls.__name__} must define a name")
    _exporters[exporter_cls.name] = exporter_cls()
    return exporter_cls


def get(name):
    try:
        return _exporters[name]
    except KeyError:
        known = ", ".join(names())
        raise UnknownFormat(f"unknown format {name!r}; known formats: {known}") from None


def names():
    return sorted(_exporters)
