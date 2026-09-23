"""S56: ai_gateway must not import referee modules, and vice versa."""

from __future__ import annotations

import ast
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1] / "app"
GATEWAY = API_ROOT / "modules" / "ai_gateway"
REFEREE = {
    "app.modules.learning.evidence",
    "app.modules.learning.grading",
    "app.modules.learning.reviews",
    "app.modules.learning.planner",
    "modules.learning.evidence",
    "modules.learning.grading",
    "modules.learning.reviews",
    "modules.learning.planner",
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_ai_gateway_import_graph() -> None:
    for path in GATEWAY.rglob("*.py"):
        mods = _imports(path)
        overlap = mods & REFEREE
        assert not overlap, f"{path} imports referee modules: {overlap}"

    for name in ("evidence.py", "grading.py", "reviews.py", "planner.py"):
        path = API_ROOT / "modules" / "learning" / name
        if not path.is_file():
            continue
        mods = _imports(path)
        assert not any(mod.startswith("app.modules.ai_gateway") for mod in mods), path
        assert not any(mod.startswith("modules.ai_gateway") for mod in mods), path
