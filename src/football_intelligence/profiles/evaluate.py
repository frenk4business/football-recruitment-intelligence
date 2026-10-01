"""Preregistered descriptive harmonisation checks; no transfer or recruitment model."""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import ks_2samp, wasserstein_distance
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from football_intelligence.profiles.aggregate import aggregate, load_observations, split_profiles
from football_intelligence.profiles.cache import write_json
from football_intelligence.profiles.features import COMMON_IDS, COUNT_KEYS, values

METHODS = ("raw", "shared", "provider_global", "provider_role")


def vector(profile: dict) -> np.ndarray:
    return np.array([profile["common"][key] for key in COMMON_IDS], dtype=float)


def scaler_key(profile: dict, method: str) -> str:
    if method == "provider_global":
        return profile["provider"]
    if method == "provider_role":
        return profile["provider"] + ":" + profile["role_family"]
    return "shared"


def fit_scalers(first_development: list[dict]) -> dict:
    result: dict = {}
    for method in METHODS:
        groups: dict[str, list] = defaultdict(list)
        for profile in first_development:
            groups[scaler_key(profile, method)].append(vector(profile))
        result[method] = {}
        for key, vectors in sorted(groups.items()):
            x = np.array(vectors)
            mean, sd = x.mean(axis=0), x.std(axis=0)
            if method == "raw":
                mean, sd = np.zeros(len(COMMON_IDS)), np.ones(len(COMMON_IDS))
            result[method][key] = dict(
                mean=mean.tolist(), scale=np.where(sd > 1e-10, sd, 1).tolist(), n=len(x)
            )
    return result


def transform(profiles: list[dict], scalers: dict, method="shared") -> np.ndarray:
    return np.array(
        [
            (vector(p) - scalers[method][scaler_key(p, method)]["mean"])
            / scalers[method][scaler_key(p, method)]["scale"]
            for p in profiles
        ]
    )


def neighbours(query: dict, candidates: list[dict], scalers: dict, count=10) -> list[dict]:
    """Enforced provider, competition-season and role boundary, common features only."""
    if not query["common_ready"] or query["role_family"] not in {"DEF", "MID", "FWD"}:
        return []
    candidates = sorted(
        [
            p
            for p in candidates
            if p["common_ready"]
            and p["id"] != query["id"]
            and (p["provider"], p["scope"], p["role_family"])
            == (query["provider"], query["scope"], query["role_family"])
        ],
        key=lambda p: p["id"],
    )
    if not candidates:
        return []
    distances = cdist(transform([query], scalers), transform(candidates, scalers))[0]
    return [
        dict(id=candidates[i]["id"], distance=round(float(distances[i]), 6))
        for i in np.argsort(distances, kind="stable")[:count]
    ]


def interval(values_, rng, repeats=2000):
    a = np.asarray(values_, dtype=float)
    if not len(a):
        return None
    means = a[rng.integers(0, len(a), size=(repeats, len(a)))].mean(axis=1)
    return [round(float(v), 6) for v in np.quantile(means, [0.025, 0.975])]


def retrieval(full, halves, threshold, scalers, method, rng):
    eligible = {p["id"] for p in full if p["common_ready"] and p["minutes"] >= threshold}
    maps = [
        {
            p["id"]: p
            for p in halves
            if p["half"] == h
            and p["common_ready"]
            and p["minutes"] >= threshold / 2
            and p["id"] in eligible
        }
        for h in (0, 1)
    ]
    groups: dict[tuple, list] = defaultdict(list)
    for key in sorted(maps[0].keys() & maps[1].keys()):
        a, b = maps[0][key], maps[1][key]
        if a["role_family"] == b["role_family"]:
            groups[(a["scope"], a["role_family"])].append((a, b))
    reports, ranks_by_provider = [], defaultdict(list)
    for (scope, role), pairs in sorted(groups.items()):
        if len(pairs) < 20:
            reports.append(
                dict(scope=scope, role=role, n=len(pairs), status="below_20", metrics=None)
            )
            continue
        distances = cdist(
            transform([p[0] for p in pairs], scalers, method),
            transform([p[1] for p in pairs], scalers, method),
        )
        ranks = np.array(
            [
                int(np.where(np.argsort(d, kind="stable") == i)[0][0]) + 1
                for i, d in enumerate(distances)
            ]
        )
        rr = 1 / ranks
        metrics = dict(
            mrr=float(rr.mean()),
            recall_at_1=float((ranks <= 1).mean()),
            recall_at_5=float((ranks <= 5).mean()),
            recall_at_10=float((ranks <= 10).mean()),
            mrr_ci=interval(rr, rng),
            random_mrr=float(np.sum(1 / np.arange(1, len(pairs) + 1)) / len(pairs)),
        )
        reports.append(
            dict(scope=scope, role=role, n=len(pairs), status="evaluated", metrics=metrics)
        )
        ranks_by_provider[scope.split("-")[0]].extend(rr.tolist())
    return dict(
        threshold=threshold,
        scaling=method,
        cohorts=reports,
        providers={
            p: dict(n=len(v), mrr=float(np.mean(v)), mrr_ci=interval(v, rng))
            for p, v in ranks_by_provider.items()
        },
    )


