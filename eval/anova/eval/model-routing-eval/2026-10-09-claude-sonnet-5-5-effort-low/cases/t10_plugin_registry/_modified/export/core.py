from . import registry
from .registry import UnknownFormat

__all__ = ["export_records", "export_to_file", "UnknownFormat"]


def export_records(records, fmt):
    """records: list of dicts with identical keys. Returns bytes."""
    return registry.get(fmt).dump(records)


def export_to_file(records, fmt, path):
    exporter = registry.get(fmt)
    path = str(path)
    if not path.endswith(exporter.extension):
        path += exporter.extension
    with open(path, "wb") as f:
        f.write(exporter.dump(records))
    return path
