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
    ap.add_argument("--json", action="store_true", help="print a JSON object instead of text")
    args = ap.parse_args(argv)
    total = {"lines": 0, "words": 0, "chars": 0}
    rc = 0
    files = []
    for path in args.files:
        try:
            c = count(path)
        except OSError as e:
            print(f"wc: {path}: {e.strerror}", file=sys.stderr)
            rc = 1
            continue
        if not args.json:
            print(f"{c['lines']:>8}{c['words']:>8}{c['chars']:>8} {path}")
        files.append({"path": path, **c})
        for k in total:
            total[k] += c[k]
    if args.json:
        print(json.dumps({"files": files, "total": total}))
    elif len(args.files) > 1:
        print(f"{total['lines']:>8}{total['words']:>8}{total['chars']:>8} total")
    return rc
