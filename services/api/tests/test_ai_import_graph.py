"""S56/S93: ai_gateway must not import referee or learner_model modules, and vice versa."""

from __future__ import annotations

import ast
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1] / "app"
GATEWAY = API_ROOT / "modules" / "ai_gateway"
LEARNER_MODEL = API_ROOT / "modules" / "learner_model"
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
LEARNER_MODEL_IMPORTS = {
    "app.modules.learner_model",
    "app.modules.learner_model.effort",
    "modules.learner_model",
    "modules.learner_model.effort",
}
GATEWAY_IMPORTS = {
    "app.modules.ai_gateway",
    "app.modules.ai_gateway.service",
    "modules.ai_gateway",
    "modules.ai_gateway.service",
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


def _starts_with_any(mod: str, prefixes: set[str]) -> bool:
    return any(mod == prefix or mod.startswith(prefix + ".") for prefix in prefixes)


def test_ai_gateway_import_graph() -> None:
    for path in GATEWAY.rglob("*.py"):
        mods = _imports(path)
        overlap = mods & REFEREE
        assert not overlap, f"{path} imports referee modules: {overlap}"
        learner_hits = {mod for mod in mods if _starts_with_any(mod, LEARNER_MODEL_IMPORTS)}
        assert not learner_hits, f"{path} imports learner_model: {learner_hits}"

    for name in ("evidence.py", "grading.py", "reviews.py", "planner.py"):
        path = API_ROOT / "modules" / "learning" / name
        if not path.is_file():
            continue
        mods = _imports(path)
        assert not any(mod.startswith("app.modules.ai_gateway") for mod in mods), path
        assert not any(mod.startswith("modules.ai_gateway") for mod in mods), path

    assert LEARNER_MODEL.is_dir(), "learner_model package missing"
    for path in LEARNER_MODEL.rglob("*.py"):
        mods = _imports(path)
        gateway_hits = {mod for mod in mods if _starts_with_any(mod, GATEWAY_IMPORTS)}
        assert not gateway_hits, f"{path} imports ai_gateway: {gateway_hits}"
        referee_hits = mods & REFEREE
        assert not referee_hits, f"{path} imports referee modules: {referee_hits}"
