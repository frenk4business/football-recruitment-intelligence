"""Intentional initial download; normal CI never invokes this command."""

from pathlib import Path

from football_intelligence.expansion.sources import Sources

if __name__ == "__main__":
    Sources(Path(__file__).resolve().parents[1]).fetch()