def select_threshold(results: list[dict], development: set[str]) -> tuple[int, dict]:
    scores = {}
    for result in results:
        groups: dict[str, list] = defaultdict(list)
        for row in result["cohorts"]:
            if row["scope"] in development and row["metrics"]:
                groups[row["scope"].split("-")[0]].append((row["n"], row["metrics"]["mrr"]))
        if len(groups) != 2:
            continue
        scores[result["threshold"]] = float(
            np.mean(
                [
                    sum(n * mrr for n, mrr in pairs) / sum(n for n, _ in pairs)
                    for pairs in groups.values()
                ]
            )
        )
    if not scores:
        raise ValueError("Insufficient development retrieval evidence to select a common threshold")
    best = max(scores.values())
    return min(t for t, score in scores.items() if score + 1e-12 >= 0.9 * best), scores


def classifier(profiles: list[dict], rng, *, primary: bool):
    shared = {
        "statsbomb-2-27": "england",
        "wyscout-364-181150": "england",
        "statsbomb-11-27": "spain",
        "wyscout-795-181144": "spain",
        "statsbomb-12-27": "italy",
        "wyscout-524-181248": "italy",
    }
    sample = profiles
    if primary:
        strata: dict[tuple, dict] = defaultdict(lambda: defaultdict(list))
        for p in profiles:
            if p["scope"] in shared:
                strata[(shared[p["scope"]], p["role_family"])][p["provider"]].append(p)
        sample = []
        for _, providers in sorted(strata.items()):
            n = min(len(providers[provider]) for provider in ("statsbomb", "wyscout"))
            for provider in ("statsbomb", "wyscout"):
                rows = sorted(providers[provider], key=lambda p: p["id"])
                sample.extend(rows[i] for i in rng.permutation(len(rows))[:n])
    sample.sort(key=lambda p: p["id"])
    x, y = (
        np.array([vector(p) for p in sample]),
        np.array([int(p["provider"] == "wyscout") for p in sample]),
    )
    groups = np.array([p["provider"] + ":" + str(p["player_id"]) for p in sample])
    train, test = next(
        GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=1102026).split(x, y, groups)
    )
    if set(groups[train]) & set(groups[test]):
        raise ValueError("Provider identity leaked into classifier holdout")
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(C=1, class_weight="balanced", max_iter=2000, random_state=1102026),
    )
    model.fit(x[train], y[train])
    probability = model.predict_proba(x[test])[:, 1]
    prediction = probability >= 0.5
    auc, balanced = (
        roc_auc_score(y[test], probability),
        balanced_accuracy_score(y[test], prediction),
    )
    # Bootstrap held-out identities, retaining repeated seasons together.
    test_groups = sorted(set(groups[test]))
    group_rows = {g: np.flatnonzero(groups[test] == g) for g in test_groups}
    boot = []
    for _ in range(500):
        indexes = np.concatenate(
            [
                group_rows[test_groups[i]]
                for i in rng.integers(0, len(test_groups), len(test_groups))
            ]
        )
        if len(set(y[test][indexes])) == 2:
            boot.append(
                (
                    roc_auc_score(y[test][indexes], probability[indexes]),
                    balanced_accuracy_score(y[test][indexes], prediction[indexes]),
                )
            )
    return dict(
        sample="men_shared_leagues_role_matched"
        if primary
        else "all_eligible_including_gender_coverage_confound",
        train_profiles=len(train),
        heldout_profiles=len(test),
        train_identities=len(set(groups[train])),
        heldout_identities=len(test_groups),
        auc=float(auc),
        balanced_accuracy=float(balanced),
        auc_ci=np.quantile(np.array(boot)[:, 0], [0.025, 0.975]).tolist(),
        balanced_accuracy_ci=np.quantile(np.array(boot)[:, 1], [0.025, 0.975]).tolist(),
        features=COMMON_IDS,
        split="30_percent_provider_identity_grouped_holdout",
        model="fixed_C1_balanced_logistic_train_only_standard_scaler",
        coefficients=model[-1].coef_[0].tolist(),
    )


