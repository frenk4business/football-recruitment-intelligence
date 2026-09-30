import json
from enum import StrEnum
from pathlib import Path

import typer

from football_intelligence.data.fetch import fetch, read_config
from football_intelligence.pipeline import build, validate_stored

app = typer.Typer(help="Reproducible football data research commands.")
data = typer.Typer()
app.add_typer(data, name="data")


class Provider(StrEnum):
    statsbomb = "statsbomb"
    skillcorner = "skillcorner"


@data.command("discover")
def discover(provider: Provider):
    """Show the deliberately pinned sample, its revision and retrieval paths."""
    if provider == Provider.statsbomb:
        from football_intelligence.dna.cohort import discover as catalogue

        typer.echo(json.dumps(catalogue(Path.cwd()), indent=2))
    else:
        typer.echo(json.dumps(read_config(Path.cwd())[provider.value], indent=2))


@data.command("fetch")
def fetch_command(provider: Provider):
    typer.echo(json.dumps(fetch(Path.cwd(), provider.value), indent=2))


@data.command("build")
def build_command():
    typer.echo(json.dumps(build(Path.cwd())["row_counts"], indent=2))


@data.command("bootstrap")
def bootstrap():
    for provider in Provider:
        fetch(Path.cwd(), provider.value)
    build_command()


@data.command("validate")
def validate_command():
    typer.echo(json.dumps(validate_stored(Path.cwd()), indent=2))


@data.command("coverage")
def coverage():
    typer.echo(Path("artifacts/data_coverage.json").read_text())


cohort_app = typer.Typer(help="Pinned competition-season evidence.")
feature_app = typer.Typer(help="Versioned player features and eligibility.")
similarity_app = typer.Typer(help="Reproducible similarity research and static publication.")
app.add_typer(cohort_app, name="cohort")
app.add_typer(feature_app, name="features")
app.add_typer(similarity_app, name="similarity")

translation_app = typer.Typer(
    help="Audited environment evidence and offline probabilistic translation."
)
app.add_typer(translation_app, name="translation")
recruitment_app = typer.Typer(help="Observed recruitment requirements, context and candidate fit.")
app.add_typer(recruitment_app, name="recruitment")


@recruitment_app.command("build")
def recruitment_build():
    from football_intelligence.recruitment.export import build

    result = build(Path.cwd())
    typer.echo(
        f"Published {result['eligible_players']} eligible candidates, {result['clubs']} clubs; {result['public_bytes']} bytes"
    )


@recruitment_app.command("audit")
def recruitment_audit():
    from football_intelligence.recruitment.audit import audit

    result = audit(Path.cwd())
    typer.echo(result["decision"])


@recruitment_app.command("publish")
def recruitment_publish():
    from football_intelligence.recruitment.export import publish

    typer.echo(publish(Path.cwd())["public_bytes"])


@translation_app.command("data")
def translation_data():
    from football_intelligence.translation.dataset import prepare
    from football_intelligence.translation.materialize import materialize

    typer.echo(materialize(Path.cwd()))
    typer.echo(prepare(Path.cwd()))


@translation_app.command("audit")
def translation_audit():
    from football_intelligence.translation.evidence import audit_catalogue_identities
    from football_intelligence.translation.materialize import settings
    from football_intelligence.translation.sources import catalogue
    from football_intelligence.translation.wyscout import audit_wyscout

    catalogue(Path.cwd(), settings(Path.cwd())["revision"], lineups=True)
    typer.echo(audit_catalogue_identities(Path.cwd()))
    typer.echo(audit_wyscout(Path.cwd()))


@translation_app.command("validate-models")
def translation_validation():
    from football_intelligence.translation.evaluation import validation

    validation(Path.cwd())


@translation_app.command("evaluate")
def translation_evaluate():
    from football_intelligence.translation.evaluation import evaluate

    evaluate(Path.cwd())


@translation_app.command("publish")
def translation_publish():
    from football_intelligence.translation.publish import publish

    result = publish(Path.cwd())
    typer.echo(f"Published {result['players']} historical profiles; {result['public_bytes']} bytes")


@cohort_app.command("build")
def cohort_build(name: str = "wsl_2023_24", max_matches: int | None = typer.Option(None, min=1)):
    from football_intelligence.dna.cohort import build_cohort

    result = build_cohort(Path.cwd(), name, max_matches)
    typer.echo(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("dates", "match_ids", "warnings")},
            indent=2,
        )
    )


@cohort_app.command("inspect")
def cohort_inspect(name: str = "wsl_2023_24"):
    from football_intelligence.dna.cohort import local_cohort

    typer.echo((local_cohort(Path.cwd(), name) / "cohort.json").read_text())


@feature_app.command("build")
def feature_build():
    from football_intelligence.dna.features import build_features

    build_features(Path.cwd())
    feature_eligibility()


@feature_app.command("eligibility")
def feature_eligibility():
    report = json.loads(Path("artifacts/phase2/cohort_eligibility.json").read_text())
    for threshold, info in sorted(report["thresholds"].items(), key=lambda kv: int(kv[0])):
        typer.echo(f"{threshold} minutes: {info['eligible']} eligible — {info['roles']}")


@similarity_app.command("evaluate")
def similarity_evaluate():
    from football_intelligence.dna.evaluation import evaluate

    evaluate(Path.cwd())


@similarity_app.command("build")
def similarity_build():
    from football_intelligence.dna.publish import publish

    manifest = publish(Path.cwd())
    typer.echo(
        f"Published {len(manifest['public_sha256'])} derived artifacts; {manifest['version']}"
    )
