import csv
import io

from ..registry import Exporter, register


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
