import re
import unicodedata

_WS = re.compile(r"\s+")


def email_key(email):
    return email.strip().lower()


def name_key(name):
    """Key for matching names: case-folded, single spaces, no accents.

    Normalises to NFKD so precomposed (Windows) and decomposed (Mac) forms
    agree, drops combining marks, and case-folds so "ß" matches "ss".
    """
    s = unicodedata.normalize("NFKD", name.casefold())
    s = "".join(c for c in s if not unicodedata.combining(c))
    # casefold again: NFKD can expose characters that fold further
    return _WS.sub(" ", s.strip()).casefold()


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
