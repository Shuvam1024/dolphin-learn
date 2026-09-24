"""CLI: python -m app.content.validate"""

from __future__ import annotations

import sys
from pathlib import Path

from app.content.loader import DEFAULT_CONTENT_ROOT, errors_only, validate_all


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0]) if args else DEFAULT_CONTENT_ROOT
    failures = validate_all(root)
    errors = errors_only(failures)
    warnings = [item for item in failures if item not in errors]
    for item in warnings:
        print(f"{item.path}:{item.line}: warning [{item.rule}] {item.message}")
    for item in errors:
        print(f"{item.path}:{item.line}: [{item.rule}] {item.message}")
    if errors:
        return 1
    if warnings:
        print(f"content ok with {len(warnings)} warning(s): {root}")
    else:
        print(f"content ok: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
