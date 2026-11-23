import argparse
import json

from blindmath.data.audit import audit_paths


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    a = ap.parse_args(argv)
    rep = audit_paths(a.paths)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 1 if rep["flagged"] else 0
