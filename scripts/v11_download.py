"""Explicit full source retrieval; CI never runs this command."""

from pathlib import Path

from football_intelligence.profiles.sources import Sources

sources = Sources(Path(__file__).resolve().parents[1])
sources.audit_catalogue()
sources.download()
