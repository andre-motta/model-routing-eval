from collections import defaultdict


def aggregate(rows):
    """Per (tenant, service): total cpu_seconds, total bytes_out, event count. Sorted by tenant then service."""
    acc = defaultdict(lambda: [0.0, 0, 0])
    for r in rows:
        a = acc[(r.tenant, r.service)]
        a[0] += r.cpu_seconds
        a[1] += r.bytes_out
        a[2] += 1
    return {k: tuple(v) for k, v in sorted(acc.items())}
