from xml.sax.saxutils import escape

from ..base import Exporter
from ..registry import register


@register
class XmlExporter(Exporter):
    name = "xml"
    extension = ".xml"

    def dump(self, records):
        parts = ["<records>"]
        for r in records:
            parts.append("  <record>")
            for k, v in r.items():
                parts.append(f"    <{k}>{escape(str(v))}</{k}>")
            parts.append("  </record>")
        parts.append("</records>")
        return ("\n".join(parts) + "\n").encode()
