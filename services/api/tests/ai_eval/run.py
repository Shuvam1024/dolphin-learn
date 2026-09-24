"""CLI entry: python -m tests.ai_eval.run"""

from __future__ import annotations

import os
import sys

from tests.ai_eval import run_all, write_live_stub


def main() -> int:
    report = run_all()
    failed = False
    for prompt_id, row in report.items():
        status = "ok" if not row["failed"] else "FAIL"
        print(f"{prompt_id}: {row['passed']}/{row['total']} {status}")
        if row["failed"]:
            failed = True
            print("  ", ", ".join(row["failed"]))
    if os.environ.get("AI_EVAL_LIVE") == "1" or os.environ.get("AI_EVAL_RECORD") == "1":
        path = write_live_stub(report)
        print(f"wrote {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
