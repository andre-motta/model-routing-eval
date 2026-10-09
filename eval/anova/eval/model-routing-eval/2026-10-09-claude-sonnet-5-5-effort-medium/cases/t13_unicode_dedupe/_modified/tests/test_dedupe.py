from contacts import dedupe


def test_accent_variants_merge():
    recs = [{"name": "José Núñez", "email": "a@x.com"},
            {"name": "Jose Nunez", "email": "b@x.com"},
            {"name": "JOSÉ  NÚÑEZ", "email": "c@x.com"}]
    assert dedupe(recs) == [recs[0]]


def test_nfd_and_eszett_merge():
    recs = [{"name": "José Strauß", "email": "a@x.com"},
            {"name": "José Strauss", "email": "b@x.com"},
            {"name": "JOSE STRAUSS", "email": "A@X.COM"}]
    assert dedupe(recs) == [recs[0]]
