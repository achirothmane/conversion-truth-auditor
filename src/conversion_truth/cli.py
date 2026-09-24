from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import audit
from .report import write_html


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="conversion-truth",
        description="Reconcile GA4 purchases against real business outcomes.",
    )
    parser.add_argument("--truth", required=True, help="Path to truth CSV")
    parser.add_argument("--ga4", required=True, help="Path to GA4 CSV")
    parser.add_argument("--json", dest="json_path", help="Write full report JSON to this path")
    parser.add_argument("--html", dest="html_path", help="Write human-readable HTML report to this path")
    args = parser.parse_args()

    report = audit(args.truth, args.ga4)
    print(json.dumps({"decision": report["decision"], "summary": report["summary"]}, indent=2))
    if args.json_path:
        Path(args.json_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.html_path:
        write_html(report, args.html_path)


if __name__ == "__main__":
    main()
