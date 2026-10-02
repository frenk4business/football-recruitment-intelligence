from pathlib import Path

from football_intelligence.expansion.evaluate import build

if __name__ == "__main__":
    build(Path(__file__).resolve().parents[1])
