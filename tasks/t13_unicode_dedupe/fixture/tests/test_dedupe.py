from contacts import dedupe


def test_accent_variants_merge():
    recs = [{"name": "José Núñez", "email": "a@x.com"},
            {"name": "Jose Nunez", "email": "b@x.com"},
            {"name": "JOSÉ  NÚÑEZ", "email": "c@x.com"}]
    assert dedupe(recs) == [recs[0]]
