from reporting import parse_rows, build_report


def test_small_report():
    rows = parse_rows(["e1,acme,api,1.5,100", "e2,acme,api,0.5,50", "e2,acme,api,0.5,50", "e3,beta,web,2,10"])
    rep = build_report(rows)
    assert rep[0] == {"tenant": "acme", "service": "api", "cpu_seconds": 2.0, "bytes_out": 150, "events": 2}
    assert rep[-1]["events"] == 3
