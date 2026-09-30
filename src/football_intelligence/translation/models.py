"""Explicit hierarchical count likelihood; all inference is offline."""

import hashlib
import json
import math
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "fri-phase3-matplotlib"))
os.environ.setdefault(
    "PYTENSOR_FLAGS", "compiledir=" + str(Path(tempfile.gettempdir()) / "fri-phase3-pytensor")
)

import arviz as az
import numpy as np
import pymc as pm
from scipy.special import gammaln, logsumexp

from football_intelligence.dna.cohort import write


def source_log(row: dict, target: str) -> float:
    return math.log((row["source"]["counts"][target] + 0.5) / (row["source_minutes"] / 90 + 0.5))


def design(rows: list[dict], target: str) -> dict:
    return dict(
        roles=sorted({r["destination_role"] for r in rows}),
        teams=sorted({r["destination"]["team_id"] for r in rows}),
        source_center=float(np.mean([source_log(r, target) for r in rows])),
        target=target,
    )


def build_model(rows: list[dict], target: str, cfg: dict, *, no_team: bool = False):
    meta = design(rows, target)
    role = np.array([meta["roles"].index(r["destination_role"]) for r in rows])
    team = np.array([meta["teams"].index(r["destination"]["team_id"]) for r in rows])
    source = np.array([source_log(r, target) - meta["source_center"] for r in rows])
    context = np.array([r["context_log_ratio"] for r in rows])
    minutes = np.log(np.array([r["source_minutes"] for r in rows]) / 900)
    changed = np.array([r["role_change"] != "same" for r in rows], dtype=float)
    exposure = np.array([r["destination_minutes"] / 90 for r in rows])
    y = np.array([r["destination"]["counts"][target] for r in rows])
    if (
        not np.isfinite(y).all()
        or np.any(y < 0)
        or np.any(y != np.floor(y))
        or np.any(exposure <= 0)
    ):
        raise ValueError(
            "Count likelihood requires nonnegative integer counts and positive exposure"
        )
    p = cfg["priors"]
    with pm.Model(
        coords={"role": meta["roles"], "team": meta["teams"], "observation": np.arange(len(rows))}
    ) as model:
        intercept = pm.Normal(
            "intercept", mu=math.log(cfg["reference_rates"][target]), sigma=p["intercept_sd"]
        )
        beta_source = pm.Normal("beta_source", mu=p["source_mean"], sigma=p["source_sd"])
        beta_minutes = pm.Normal("beta_minutes", mu=0, sigma=p["minutes_sd"])
        beta_role_change = pm.Normal("beta_role_change", mu=0, sigma=p["role_change_sd"])
        role_sd = pm.HalfNormal("role_sd", sigma=p["role_scale"])
        role_z = pm.Normal("role_z", 0, 1, dims="role")
        role_effect = pm.Deterministic(
            "role_effect", role_sd * (role_z - role_z.mean()), dims="role"
        )
        eta = (
            intercept
            + beta_source * source
            + beta_minutes * minutes
            + beta_role_change * changed
            + role_effect[role]
        )
        if not no_team:
            beta_context = pm.Normal("beta_context", 0, p["context_sd"])
            team_sd = pm.HalfNormal("team_sd", sigma=p["team_scale"])
            team_z = pm.Normal("team_z", 0, 1, dims="team")
            team_effect = pm.Deterministic(
                "team_effect", team_sd * (team_z - team_z.mean()), dims="team"
            )
            eta = eta + beta_context * context + team_effect[team]
        latent_rate = pm.Deterministic("rate", pm.math.exp(eta), dims="observation")
        dispersion = pm.Exponential("dispersion", p["dispersion_rate"])
        pm.NegativeBinomial(
            "count",
            mu=exposure * latent_rate,
            alpha=dispersion,
            observed=y.astype(int),
            dims="observation",
        )
    meta["no_team"] = no_team
    return model, meta


def diagnostics(idata) -> dict:
    names = [k for k in idata.posterior.data_vars if k != "rate"]
    summary: Any = az.summary(idata, var_names=names, round_to=None)
    rhat = float(az.rhat(idata, var_names=names).to_array().max())
    key_names = [k for k in names if k not in ("role_z", "team_z", "role_effect", "team_effect")]
    ess = float(az.ess(idata, var_names=key_names, method="bulk").to_array().min())
    divergences = int(idata.sample_stats.diverging.values.sum())
    tree = int(idata.sample_stats.tree_depth.values.max())
    return dict(
        divergences=divergences,
        max_rhat=rhat,
        min_key_bulk_ess=ess,
        min_tail_ess=float(summary["ess_tail"].min()),
        max_tree_depth=tree,
        passed=divergences == 0 and rhat <= 1.01 and ess >= 400 and tree < 10,
        parameters=json.loads(summary.reset_index(names="parameter").to_json(orient="records")),
    )


def prior_check(model, cfg: dict, target: str, exposures: np.ndarray | None = None) -> dict:
    with model:
        prior = pm.sample_prior_predictive(
            samples=cfg.get("prior_samples", 1500), random_seed=cfg["seed"]
        )
    values = prior.prior["rate"].values.reshape(-1)
    ceiling = cfg["prior_rate_ceilings"][target]
    fraction = float(np.mean(values > ceiling))
    predictive = None
    if exposures is not None:
        simulated = prior.prior_predictive["count"].values / exposures
        predictive = dict(
            rate_quantiles=np.quantile(simulated, [0.01, 0.5, 0.99]).tolist(),
            fraction_above_ceiling=float(np.mean(simulated > ceiling)),
            finite=bool(np.isfinite(simulated).all()),
        )
    return dict(
        target=target,
        rate_quantiles=dict(
            zip(["p01", "p50", "p99"], np.quantile(values, [0.01, 0.5, 0.99]).tolist(), strict=True)
        ),
        ceiling=ceiling,
        fraction_above_ceiling=fraction,
        finite=bool(np.isfinite(values).all()),
        observation_prediction=predictive,
        passed=bool(
            np.isfinite(values).all()
            and fraction <= 0.01
            and (
                predictive is None
                or (predictive["finite"] and predictive["fraction_above_ceiling"] <= 0.01)
            )
        ),
    )


