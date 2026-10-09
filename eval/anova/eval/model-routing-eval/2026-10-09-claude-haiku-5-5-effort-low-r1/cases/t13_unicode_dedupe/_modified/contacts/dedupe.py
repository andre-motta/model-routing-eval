import re
import unicodedata

_WS = re.compile(r"\s+")


def email_key(email):
    return email.strip().casefold()


def name_key(name):
    """Key for matching names: casefolded, single spaces, no accents.

    Casefold before decomposing so that "ß" becomes "ss" and uppercase
    accented letters are reduced to their base letter. NFKD splits both
    precomposed (Windows) and decomposed (Mac) accents into base letter plus
    combining mark, and the combining marks are then dropped.
    """
    s = unicodedata.normalize("NFKD", name.casefold())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return _WS.sub(" ", s).strip()


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
