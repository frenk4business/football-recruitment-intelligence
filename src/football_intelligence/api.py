import json
import os
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from football_intelligence.contracts import (
    CompetitionSummary,
    Coverage,
    Explorer,
    MatchSummary,
    MetricDefinition,
    PlayerSummary,
    Source,
)


class Health(BaseModel):
    status: str
    data_ready: bool
    version: str


def create_app(artifact_dir: Path | None = None) -> FastAPI:
    root = artifact_dir or Path(os.getenv("FRI_ARTIFACTS", "artifacts"))
    app = FastAPI(
        title="Football Recruitment Intelligence",
        version="0.1.0",
        description="Phase 1 aggregate research contracts; no arbitrary SQL or predictive models.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("FRI_CORS_ORIGINS", "http://localhost:3000").split(","),
        allow_methods=["GET"],
        allow_headers=["Accept"],
    )

    def read(name: str):
        try:
            return json.loads((root / name).read_text())
        except FileNotFoundError:
            raise HTTPException(
                503, "Data artifacts unavailable; run make data-bootstrap"
            ) from None
        except (ValueError, OSError):
            raise HTTPException(503, "Data artifacts cannot be read") from None

    @app.get("/health", response_model=Health)
    def health():
        return Health(
            status="ok", data_ready=(root / "data_coverage.json").exists(), version="0.1.0"
        )

    @app.get("/api/v1/coverage", response_model=Coverage)
    def coverage():
        return read("data_coverage.json")

    @app.get("/api/v1/sources", response_model=list[Source])
    def sources():
        return read("sources.json")

    @app.get("/api/v1/metrics", response_model=list[MetricDefinition])
    def metrics():
        return read("metrics.json")

    @app.get("/api/v1/competitions", response_model=list[CompetitionSummary])
    def competitions():
        return read("competitions.json")

    @app.get("/api/v1/matches", response_model=list[MatchSummary])
    def matches(
        provider: Literal["statsbomb", "skillcorner"] | None = None,
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ):
        rows = read("matches.json")
        return [r for r in rows if provider is None or r["provider"] == provider][
            offset : offset + limit
        ]

    def explorer_data(match_id: UUID):
        if str(match_id) not in {m["id"] for m in read("matches.json")}:
            raise HTTPException(404, "Match not in this sample")
        return read(f"explorer/{match_id}.json")

    @app.get("/api/v1/explorer/{match_id}", response_model=Explorer)
    def explorer(match_id: UUID):
        return explorer_data(match_id)

    @app.get("/api/v1/players", response_model=list[PlayerSummary])
    def players(match_id: UUID, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0)):
        return explorer_data(match_id)["players"][offset : offset + limit]

    return app


app = create_app()
