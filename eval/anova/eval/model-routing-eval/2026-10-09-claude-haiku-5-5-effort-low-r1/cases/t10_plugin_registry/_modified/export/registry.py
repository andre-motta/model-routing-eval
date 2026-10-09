from abc import ABC, abstractmethod


class UnknownFormat(ValueError):
    pass


class Exporter(ABC):
    """Base class for an export format.

    Subclasses set ``name`` and ``extension`` (with the leading dot) and
    implement ``dump``. Register a subclass with ``@register``.
    """

    name: str
    extension: str

    @abstractmethod
    def dump(self, records):
        """records: list of dicts with identical keys. Returns bytes."""


_exporters = {}


def register(exporter_cls):
    """Class decorator that adds an Exporter subclass to the registry."""
    name = exporter_cls.name
    existing = _exporters.get(name)
    if existing is not None and existing is not exporter_cls:
        raise ValueError(f"export format {name!r} is already registered")
    _exporters[name] = exporter_cls
    return exporter_cls


def get(name):
    """Return an Exporter instance for ``name``, or raise UnknownFormat."""
    try:
        exporter_cls = _exporters[name]
    except KeyError:
        known = ", ".join(names())
        raise UnknownFormat(f"unknown format {name!r}; known formats: {known}") from None
    return exporter_cls()


def names():
    """Sorted list of registered format names."""
    return sorted(_exporters)
