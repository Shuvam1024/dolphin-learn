"""CLI: python -m app.content.validate"""

from __future__ import annotations

import sys
from pathlib import Path

from app.content.loader import DEFAULT_CONTENT_ROOT, validate_all


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0]) if args else DEFAULT_CONTENT_ROOT
    failures = validate_all(root)
    if not failures:
        print(f"content ok: {root}")
        return 0
    for item in failures:
        print(f"{item.path}:{item.line}: [{item.rule}] {item.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
