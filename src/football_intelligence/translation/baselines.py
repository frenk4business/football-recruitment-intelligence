"""Registered deterministic baselines with empirical out-of-fold prediction ranges."""

import hashlib
import math

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

METHODS = ("unchanged_source", "role_mean", "ridge")


def rate(row: dict, side: str, target: str) -> float:
    e = row[side]
    return 90 * e["counts"][target] / e["reliable_minutes"]


class Baseline:
    def __init__(self, method: str, target: str):
        if method not in METHODS:
            raise ValueError("Unknown baseline")
        self.method, self.target = method, target

    def matrix(self, rows: list[dict]) -> np.ndarray:
        return np.array(
            [
                [
                    rate(r, "source", self.target),
                    math.log(r["source_minutes"] / 900),
                    math.log(r["source_context"]["passes_per90"]),
                    math.log(r["target_context"]["passes_per90"]),
                    r["context_log_ratio"],
                    float(r["role_change"] != "same"),
                ]
                + [float(r[side + "_role"] == role) for side, role in self.categories]
                for r in rows
            ]
        )

    def fit(self, rows: list[dict]):
        self.mean = sum(r["destination"]["counts"][self.target] for r in rows) / sum(
            r["destination_minutes"] / 90 for r in rows
        )
        self.role_means = {
            role: sum(
                r["destination"]["counts"][self.target]
                for r in rows
                if r["destination_role"] == role
            )
            / sum(r["destination_minutes"] / 90 for r in rows if r["destination_role"] == role)
            for role in sorted({r["destination_role"] for r in rows})
        }
        self.categories = [
            (side, role)
            for side in ("source", "destination")
            for role in sorted({r[side + "_role"] for r in rows})
        ]
        if self.method == "ridge":
            self.scaler = StandardScaler().fit(self.matrix(rows))
            self.model = Ridge(alpha=10).fit(
                self.scaler.transform(self.matrix(rows)),
                np.array([rate(r, "destination", self.target) for r in rows]),
            )
        return self

    def predict(self, rows: list[dict]) -> np.ndarray:
        if self.method == "unchanged_source":
            return np.array([rate(r, "source", self.target) for r in rows])
        if self.method == "role_mean":
            return np.array([self.role_means.get(r["destination_role"], self.mean) for r in rows])
        return np.maximum(0, self.model.predict(self.scaler.transform(self.matrix(rows))))

    def fit_residuals(self, rows: list[dict]):
        folds = {
            r["player_id"]: int(hashlib.sha256(r["player_id"].encode()).hexdigest(), 16) % 5
            for r in rows
        }
        residuals = []
        for fold in range(5):
            train = [r for r in rows if folds[r["player_id"]] != fold]
            test = [r for r in rows if folds[r["player_id"]] == fold]
            if not test or not train:
                continue
            pred = Baseline(self.method, self.target).fit(train).predict(test)
            residuals.extend(np.array([rate(r, "destination", self.target) for r in test]) - pred)
        self.residuals = np.array(residuals) - np.mean(residuals)
        return self.fit(rows)

    def predictive(self, rows: list[dict]) -> np.ndarray:
        return np.maximum(0, self.predict(rows)[None, :] + self.residuals[:, None])

    def metadata(self) -> dict:
        return dict(
            method=self.method,
            target=self.target,
            role_means=self.role_means,
            population_mean=self.mean,
            interval_method="centred_player_out_of_fold_empirical_residuals",
            residual_count=len(self.residuals),
            ridge_alpha=10 if self.method == "ridge" else None,
            nonnegative_boundary=True,
        )
