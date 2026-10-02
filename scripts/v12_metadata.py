from pathlib import Path

from football_intelligence.expansion.metadata import build, skillcorner

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    build(root)
    skillcorner(root)