def distributions(profiles):
    groups: dict[tuple, dict] = defaultdict(lambda: defaultdict(list))
    pairs = {
        "statsbomb-2-27": "england",
        "wyscout-364-181150": "england",
        "statsbomb-11-27": "spain",
        "wyscout-795-181144": "spain",
        "statsbomb-12-27": "italy",
        "wyscout-524-181248": "italy",
    }
    for p in profiles:
        for league in ["all", *([pairs[p["scope"]]] if p["scope"] in pairs else [])]:
            groups[(league, p["role_family"])][p["provider"]].append(p)
    rows = []
    for (league, role), providers in sorted(groups.items()):
        if set(providers) != {"statsbomb", "wyscout"}:
            continue
        for key in COMMON_IDS:
            arrays = {
                provider: np.array([p["common"][key] for p in group])
                for provider, group in providers.items()
            }
            stats = {
                provider: dict(
                    n=len(a),
                    mean=float(a.mean()),
                    median=float(np.median(a)),
                    sd=float(a.std()),
                    quantiles=np.quantile(a, [0.05, 0.25, 0.75, 0.95]).tolist(),
                )
                for provider, a in arrays.items()
            }
            a, b = arrays["statsbomb"], arrays["wyscout"]
            rows.append(
                dict(
                    league=league,
                    role=role,
                    feature=key,
                    providers=stats,
                    ks_statistic=float(ks_2samp(a, b).statistic),
                    wasserstein=float(wasserstein_distance(a, b)),
                )
            )
    return rows


def provider_balance(profiles, scalers):
    reports = []
    for method in METHODS:
        for role in ("DEF", "MID", "FWD"):
            cohort = sorted(
                [p for p in profiles if p["role_family"] == role], key=lambda p: p["id"]
            )
            x = transform(cohort, scalers, method)
            d = cdist(x, x)
            np.fill_diagonal(d, np.inf)
            ranks = np.argsort(d, axis=1, kind="stable")[:, :10]
            for provider in ("statsbomb", "wyscout"):
                indexes = [i for i, p in enumerate(cohort) if p["provider"] == provider]
                share = np.mean(
                    [
                        np.mean([cohort[j]["provider"] == provider for j in ranks[i]])
                        for i in indexes
                    ]
                )
                reports.append(
                    dict(
                        scaling=method,
                        role=role,
                        provider=provider,
                        queries=len(indexes),
                        same_provider_top10_share=float(share),
                        same_provider_available_share=(len(indexes) - 1) / (len(cohort) - 1),
                    )
                )
    return reports


def match_stability(profiles, observations, scalers, validated, rng):
    by_id: dict[str, list] = defaultdict(list)
    for r in observations:
        by_id[f"{r['scope']}-{r['player_id']}"].append(r)
    groups: dict[tuple, list] = defaultdict(list)
    for p in profiles:
        if (p["scope"], p["role_family"]) in validated:
            groups[(p["scope"], p["role_family"])].append(p)
    reports = []
    for (scope, role), cohort in sorted(groups.items()):
        cohort.sort(key=lambda p: p["id"])
        x = transform(cohort, scalers)
        distance = cdist(x, x)
        np.fill_diagonal(distance, np.inf)
        query_ids = sorted(
            rng.choice(len(cohort), size=min(12, len(cohort)), replace=False).tolist()
        )
        baseline = {i: set(np.argsort(distance[i], kind="stable")[:10]) for i in query_ids}
        arrays = [
            np.array([[r["minutes"]] + [r["c_" + k] for k in COUNT_KEYS] for r in by_id[p["id"]]])
            for p in cohort
        ]
        scores = []
        for _ in range(40):
            replicate = []
            for p, a in zip(cohort, arrays, strict=True):
                summed = a[rng.integers(0, len(a), len(a))].sum(axis=0)
                feature_values = values(dict(zip(COUNT_KEYS, summed[1:], strict=True)), summed[0])
                replicate.append(p | {"common": feature_values})
            matrix = transform(replicate, scalers)
            d = cdist(matrix[query_ids], matrix)
            for index, i in enumerate(query_ids):
                d[index, i] = np.inf
                chosen = set(np.argsort(d[index], kind="stable")[:10])
                scores.append(len(chosen & baseline[i]) / len(chosen | baseline[i]))
        reports.append(
            dict(
                scope=scope,
                role=role,
                candidates=len(cohort),
                queries=len(query_ids),
                replicates=40,
                mean_top10_jaccard=float(np.mean(scores)),
                interval=np.quantile(scores, [0.025, 0.975]).tolist(),
                resampling="independent_appearances_both_queries_and_candidates_fixed_scaler",
            )
        )
    return reports


