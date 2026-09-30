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
