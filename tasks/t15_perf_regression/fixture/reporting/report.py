from .dedupe import dedupe_rows
from .aggregate import aggregate


def build_report(rows):
    """Returns list of dicts, one per (tenant, service), plus a totals row at the end."""
    rows = dedupe_rows(rows)
    agg = aggregate(rows)
    out = []
    tot_cpu, tot_bytes, tot_n = 0.0, 0, 0
    for (tenant, service), (cpu, byts, n) in agg.items():
        out.append({"tenant": tenant, "service": service, "cpu_seconds": round(cpu, 3), "bytes_out": byts, "events": n})
        tot_cpu += cpu; tot_bytes += byts; tot_n += n
    out.append({"tenant": "*", "service": "*", "cpu_seconds": round(tot_cpu, 3), "bytes_out": tot_bytes, "events": tot_n})
    return out
