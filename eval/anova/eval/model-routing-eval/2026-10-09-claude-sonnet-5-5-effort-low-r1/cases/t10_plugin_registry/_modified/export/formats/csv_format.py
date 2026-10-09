import csv
import io

from ..base import Exporter
from ..registry import register


@register
class CsvExporter(Exporter):
    name = "csv"
    extension = ".csv"

    def dump(self, records):
        buf = io.StringIO()
        if records:
            w = csv.DictWriter(buf, fieldnames=list(records[0].keys()), lineterminator="\n")
            w.writeheader()
            w.writerows(records)
        return buf.getvalue().encode()
