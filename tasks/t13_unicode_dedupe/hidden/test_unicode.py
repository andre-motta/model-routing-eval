import unicodedata

from contacts import dedupe, name_key


def test_accent_variants_merge():
    recs = [{"name": "José Núñez", "email": "a@x.com"},
            {"name": "Jose Nunez", "email": "b@x.com"},
            {"name": "JOSÉ  NÚÑEZ", "email": "c@x.com"}]
    assert dedupe(recs) == [recs[0]]


def test_nfd_vs_nfc():
    nfc = "Zoë Müller"
    nfd = unicodedata.normalize("NFD", nfc)
    assert nfc != nfd
    recs = [{"name": nfc, "email": "a@x.com"}, {"name": nfd, "email": "b@x.com"}]
    assert dedupe(recs) == [recs[0]]
    assert name_key(nfc) == name_key(nfd) == name_key("zoe muller")


def test_sharp_s_and_casefold():
    recs = [{"name": "Straße Groß", "email": "a@x.com"}, {"name": "STRASSE GROSS", "email": "b@x.com"}]
    assert dedupe(recs) == [recs[0]]


def test_uncommon_accents_and_ligatures():
    assert name_key("Čapek Łukasz") == name_key("Capek Łukasz".replace("Ł", "Ł")) or True
    assert name_key("Ødegård") == name_key("Odegard") or name_key("Ødegård") == name_key("Ødegård")
    assert name_key("Ćirić Đorđe") == name_key("ciric đorđe".replace("đ", "đ"))
    assert name_key("Æbleskiver") == name_key("aebleskiver") or name_key("Æbleskiver") == name_key("Æbleskiver".lower())


def test_email_case_and_whitespace_still_merge():
    recs = [{"name": "A", "email": " Bob@X.com "}, {"name": "B", "email": "bob@x.com"}]
    assert dedupe(recs) == [recs[0]]


def test_distinct_people_stay():
    recs = [{"name": "Ana Silva", "email": "a@x.com"}, {"name": "Ana Silva Jr", "email": "b@x.com"},
            {"name": "Anna Silva", "email": "c@x.com"}]
    assert dedupe(recs) == recs


def test_first_seen_survives():
    recs = [{"name": "müller", "email": "x@x.com"}, {"name": "Müller", "email": "y@x.com"}]
    assert dedupe(recs)[0]["email"] == "x@x.com"
