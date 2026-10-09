import re
import unicodedata

_WS = re.compile(r"\s+")


def email_key(email):
    return email.strip().lower()


def name_key(name):
    """Key for matching names: case-folded, single spaces, no accents.

    NFKD splits precomposed letters (macOS often stores "é" as "e" + U+0301,
    Windows as one code point), so dropping combining marks removes accents
    regardless of which form was typed. casefold() maps "ß" to "ss".
    """
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return _WS.sub(" ", s.casefold()).strip()


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
