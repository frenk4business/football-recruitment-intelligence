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
        description="Versioned aggregate research contracts and precomputed player similarity; no arbitrary SQL.",
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

    from football_intelligence.dna.contracts import DNAEvaluation, DNAIndex, DNANeighbor, DNAProfile
    from football_intelligence.dna.registry import FeatureDefinition

    @app.get("/api/v1/player-dna", response_model=DNAIndex)
    def dna_index():
        return read("phase2/public/index.json")

    def dna_detail(player_id: UUID, threshold: int):
        index = read("phase2/public/index.json")
        if threshold not in index["thresholds"]:
            raise HTTPException(422, "Unsupported evidence threshold")
        if str(player_id) not in {p["player_id"] for p in index["players"]}:
            raise HTTPException(404, "Player not in analytical cohort")
        return read(f"phase2/public/{threshold}/{player_id}.json")

    @app.get("/api/v1/player-dna/{player_id}", response_model=DNAProfile)
    def dna_profile(player_id: UUID, threshold: int = 900):
        return dna_detail(player_id, threshold)

    @app.get("/api/v1/player-dna/{player_id}/similar", response_model=list[DNANeighbor])
    def dna_similar(player_id: UUID, threshold: int = 900, limit: int = Query(10, ge=1, le=20)):
        return dna_detail(player_id, threshold)["neighbors"][:limit]

    @app.get("/api/v1/similarity/evaluation", response_model=DNAEvaluation)
    def dna_evaluation():
        return read("phase2/public/evaluation.json")

    @app.get("/api/v1/features", response_model=list[FeatureDefinition])
    def dna_features():
        return read("phase2/public/features.json")

    from football_intelligence.translation.contracts import (
        TranslationEvaluation,
        TranslationIndex,
        TranslationModels,
        TranslationPlayerDetail,
        TranslationPrediction,
    )

    @app.get("/api/v1/translation/models", response_model=TranslationModels)
    def translation_models():
        return read("phase3/public/models.json")

    @app.get("/api/v1/translation/environments", response_model=TranslationIndex)
    def translation_environments():
        return read("phase3/public/index.json")

    def translation_detail(player_id: UUID):
        if str(player_id) not in {
            p["player_id"] for p in read("phase3/public/index.json")["players"]
        }:
            raise HTTPException(404, "Player not in audited historical cohort")
        return read(f"phase3/public/players/{player_id}.json")

    @app.get("/api/v1/translation/players/{player_id}", response_model=TranslationPlayerDetail)
    def translation_player(player_id: UUID):
        return translation_detail(player_id)

    @app.get("/api/v1/translation/predict", response_model=TranslationPrediction)
    def translation_predict(
        player_id: UUID,
        source_environment: UUID,
        target_environment: UUID,
        target_role: str = Query(max_length=10),
    ):
        detail = translation_detail(player_id)
        for prediction in detail["predictions"]:
            if (
                prediction["source_environment_id"] == str(source_environment)
                and prediction["target_environment_id"] == str(target_environment)
                and prediction["target_role"] == target_role
            ):
                return prediction
        raise HTTPException(
            422, "Unsupported source, target or role; inspect the player's environment exclusions"
        )

    @app.get("/api/v1/translation/evaluation", response_model=TranslationEvaluation)
    def translation_evaluation():
        return read("phase3/public/evaluation.json")

    from football_intelligence.recruitment.contracts import (
        ClubContext,
        RecruitmentCandidate,
        RecruitmentClubSummary,
        RecruitmentEvaluation,
        RecruitmentFeature,
        RecruitmentIndex,
        RecruitmentResult,
        RecruitmentScenario,
    )
    from football_intelligence.recruitment.scoring import rank_candidates, validate_scenario

    @app.get("/api/v1/recruitment", response_model=RecruitmentIndex)
    def recruitment_index():
        return read("phase4/public/index.json")

    @app.get("/api/v1/recruitment/clubs", response_model=list[RecruitmentClubSummary])
    def recruitment_clubs():
        return recruitment_index()["clubs"]

    @app.get("/api/v1/recruitment/clubs/{club_id}", response_model=ClubContext)
    def recruitment_club(club_id: UUID):
        if str(club_id) not in {c["club_id"] for c in recruitment_clubs()}:
            raise HTTPException(404, "Club not in observed cohort")
        return read(f"phase4/public/clubs/{club_id}.json")

    @app.get("/api/v1/recruitment/requirements", response_model=list[RecruitmentFeature])
    def recruitment_requirements():
        return recruitment_index()["features"]

    @app.get("/api/v1/recruitment/candidates", response_model=list[RecruitmentCandidate])
    def recruitment_candidates(role: str | None = None):
        index = recruitment_index()
        if role is not None and role not in index["roles"]:
            raise HTTPException(422, "Unsupported comparison role")
        return [p for p in index["players"] if role is None or p["role"] == role]

    @app.post("/api/v1/recruitment/scenario", response_model=RecruitmentResult)
    def recruitment_scenario(scenario: RecruitmentScenario):
        index = recruitment_index()
        try:
            validate_scenario(index, scenario)
            return rank_candidates(index["players"], scenario, index["method"])
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/api/v1/recruitment/evaluation", response_model=RecruitmentEvaluation)
    def recruitment_evaluation():
        return read("phase4/public/evaluation.json")

    return app


app = create_app()
