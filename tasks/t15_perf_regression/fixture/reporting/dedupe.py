"""Drop duplicate events (the collector retries, so the same event_id can appear several times).

Refactored to keep insertion order of first occurrence, which the old set-based version did not guarantee.
"""


def dedupe_rows(rows):
    seen_ids = []
    out = []
    for r in rows:
        if r.event_id in seen_ids:
            continue
        seen_ids.append(r.event_id)
        out.append(r)
    return out
