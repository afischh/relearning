#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from pathlib import Path

ROOT = Path.home() / "relearning" / "lang" / "python" / "quiet_logos"
LOG_DIR = ROOT / "log"


def today_str() -> str:
    return date.today().isoformat()


def ensure_dirs() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def prompt_line(title: str) -> str:
    s = input(title).strip()
    return s


def write_entry(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def main() -> None:
    ensure_dirs()

    d = today_str()
    out_path = LOG_DIR / f"{d}.md"

    # 1) Тихая запись (поэтика)
    quiet = prompt_line("quiet> ")

    # 2) Техническая нить (связь с языками/ИИ/практикой)
    tech = prompt_line("tech> ")

    content = f"""# quiet_logos — {d}

## quiet

{quiet}

## tech

{tech}
"""

    write_entry(out_path, content)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