def evaluate(root: Path, destination: Path):
    config = json.loads((root / "config/v11-expansion.json").read_text())
    rng = np.random.default_rng(config["seed"])
    full = aggregate(destination)
    observations = load_observations(destination)
    halves, cutoffs = split_profiles(destination, observations)
    development = set(config["development_scopes"])
    training = [
        p
        for p in halves
        if p["half"] == 0
        and p["scope"] in development
        and p["common_ready"]
        and p["minutes"] >= 225
    ]
    scalers = fit_scalers(training)
    temporal = [
        retrieval(full, halves, threshold, scalers, method, rng)
        for method in METHODS
        for threshold in config["candidate_thresholds"]
    ]
    threshold, dev_scores = select_threshold(
        [r for r in temporal if r["scaling"] == "shared"], development
    )
    eligible = [p for p in full if p["common_ready"] and p["minutes"] >= threshold]
    selected = next(r for r in temporal if r["scaling"] == "shared" and r["threshold"] == threshold)
    validated = {(r["scope"], r["role"]) for r in selected["cohorts"] if r["status"] == "evaluated"}
    primary, secondary = (
        classifier(eligible, rng, primary=True),
        classifier(eligible, rng, primary=False),
    )
    gate = (
        max(
            primary["auc"],
            primary["balanced_accuracy"],
            secondary["auc"],
            secondary["balanced_accuracy"],
        )
        <= config["provider_bias_gate"]
    )
    report = dict(
        version="common-similarity-v1",
        common_version="common-profile-v1",
        seed=config["seed"],
        features=COMMON_IDS,
        selected_threshold=threshold,
        development_scores=dev_scores,
        development_scopes=sorted(development),
        cutoffs=cutoffs,
        scalers=scalers,
        scaler_fit_ids=[p["id"] for p in training],
        temporal=temporal,
        provider_classification=dict(primary=primary, secondary=secondary),
        provider_bias_gate_passed=gate,
        cross_provider_ranking_enabled=False,
        publication_decision="descriptive_comparison_only_three_features_and_no_cross_provider_identity_ground_truth",
        provider_bias_gate=config["provider_bias_gate"],
        distributions=distributions(eligible),
        neighbour_provider_balance=provider_balance(eligible, scalers),
        match_bootstrap=match_stability(eligible, observations, scalers, validated, rng),
        limitations=[
            "provider_league_season_and_gender_are_confounded",
            "no_cross_provider_identity_ground_truth",
            "split_half_survivor_cohorts_require_sufficient_minutes_in_both_halves",
            "match_bootstrap_conditions_on_observed_schedule_and_fixed_scaler",
            "descriptive_comparison_is_not_transfer_or_recruitment_validation",
        ],
    )
    output = root / "artifacts/v11" if destination.name == "full" else destination / "evaluation"
    write_json(output / "evaluation.json", report)
    write_json(destination / "split-profiles.json", halves)
    # Standalone research figure, with no event data or player labels.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = transform(eligible, scalers)
    pca = PCA(n_components=2).fit(x)
    projected = pca.transform(x)
    fig, ax = plt.subplots(figsize=(7, 4.5), layout="constrained")
    for provider, color in (("statsbomb", "#174463"), ("wyscout", "#7c985c")):
        mask = [p["provider"] == provider for p in eligible]
        ax.scatter(
            projected[mask, 0], projected[mask, 1], s=8, alpha=0.3, label=provider, color=color
        )
    ax.set(
        xlabel=f"PC1 ({pca.explained_variance_ratio_[0]:.1%})",
        ylabel=f"PC2 ({pca.explained_variance_ratio_[1]:.1%})",
        title="Common profiles · shared development scaling\nDescriptive; provider, league, season and gender are confounded",
    )
    ax.legend()
    fig.savefig(output / "provider-pca.png", dpi=180)
    plt.close(fig)
    write_json(
        output / "pca.json",
        dict(
            explained_variance_ratio=pca.explained_variance_ratio_.tolist(),
            components=pca.components_.tolist(),
            fit="all_eligible_descriptive_only_not_used_in_ranking",
            n=len(eligible),
        ),
    )
    print(
        f"Common threshold {threshold}; primary provider AUC {primary['auc']:.3f}; provider bias gate passed {gate}; public cross-provider ranking withheld",
        flush=True,
    )
    return report
