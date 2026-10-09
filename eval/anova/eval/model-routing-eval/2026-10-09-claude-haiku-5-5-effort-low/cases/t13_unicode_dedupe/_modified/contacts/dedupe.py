import re
import unicodedata

_WS = re.compile(r"\s+")


def email_key(email):
    return unicodedata.normalize("NFKC", email).strip().casefold()


def name_key(name):
    """Key for matching names: casefolded, single spaces, no accents.

    NFKD splits precomposed characters (macOS sends NFD, Windows NFC) into
    base letter plus combining marks, which are then dropped. casefold() maps
    "ß" to "ss" and handles other case pairs that lower() misses.
    """
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
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
