from abc import ABC, abstractmethod


class Exporter(ABC):
    """Serialises a list of record dicts (identical keys) to bytes.

    Subclasses set ``name`` and ``extension`` and implement ``dump``.
    """

    name: str
    extension: str

    @abstractmethod
    def dump(self, records):
        """Return the serialised form of ``records`` as bytes."""
