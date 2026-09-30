"""Deterministic role-isolated distances with inspectable fitted transformations."""

from collections import Counter

import numpy as np
from sklearn.decomposition import PCA

from football_intelligence.dna.features import eligibility
from football_intelligence.dna.registry import CORE, FAMILIES


class Representation:
    def __init__(
        self,
        features: list[str] | None = None,
        method: str = "euclidean",
        scaling: str = "robust",
        balanced: bool = True,
    ):
        self.features = features or CORE
        self.method = method
        self.scaling = scaling
        self.balanced = balanced

    def fit(self, x: np.ndarray):
        if not np.isfinite(x).all():
            raise ValueError("Missing or non-finite core features")
        self.lower = np.quantile(x, 0.01, axis=0) if self.scaling == "winsor" else None
        self.upper = np.quantile(x, 0.99, axis=0) if self.scaling == "winsor" else None
        work = np.clip(x, self.lower, self.upper) if self.lower is not None else x
        self.center = (
            np.mean(work, axis=0) if self.scaling == "standard" else np.median(work, axis=0)
        )
        self.scale = (
            np.std(work, axis=0)
            if self.scaling == "standard"
            else np.quantile(work, 0.75, axis=0) - np.quantile(work, 0.25, axis=0)
        )
        self.fallback = self.scale < 1e-10
        self.scale = np.where(self.fallback, np.std(work, axis=0), self.scale)
        self.active = self.scale >= 1e-10
        self.scale = np.where(self.active, self.scale, 1.0)
        groups = Counter(FAMILIES[f] for j, f in enumerate(self.features) if self.active[j])
        if not groups:
            raise ValueError("All features are constant")
        self.weights = (
            np.array(
                [
                    1 / (len(groups) * groups[FAMILIES[f]]) if self.active[j] else 0
                    for j, f in enumerate(self.features)
                ]
            )
            if self.balanced
            else self.active / self.active.sum()
        )
        z = self.standardize(work)
        self.pca = PCA(n_components=0.90, svd_solver="full") if self.method == "pca" else None
        if self.pca is not None:
            self.pca.fit(z * np.sqrt(self.weights))
        return self

    def standardize(self, x: np.ndarray) -> np.ndarray:
        if not np.isfinite(x).all():
            raise ValueError("Missing or non-finite core features")
        if self.lower is not None:
            x = np.clip(x, self.lower, self.upper)
        return (x - self.center) / self.scale * self.active

    def distances(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        za, zb = self.standardize(a), self.standardize(b)
        if self.pca is not None:
            za = self.pca.transform(za * np.sqrt(self.weights))
            zb = self.pca.transform(zb * np.sqrt(self.weights))
            return np.sqrt(np.maximum(0, ((za[:, None, :] - zb[None, :, :]) ** 2).sum(axis=2)))
        if self.method == "cosine":
            family_results = []
            for family in sorted(set(FAMILIES.values())):
                indexes = [
                    j
                    for j, f in enumerate(self.features)
                    if FAMILIES[f] == family and self.active[j]
                ]
                if not indexes:
                    continue
                x, y = za[:, indexes], zb[:, indexes]
                nx, ny = np.linalg.norm(x, axis=1), np.linalg.norm(y, axis=1)
                denom = nx[:, None] * ny[None, :]
                cosine = np.divide(x @ y.T, denom, out=np.zeros_like(denom), where=denom > 1e-12)
                distance = 1 - np.clip(cosine, -1, 1)
                distance[(nx[:, None] < 1e-12) & (ny[None, :] < 1e-12)] = 0
                family_results.append(distance)
            return np.mean(family_results, axis=0)
        return np.sqrt(
            np.maximum(0, ((za[:, None, :] - zb[None, :, :]) ** 2 * self.weights).sum(axis=2))
        )

    def metadata(self) -> dict:
        return dict(
            features=self.features,
            center=self.center.tolist(),
            scale=self.scale.tolist(),
            active=self.active.tolist(),
            std_fallback=self.fallback.tolist(),
            weights=self.weights.tolist(),
            scaling=self.scaling,
            method=self.method,
            clipping=None
            if self.lower is None
            else dict(
                lower=self.lower.tolist(),
                upper=self.upper.tolist() if self.upper is not None else [],
            ),
            pca=None
            if self.pca is None
            else dict(
                components=self.pca.components_.tolist(),
                mean=self.pca.mean_.tolist(),
                explained_variance_ratio=self.pca.explained_variance_ratio_.tolist(),
                n_components=int(self.pca.n_components_),
            ),
        )

    def explain(self, a: np.ndarray, b: np.ndarray) -> dict:
        if self.method != "euclidean":
            raise ValueError("Additive squared-distance explanation is for Euclidean only")
        delta = self.standardize(b[None, :])[0] - self.standardize(a[None, :])[0]
        squared = delta**2 * self.weights
        total = float(squared.sum())
        contributions: list[dict] = [
            dict(
                feature=f,
                standardized_difference=float(delta[j]),
                squared_contribution=float(squared[j]),
                share=float(squared[j] / total) if total else 0.0,
            )
            for j, f in enumerate(self.features)
        ]
        families = {
            family: sum(c["share"] for c in contributions if FAMILIES[c["feature"]] == family)
            for family in sorted(set(FAMILIES.values()))
        }
        usable = [c for j, c in enumerate(contributions) if self.active[j]]
        return dict(
            distance=math_sqrt(total),
            features=contributions,
            families=families,
            similar=[
                c["feature"]
                for c in sorted(
                    usable, key=lambda c: (abs(c["standardized_difference"]), c["feature"])
                )[:3]
            ],
            different=[
                c["feature"]
                for c in sorted(
                    usable, key=lambda c: (-abs(c["standardized_difference"]), c["feature"])
                )[:3]
            ],
        )


def math_sqrt(value: float) -> float:
    return float(np.sqrt(value))


def select(profiles: list[dict], threshold: int, minimum_role_players: int = 12) -> list[dict]:
    candidates = [p for p in profiles if not eligibility(p, threshold)]
    counts = Counter(p["primary_role"] for p in candidates)
    return sorted(
        [p for p in candidates if counts[p["primary_role"]] >= minimum_role_players],
        key=lambda p: p["player_id"],
    )


def matrix(
    profiles: list[dict], features: list[str] | None = None, context: bool = False
) -> np.ndarray:
    replacements = (
        {
            "pressures_per90": "pressures_per100_opponent",
            "interceptions_per90": "interceptions_per100_opponent",
            "progressive_passes_per90": "progressive_passes_per100_team",
        }
        if context
        else {}
    )
    x = np.array(
        [[p["values"][replacements.get(f, f)] for f in (features or CORE)] for p in profiles],
        dtype=float,
    )
    if not np.isfinite(x).all():
        raise ValueError("Missing required feature in comparison cohort")
    return x


def topk(
    distances: np.ndarray, ids: list[str], k: int = 10, exclude_self: bool = True
) -> list[list[int]]:
    result = []
    for i, row in enumerate(distances):
        candidates = [j for j in range(len(ids)) if not exclude_self or i != j]
        result.append(sorted(candidates, key=lambda j: (row[j], ids[j]))[:k])
    return result


def percentile(values: np.ndarray, value: float) -> float:
    return float(100 * (np.sum(values < value) + 0.5 * np.sum(values == value)) / len(values))
