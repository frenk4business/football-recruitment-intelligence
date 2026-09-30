"""Validate explicit publication contracts; lazy per-player top-k artifacts only."""

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA

from football_intelligence.data.fetch import digest
from football_intelligence.dna.cohort import COHORT, local_cohort, settings
from football_intelligence.dna.cohort import write as write_report
from football_intelligence.dna.contracts import (
    DNAEvaluation,
    DNAEvaluationRow,
    DNAFeatureValue,
    DNAIndex,
    DNAMap,
    DNAMapPoint,
    DNANeighbor,
    DNAProfile,
)
from football_intelligence.dna.registry import CORE, DNA_VERSION, FAMILIES, REGISTRY, VERSION
from football_intelligence.dna.similarity import Representation, matrix, percentile, select, topk

DEFAULT_METHOD = "standard_scaling"


def write(path: Path, value):
    # Compact derived JSON lowers repository, deployment and request payload size.
    def rounded(v):
        if isinstance(v, float):
            return round(v, 8)
        if isinstance(v, dict):
            return {k: rounded(x) for k, x in v.items()}
        if isinstance(v, list):
            return [rounded(x) for x in v]
        return v

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(rounded(value), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    )


def publish(root: Path, name: str = COHORT) -> dict:
    cfg = settings(root)
    directory = local_cohort(root, name)
    profiles = json.loads((directory / "player_profiles.json").read_text())
    eligibility = json.loads((root / "artifacts/phase2/cohort_eligibility.json").read_text())
    evaluation = json.loads((root / "artifacts/phase2/similarity_evaluation.json").read_text())
    stability = json.loads((directory / "stability.json").read_text())
    if not eligibility["complete"]:
        raise ValueError("Cannot publish an incomplete season as the analytical cohort")
    target = root / "artifacts/phase2/public"
    staging = root / "data/interim/dna-public"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    excluded = {
        t: {p["player_id"]: p["reasons"] for p in info["excluded"]}
        for t, info in eligibility["thresholds"].items()
    }

    def summary(p):
        keys = [
            "player_id",
            "name",
            "teams",
            "competition",
            "season",
            "primary_role",
            "secondary_role",
            "role_shares",
            "multi_role",
            "minutes",
            "appearances",
            "unreliable_appearances",
        ]
        return {
            **{k: p[k] for k in keys},
            "eligibility": {
                str(t): excluded[str(t)].get(p["player_id"], []) for t in cfg["thresholds"]
            },
        }

    index = DNAIndex(
        version=DNA_VERSION,
        cohort=name,
        competition=eligibility["competition"],
        season=eligibility["season"],
        thresholds=cfg["thresholds"],
        default_threshold=cfg["default_threshold"],
        matches=eligibility["matches"],
        players=[summary(p) for p in sorted(profiles, key=lambda p: (p["name"], p["player_id"]))],
    )
    write(staging / "index.json", index.model_dump())
    write(staging / "features.json", [f.model_dump() for f in REGISTRY])
    models = {}
    for threshold in cfg["thresholds"]:
        selected = select(profiles, threshold, cfg["minimum_role_players"])
        model_by_role = {}
        data_by_id = {}
        model_rows = []
        for role in sorted({p["primary_role"] for p in selected}):
            group = [p for p in selected if p["primary_role"] == role]
            x = matrix(group)
            model = Representation(scaling="standard").fit(x)
            model_by_role[role] = (group, x, model)
            distances = model.distances(x, x)
            order = topk(distances, [p["player_id"] for p in group], 10)
            for i, p in enumerate(group):
                data_by_id[p["player_id"]] = (i, order[i], distances[i])
            model_rows.append(dict(role=role, **model.metadata()))
        models[str(threshold)] = model_rows
        map_values = []
        for p in profiles:
            reasons = excluded[str(threshold)].get(p["player_id"], [])
            values = [dict(id=f.id, value=p["values"][f.id], percentile=None) for f in REGISTRY]
            neighbors = []
            scaled = None
            comparison_size = 0
            if not reasons:
                group, x, model = model_by_role[p["primary_role"]]
                comparison_size = len(group)
                i, neighbor_order, distances = data_by_id[p["player_id"]]
                scaled = model.standardize(x[i : i + 1])[0].tolist()
                map_values.append((p, np.array(scaled) * np.sqrt(model.weights)))
                for v in values:
                    distribution = np.array(
                        [q["values"][v["id"]] for q in group if q["values"][v["id"]] is not None]
                    )
                    v["percentile"] = (
                        percentile(distribution, v["value"]) if v["value"] is not None else None
                    )
                for rank, j in enumerate(neighbor_order, 1):
                    other = group[j]
                    explanation = model.explain(x[i], x[j])
                    neighbors.append(
                        dict(
                            player_id=other["player_id"],
                            name=other["name"],
                            teams=other["teams"],
                            role=other["primary_role"],
                            minutes=other["minutes"],
                            rank=rank,
                            distance=float(distances[j]),
                            stability=stability[str(threshold)][p["player_id"]]["inclusion"].get(
                                other["player_id"], 0
                            ),
                            similar=explanation["similar"],
                            different=explanation["different"],
                            contributions=explanation["features"],
                            family_contributions=explanation["families"],
                        )
                    )
            detail = DNAProfile(
                player=summary(p),
                cohort=name,
                threshold=threshold,
                eligible=not reasons,
                exclusions=reasons,
                comparison_size=comparison_size,
                features=[DNAFeatureValue.model_validate(v) for v in values],
                scaled_vector=scaled,
                neighbors=[DNANeighbor.model_validate(v) for v in neighbors],
                neighbor_jaccard=stability[str(threshold)].get(p["player_id"], {}).get("jaccard"),
                bootstrap_samples=cfg["bootstrap_samples"],
                bins=p["bins"],
            )
            write(staging / str(threshold) / f"{p['player_id']}.json", detail.model_dump())
        projection = PCA(n_components=2, svd_solver="full")
        coords = projection.fit_transform(np.array([x for _, x in map_values]))
        points = [
            dict(
                player_id=p["player_id"],
                name=p["name"],
                teams=p["teams"],
                role=p["primary_role"],
                minutes=p["minutes"],
                x=float(coords[i, 0]),
                y=float(coords[i, 1]),
            )
            for i, (p, _) in enumerate(map_values)
        ]
        view = DNAMap(
            threshold=threshold,
            method="PCA",
            explained_variance=projection.explained_variance_ratio_.tolist(),
            points=[DNAMapPoint.model_validate(v) for v in points],
        )
        write(staging / f"map-{threshold}.json", view.model_dump())
    rows = []
    for threshold, result in evaluation["thresholds"].items():
        for method, values in result["methods"].items():
            r = values["retrieval"]
            rows.append(
                dict(
                    method=method,
                    threshold=int(threshold),
                    eligible=result["eligible"],
                    queries=r["queries"],
                    recall1=r["recall1"],
                    recall5=r["recall5"],
                    recall10=r["recall10"],
                    mrr=r["mrr"],
                    bootstrap_jaccard=values["bootstrap_jaccard"],
                    random_recall5=r["random_expectation"]["recall5"],
                )
            )
    public_evaluation = DNAEvaluation(
        version=evaluation["version"],
        default_method=DEFAULT_METHOD,
        bootstrap_samples=cfg["bootstrap_samples"],
        seed=cfg["seed"],
        rows=[DNAEvaluationRow.model_validate(v) for v in rows],
    )
    write(staging / "evaluation.json", public_evaluation.model_dump())
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(staging, target)
    manifest = dict(
        version=DNA_VERSION,
        feature_registry_version=VERSION,
        cohort=name,
        source_revision=eligibility["source_revision"],
        minimum_minutes=cfg["default_threshold"],
        thresholds=cfg["thresholds"],
        role_grouping="Original roles, no merging; GK excluded; at least 12 eligible members",
        scaling_method="Role-specific mean / population standard deviation; constant features omitted; no clipping",
        similarity_method="Euclidean: square root of mean of within-family mean squared standardized differences",
        family_weights={f: 0.2 for f in sorted(set(FAMILIES.values()))},
        default_method=DEFAULT_METHOD,
        seed=cfg["seed"],
        bootstrap_samples=cfg["bootstrap_samples"],
        scalers=models,
        features=CORE,
        generated_at=datetime.now(UTC).isoformat(),
        public_sha256={
            str(p.relative_to(target)): digest(p.read_bytes())
            for p in sorted(target.rglob("*.json"))
        },
        evaluation_metrics=evaluation["thresholds"][str(cfg["default_threshold"])]["methods"][
            DEFAULT_METHOD
        ],
    )
    write_report(root / "artifacts/phase2/model_manifest.json", manifest)
    return manifest
