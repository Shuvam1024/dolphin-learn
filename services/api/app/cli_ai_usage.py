"""Write docs/evaluations/ai-usage.md from in-process metrics (S102)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from app.observability import metrics_snapshot


def write_ai_usage(path: Path | None = None) -> Path:
    target = path or (
        Path(__file__).resolve().parents[3] / "docs" / "evaluations" / "ai-usage.md"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    snap = metrics_snapshot()
    lines = [
        f"# AI usage — {date.today().isoformat()}",
        "",
        "Daily summary of gateway metrics (no learner data).",
        "",
    ]
    if not snap:
        lines.append("No AI calls recorded in this process yet.")
    for prompt_id, row in sorted(snap.items()):
        lines.append(
            f"- **{prompt_id}**: calls={row['calls']} p95={row['p95_latency_ms']}ms "
            f"fallback={row['fallback_rate']:.0%} reject={row['validator_rejection_rate']:.0%} "
            f"tokens_in={row['tokens_in']} tokens_out={row['tokens_out']}"
        )
    lines.append("")
    target.write_text("\n".join(lines))
    return target


def main() -> None:
    path = write_ai_usage()
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
