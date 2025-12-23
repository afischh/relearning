#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

REPO = Path.home() / "relearning"
SRC = REPO / "lang" / "python" / "quiet_logos" / "log"
DST = REPO / "docs" / "log"


def today_str() -> str:
    return date.today().isoformat()


def main() -> None:
    d = today_str()
    src = SRC / f"{d}.md"
    if not src.exists():
        print(f"ERROR: not found: {src}", file=sys.stderr)
        sys.exit(1)

    DST.mkdir(parents=True, exist_ok=True)

    # Публикуем как markdown (GitHub Pages спокойно отдаёт .md как файл; позже сделаем HTML-рендер)
    dst = DST / f"{d}.md"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"OK: {dst}")


if __name__ == "__main__":
    main()
