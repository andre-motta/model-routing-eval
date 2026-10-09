import json

from ..registry import Exporter, register


@register
class JsonExporter(Exporter):
    name = "json"
    extension = ".json"

    def dump(self, records):
        return json.dumps(records, indent=2, sort_keys=True).encode() + b"\n"
