"""Recompute Phase 4 without rewriting the registered research evidence.

Requires the pinned WSL cohort cache; `make phase4-build` materializes it.
No evaluation selection is repeated and final outcomes cannot select a method.
"""

import hashlib
import json
from pathlib import Path

from football_intelligence.recruitment.evaluation import evaluate
from football_intelligence.recruitment.robustness import analyze

ROOT = Path(__file__).resolve().parents[1]


def equivalent(actual, expected, path="root"):
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys(), path
        for key in expected:
            if key != "code_commit":
                equivalent(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(expected, list):
        assert len(actual) == len(expected), path
        for i, value in enumerate(expected):
            equivalent(actual[i], value, f"{path}[{i}]")
    elif isinstance(expected, float):
        assert abs(actual - expected) <= 1e-10, (path, actual, expected)
    else:
        assert actual == expected, (path, actual, expected)


def main():
    base = ROOT / "artifacts/phase4"
    paths = [base / f"{stage}_evaluation.json" for stage in ("development", "final")]
    paths += [base / "robustness.json", base / "method_selection.json"]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    for stage in ("development", "final"):
        expected = json.loads((base / f"{stage}_evaluation.json").read_text())
        equivalent(evaluate(ROOT, stage, persist=False), expected)
        print(
            f"{stage}: all per-query results and summaries reproduced (1e-10 tolerance)", flush=True
        )
    equivalent(analyze(ROOT, persist=False), json.loads((base / "robustness.json").read_text()))
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    print(
        "205 robustness scenarios reproduced; frozen evidence and selection unchanged.", flush=True
    )


if __name__ == "__main__":
    main()
