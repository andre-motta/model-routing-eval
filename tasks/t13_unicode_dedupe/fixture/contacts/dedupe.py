import re

_WS = re.compile(r"\s+")


def email_key(email):
    return email.strip().lower()


def name_key(name):
    """Key for matching names: lower-case, single spaces, no accents."""
    s = _WS.sub(" ", name.strip()).lower()
    # strip common accents
    for a, b in (("é", "e"), ("è", "e"), ("á", "a"), ("ó", "o"), ("ü", "u"), ("ö", "o"), ("ä", "a"), ("ñ", "n")):
        s = s.replace(a, b)
    return s


def dedupe(records):
    """records: list of dicts with 'name' and 'email'. Returns survivors in first-seen order."""
    seen_names, seen_emails, out = set(), set(), []
    for r in records:
        nk, ek = name_key(r["name"]), email_key(r["email"])
        if nk in seen_names or ek in seen_emails:
            continue
        seen_names.add(nk)
        seen_emails.add(ek)
        out.append(r)
    return out
