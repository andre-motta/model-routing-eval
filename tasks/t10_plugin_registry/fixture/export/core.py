import csv
import io
import json
from xml.sax.saxutils import escape


class UnknownFormat(ValueError):
    pass


def _extension(fmt):
    if fmt == "csv":
        return ".csv"
    elif fmt == "json":
        return ".json"
    elif fmt == "xml":
        return ".xml"
    raise UnknownFormat(fmt)


def export_records(records, fmt):
    """records: list of dicts with identical keys. Returns bytes."""
    if fmt == "csv":
        buf = io.StringIO()
        if records:
            w = csv.DictWriter(buf, fieldnames=list(records[0].keys()), lineterminator="\n")
            w.writeheader()
            w.writerows(records)
        return buf.getvalue().encode()
    elif fmt == "json":
        return json.dumps(records, indent=2, sort_keys=True).encode() + b"\n"
    elif fmt == "xml":
        parts = ["<records>"]
        for r in records:
            parts.append("  <record>")
            for k, v in r.items():
                parts.append(f"    <{k}>{escape(str(v))}</{k}>")
            parts.append("  </record>")
        parts.append("</records>")
        return ("\n".join(parts) + "\n").encode()
    raise UnknownFormat(fmt)


def export_to_file(records, fmt, path):
    if fmt not in ("csv", "json", "xml"):
        raise UnknownFormat(fmt)
    path = str(path)
    if not path.endswith(_extension(fmt)):
        path += _extension(fmt)
    with open(path, "wb") as f:
        f.write(export_records(records, fmt))
    return path
