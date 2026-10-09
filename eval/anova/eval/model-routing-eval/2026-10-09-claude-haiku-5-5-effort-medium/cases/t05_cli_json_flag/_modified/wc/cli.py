import argparse
import json
import sys


def count(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return {"lines": text.count("\n"), "words": len(text.split()), "chars": len(text)}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wc")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true", help="print one JSON object")
    args = ap.parse_args(argv)
    total = {"lines": 0, "words": 0, "chars": 0}
    results = []
    rc = 0
    for path in args.files:
        try:
            c = count(path)
        except OSError as e:
            print(f"wc: {path}: {e.strerror}", file=sys.stderr)
            rc = 1
            continue
        results.append({"path": path, **c})
        if not args.json:
            print(f"{c['lines']:>8}{c['words']:>8}{c['chars']:>8} {path}")
        for k in total:
            total[k] += c[k]
    if args.json:
        print(json.dumps({"files": results, "total": total}))
    elif len(args.files) > 1:
        print(f"{total['lines']:>8}{total['words']:>8}{total['chars']:>8} total")
    return rc