def fit(root: Path, rows: list[dict], target: str, cfg: dict, label: str, *, no_team: bool = False):
    directory = root / "artifacts/phase3/posterior"
    directory.mkdir(parents=True, exist_ok=True)
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    key = hashlib.sha256(
        json.dumps(
            dict(
                rows=rows,
                target=target,
                cfg=cfg,
                no_team=no_team,
                code_hash=code_hash,
                pymc=pm.__version__,
            ),
            sort_keys=True,
        ).encode()
    ).hexdigest()
    path = directory / f"{label}-{target}.nc"
    manifest_path = path.with_suffix(".json")
    if path.exists() and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest["fit_hash"] == key:
            return az.from_netcdf(path), manifest
    model, meta = build_model(rows, target, cfg, no_team=no_team)
    prior = prior_check(model, cfg, target, np.array([r["destination_minutes"] / 90 for r in rows]))
    if not prior["passed"]:
        write(directory / f"{label}-{target}-prior-rejected.json", prior)
        raise ValueError(f"Prior plausibility gate failed: {prior}")
    with model:
        idata = pm.sample(
            **cfg["sampling"],
            random_seed=cfg["seed"],
            progressbar=False,
            return_inferencedata=True,
            idata_kwargs={"log_likelihood": True},
        )
        pm.sample_posterior_predictive(
            idata, random_seed=cfg["seed"] + 1, progressbar=False, extend_inferencedata=True
        )
    idata.to_netcdf(path)
    manifest = dict(
        fit_hash=key,
        model_version=cfg["version"],
        feature_version=cfg["feature_version"],
        player_dna_version=cfg["player_dna_version"],
        prior_version=cfg["priors_version"],
        source_revision=cfg["revision"],
        config=cfg,
        design=meta,
        prior_check=prior,
        diagnostics=diagnostics(idata),
        data_hash=hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
        model_code_hash=code_hash,
        git_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        generated_at=datetime.now(UTC).isoformat(),
        versions=dict(pymc=pm.__version__, arviz=az.__version__, numpy=np.__version__),
        posterior_bytes=path.stat().st_size,
        episodes=len(rows),
        players=len({r["player_id"] for r in rows}),
        destination_dates=[
            min(r["destination"]["start_date"] for r in rows),
            max(r["destination"]["end_date"] for r in rows),
        ],
    )
    write(manifest_path, manifest)
    return idata, manifest


def posterior_array(idata, name: str) -> np.ndarray:
    value = idata.posterior[name].values
    return value.reshape((-1, *value.shape[2:]))


def predict(
    idata,
    meta: dict,
    rows: list[dict],
    *,
    seed: int = 20260930,
    exposure_minutes: int | None = None,
    source_rates: dict[str, np.ndarray] | None = None,
) -> dict:
    rng = np.random.default_rng(seed)
    alpha = posterior_array(idata, "intercept")
    n = len(alpha)
    rates = []
    unseen = {}
    for r in rows:
        src = source_log(r, meta["target"]) - meta["source_center"]
        if source_rates is not None:
            samples = source_rates[r["source_environment_id"]]
            chosen = rng.choice(samples, n)
            exposure = r["source_minutes"] / 90
            src = np.log((chosen * exposure + 0.5) / (exposure + 0.5)) - meta["source_center"]
        eta = (
            alpha
            + posterior_array(idata, "beta_source") * src
            + posterior_array(idata, "beta_minutes") * math.log(r["source_minutes"] / 900)
            + posterior_array(idata, "beta_role_change") * float(r["role_change"] != "same")
        )
        if r["destination_role"] not in meta["roles"]:
            raise ValueError("Unsupported target role")
        eta = (
            eta
            + posterior_array(idata, "role_effect")[:, meta["roles"].index(r["destination_role"])]
        )
        if not meta["no_team"]:
            eta = eta + posterior_array(idata, "beta_context") * r["context_log_ratio"]
            tid = r["destination"]["team_id"]
            if tid in meta["teams"]:
                eta = eta + posterior_array(idata, "team_effect")[:, meta["teams"].index(tid)]
            else:
                if tid not in unseen:
                    unseen[tid] = rng.normal(0, posterior_array(idata, "team_sd"))
                eta = eta + unseen[tid]
        rates.append(np.exp(eta))
    latent = np.stack(rates, axis=1)
    exposure = np.array([(exposure_minutes or r["destination_minutes"]) / 90 for r in rows])
    mu = latent * exposure[None, :]
    dispersion = posterior_array(idata, "dispersion")[:, None]
    counts = rng.negative_binomial(dispersion, dispersion / (dispersion + mu))
    return dict(
        mean=latent.mean(axis=0),
        latent=latent,
        predictive=counts / exposure[None, :],
        mu=mu,
        dispersion=dispersion,
        unseen_teams=sorted(unseen),
    )


def log_predictive_density(prediction: dict, counts: np.ndarray) -> float:
    mu, a = prediction["mu"], prediction["dispersion"]
    y = counts[None, :]
    logp = (
        gammaln(y + a)
        - gammaln(a)
        - gammaln(y + 1)
        + a * np.log(a / (a + mu))
        + y * np.log(mu / (a + mu))
    )
    return float(np.mean(logsumexp(logp, axis=0) - np.log(mu.shape[0])))
