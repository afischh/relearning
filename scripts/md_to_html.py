#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import re
import sys
import subprocess
from pathlib import Path
from datetime import date

import markdown  # pip install markdown (внутри .venv)


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
LOG_DIR = DOCS_DIR / "log"
TEMPLATE_PATH = LOG_DIR / "_template.html"
LOG_INDEX_PATH = LOG_DIR / "index.html"
AGENT_PATH = REPO_ROOT / "scripts" / "agent_stub.py"

# Плейсхолдеры в шаблоне
PH_TITLE = "__TITLE__"
PH_DATE = "__DATE__"
PH_CONTENT = "__CONTENT__"
PH_AGENT = "<!--AGENT_COMMENT-->"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _extract_title_and_date(md_text: str, md_path: Path) -> tuple[str, str]:
    """
    Берём:
    - title: из первой строки заголовка '# ...' если есть, иначе из имени файла
    - date: из имени файла YYYY-MM-DD.md если совпадает, иначе today
    """
    # date from filename
    m = re.match(r"^(\d{4}-\d{2}-\d{2})\.md$", md_path.name)
    post_date = m.group(1) if m else str(date.today())

    # title from first markdown H1
    title = ""
    for line in md_text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            title = line[2:].strip()
            break

    if not title:
        title = md_path.stem

    return title, post_date


def _md_to_html(md_text: str) -> str:
    # Минимальный набор расширений (без “магии”)
    return markdown.markdown(
        md_text,
        extensions=["extra", "sane_lists", "smarty"],
        output_format="html5",
    )


def _agent_comment_html(title: str, post_date: str) -> str:
    """
    Вызывает scripts/agent_stub.py и получает готовый HTML-фрагмент.
    Если агент не запускается — возвращаем пустую строку.
    """
    if not AGENT_PATH.exists():
        return ""

    try:
        out = subprocess.check_output(
            [str(AGENT_PATH), title, post_date],
            text=True,
            cwd=str(REPO_ROOT),
        )
        return out.strip()
    except Exception:
        return ""


def build_one(md_path: Path) -> Path:
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")

    md_text = _read_text(md_path)
    title, post_date = _extract_title_and_date(md_text, md_path)

    # Контент поста: убираем первую строку '# ...' (чтобы не дублировать заголовок в теле)
    lines = md_text.splitlines()
    if lines and lines[0].lstrip().startswith("# "):
        body_md = "\n".join(lines[1:]).lstrip()
    else:
        body_md = md_text

    content_html = _md_to_html(body_md)
    template = _read_text(TEMPLATE_PATH)

    # Вставка агента (HTML-фрагмент)
    agent_html = _agent_comment_html(title, post_date)

    out_html = template
    out_html = out_html.replace(PH_TITLE, title)
    out_html = out_html.replace(PH_DATE, post_date)
    out_html = out_html.replace(PH_CONTENT, content_html)
    out_html = out_html.replace(PH_AGENT, agent_html)

    out_path = LOG_DIR / (md_path.stem + ".html")
    _write_text(out_path, out_html)
    return out_path


def rebuild_log_index() -> None:
    """
    Обновляет docs/log/index.html:
    - собирает все YYYY-MM-DD.html
    - сортирует по убыванию
    - выводит список ссылок
    """
    items = []
    for p in LOG_DIR.glob("*.html"):
        if p.name in ("index.html", "_template.html"):
            continue
        if re.match(r"^\d{4}-\d{2}-\d{2}\.html$", p.name):
            items.append(p)

    items.sort(reverse=True)  # по имени файла (дата) — убывание

    li = []
    for p in items:
        d = p.stem
        li.append(f'    <li><a href="{p.name}">{d}</a></li>')

    html = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Дневник</title>
  <link rel="stylesheet" href="../css/style.css" />
</head>
<body>
  <main class="wrap">
    <h1>Дневник практики</h1>
    <p class="meta"><a href="../index.html">← на главную</a></p>

    <section class="card">
      <h2>Лента</h2>
      <ul class="list">
{items}
      </ul>
    </section>
  </main>
</body>
</html>
""".replace("{items}", "\n".join(li) if li else "    <li>Пока пусто.</li>")

    _write_text(LOG_INDEX_PATH, html)


def main() -> int:
    if not LOG_DIR.exists():
        raise FileNotFoundError(f"Log dir not found: {LOG_DIR}")

    # Если файл не передан — берём сегодняшнюю дату
    if len(sys.argv) >= 2:
        md_file = sys.argv[1]
        md_path = Path(md_file)
        if not md_path.is_absolute():
            md_path = (LOG_DIR / md_path).resolve()
    else:
        md_path = (LOG_DIR / f"{date.today():%Y-%m-%d}.md").resolve()

    if not md_path.exists():
        raise FileNotFoundError(f"MD not found: {md_path}")

    out_path = build_one(md_path)
    print(f"OK: {md_path.name} -> {out_path.name}")

    rebuild_log_index()
    print("Updated: docs/log/index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
