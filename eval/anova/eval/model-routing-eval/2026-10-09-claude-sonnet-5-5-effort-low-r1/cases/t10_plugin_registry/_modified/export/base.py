class Exporter:
    """Base class for export formats. Subclasses set name and extension."""

    name = None
    extension = None

    def dump(self, records):
        """records: list of dicts with identical keys. Returns bytes."""
        raise NotImplementedError
