import pathlib
import random
import time

from reporting import UsageRow, build_report, dedupe_rows


def _rows(n, dup_every=7):
    rnd = random.Random(3)
    rows = []
    for i in range(n):
        eid = f"e{i}" if i % dup_every else f"e{i - 1}"
        rows.append(UsageRow(eid, f"t{rnd.randint(0, 50)}", rnd.choice(["api", "web", "db"]), rnd.random(), rnd.randint(0, 999)))
    return rows


def test_dedupe_keeps_first_occurrence_order():
    rows = [UsageRow("a", "t", "s", 1, 1), UsageRow("b", "t", "s", 2, 2), UsageRow("a", "t", "s", 3, 3)]
    assert [r.cpu_seconds for r in dedupe_rows(rows)] == [1, 2]


def test_large_input_is_fast_and_correct():
    rows = _rows(60_000)
    t0 = time.perf_counter()
    rep = build_report(rows)
    elapsed = time.perf_counter() - t0
    assert elapsed < 3.0, f"build_report took {elapsed:.1f}s on 60k rows"
    # independent reference
    seen, uniq = set(), []
    for r in rows:
        if r.event_id not in seen:
            seen.add(r.event_id); uniq.append(r)
    assert rep[-1]["events"] == len(uniq)
    assert rep[-1]["bytes_out"] == sum(r.bytes_out for r in uniq)


def test_regression_test_added():
    tests = pathlib.Path(__file__).resolve().parent.parent / "tests"
    src = "\n".join(p.read_text() for p in tests.glob("test_*.py"))
    assert src.count("def test_") >= 2, "expected a new regression test under tests/"
    # Any shape of regression test is fine: a timing bound, an operation-count budget, or a large-input run.
    assert any(k in src for k in ("perf_counter", "time", "timeout", "benchmark", "comparisons", "count", "range(")), src[-400:]
