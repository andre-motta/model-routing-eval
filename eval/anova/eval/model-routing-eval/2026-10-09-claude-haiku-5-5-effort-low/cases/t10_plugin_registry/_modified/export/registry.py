from abc import ABC, abstractmethod


class UnknownFormat(ValueError):
    pass


class Exporter(ABC):
    """Base class for an output format.

    Subclasses set `name` and `extension` and implement `dump`.
    """

    name = None
    extension = None

    @abstractmethod
    def dump(self, records):
        """records: list of dicts with identical keys. Returns bytes."""


_registry = {}


def register(exporter_cls):
    """Class decorator: add an Exporter subclass to the registry under its name."""
    if not exporter_cls.name:
        raise ValueError(f"{exporter_cls.__name__} must set a name")
    if exporter_cls.name in _registry:
        raise ValueError(f"format {exporter_cls.name!r} is already registered")
    _registry[exporter_cls.name] = exporter_cls
    return exporter_cls


def get(name):
    try:
        return _registry[name]
    except KeyError:
        raise UnknownFormat(
            f"unknown format {name!r}; known formats: {', '.join(names())}"
        ) from None


def names():
    return sorted(_registry)
