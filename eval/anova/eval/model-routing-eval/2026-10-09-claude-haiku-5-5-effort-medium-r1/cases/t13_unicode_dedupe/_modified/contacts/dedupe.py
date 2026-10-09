import re
import unicodedata

_WS = re.compile(r"\s+")


def _fold_marks(s):
    """Decompose (NFKD) and drop combining marks and format characters.

    NFKD makes NFC (Windows) and NFD (macOS) input compare equal, and removing
    combining marks strips accents for any script, not just a fixed list.
    Format characters (category Cf) such as zero-width spaces are dropped too.
    """
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s
                   if not unicodedata.combining(c) and unicodedata.category(c) != "Cf")


def email_key(email):
    return unicodedata.normalize("NFC", email.strip()).casefold()


def name_key(name):
    """Key for matching names: case-folded, single spaces, no accents."""
    s = _fold_marks(name).casefold()
    # casefold can introduce marks (e.g. "İ" -> "i" + U+0307), so fold again
    s = _fold_marks(s)
    return _WS.sub(" ", s).strip()


def dedupe(records):
    """records: list of dicts with 'name' and 'email'. Returns survivors in first-seen order.

    A record is dropped if its name or email key matches any earlier record,
    including records that were themselves dropped. Matching is therefore
    transitive, so each record's keys are added to the seen set either way.
    """
    seen, out = set(), []
    for r in records:
        keys = {("name", name_key(r["name"])), ("email", email_key(r["email"]))}
        if not keys & seen:
            out.append(r)
        seen |= keys
    return out
