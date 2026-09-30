from pathlib import Path

import numpy as np
import pytest

from football_intelligence.translation.baselines import Baseline
from football_intelligence.translation.materialize import settings
from football_intelligence.translation.models import build_model, pm, posterior_array, predict


def synthetic_rows():
    rng = np.random.default_rng(1947)
    rows = []
    for i in range(100):
        source = float(rng.uniform(0.6, 4.0))
        low = i >= 96
        exposure = 1.0 if low else 20.0
        count = int(rng.poisson(exposure * source * (2.0 if low else 0.8)))
        src_count = int(round(source * 40))
        rows.append(
            dict(
                player_id=str(i),
                source_environment_id=str(i),
                source_minutes=3600,
                destination_minutes=90 * exposure,
                source_role="A",
                destination_role="B" if low else "A",
                role_change="same",
                context_log_ratio=0,
                source_context={"passes_per90": 400},
                target_context={"passes_per90": 400},
                source={"counts": {"shots": src_count}, "reliable_minutes": 3600},
                destination={
                    "counts": {"shots": count},
                    "reliable_minutes": 90 * exposure,
                    "team_id": "t" + str(i % 4),
                },
            )
        )
    return rows


@pytest.fixture(scope="module")
def fitted():
    rows = synthetic_rows()
    cfg = settings(Path(__file__).resolve().parents[2])
    model, meta = build_model(rows, "shots", cfg)
    with model:
        trace = pm.sample(
            draws=350,
            tune=500,
            chains=2,
            cores=1,
            target_accept=0.95,
            random_seed=491,
            progressbar=False,
            compute_convergence_checks=False,
        )
    return rows, meta, trace


def test_synthetic_known_translation_and_partial_pooling(fitted):
    rows, meta, trace = fitted
    pred = predict(trace, meta, rows, seed=551)
    source = np.array([r["source"]["counts"]["shots"] / 40 for r in rows])
    ratio = float(np.mean(pred["mean"][:96] / source[:96]))
    assert 0.65 < ratio < 0.95
    assert np.isfinite(pred["predictive"]).all() and (pred["predictive"] >= 0).all()
    lo, hi = np.quantile(pred["predictive"], [0.1, 0.9], axis=0)
    assert np.all(lo <= hi)
    low_unpooled = np.mean([r["destination"]["counts"]["shots"] for r in rows[96:]])
    pooled = float(pred["mean"][96:].mean())
    assert pooled < low_unpooled
    assert posterior_array(trace, "role_sd").mean() > 0


def test_exposure_uncertainty_and_unsupported_role(fitted):
    rows, meta, trace = fitted
    short = predict(trace, meta, rows[:1], exposure_minutes=90, seed=553)["predictive"]
    long = predict(trace, meta, rows[:1], exposure_minutes=9000, seed=554)["predictive"]
    assert np.var(long) < np.var(short)
    bad = [{**rows[0], "destination_role": "unknown"}]
    with pytest.raises(ValueError, match="Unsupported target role"):
        predict(trace, meta, bad)


def test_baselines_fit_only_passed_training_and_keep_nonnegative_ranges():
    rows = synthetic_rows()
    for method in ["unchanged_source", "role_mean", "ridge"]:
        model = Baseline(method, "shots").fit_residuals(rows[:75])
        first = model.predict(rows[75:])
        rows[75]["destination"]["counts"]["shots"] = 999999
        assert np.array_equal(first, model.predict(rows[75:]))
        assert (model.predictive(rows[75:]) >= 0).all()
        assert len(model.residuals) == 75
