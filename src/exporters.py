from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT_DIR / "data" / "exports"


def write_markdown(filename: str, content: str) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / filename
    path.write_text(content, encoding="utf-8")
    return path

