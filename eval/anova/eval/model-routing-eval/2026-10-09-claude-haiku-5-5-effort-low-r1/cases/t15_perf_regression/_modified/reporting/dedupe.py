"""Drop duplicate events (the collector retries, so the same event_id can appear several times).

Keeps insertion order of first occurrence. Membership is checked against a set, so this is
linear in the number of rows; a list here made it quadratic.
"""


def dedupe_rows(rows):
    seen_ids = set()
    out = []
    for r in rows:
        if r.event_id in seen_ids:
            continue
        seen_ids.add(r.event_id)
        out.append(r)
    return out
