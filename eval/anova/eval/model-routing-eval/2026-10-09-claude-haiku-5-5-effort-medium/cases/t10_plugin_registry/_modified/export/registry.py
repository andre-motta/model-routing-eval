from abc import ABC, abstractmethod


class UnknownFormat(ValueError):
    pass


class Exporter(ABC):
    """Serialises a list of record dicts to bytes in one format.

    Subclasses set `name` (the format key, e.g. "csv") and `extension`
    (including the leading dot, e.g. ".csv"), then decorate with @register.
    """

    name: str
    extension: str

    @abstractmethod
    def dump(self, records):
        """records: list of dicts with identical keys. Returns bytes."""


_exporters = {}


def register(exporter_cls):
    """Class decorator: add an Exporter subclass to the registry under its name."""
    if exporter_cls.name in _exporters:
        raise ValueError(f"exporter {exporter_cls.name!r} is already registered")
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
