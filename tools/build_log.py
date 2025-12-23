#!/usr/bin/env python3
# build_log.py — quiet_logos: md -> html + обновление ленты
# Без зависимостей. Работает на стандартном Python 3.

from __future__ import annotations
from pathlib import Path
from datetime import datetime
import re
import html

ROOT = Path(__file__).resolve().parents[1]          # ~/relearning
DOCS = ROOT / "docs"
LOG = DOCS / "log"
CSS_REL = "../css/style.css"                        # из log/*.html до css

TEMPLATE = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="{css}">
</head>
<body>
  <main class="wrap">
    <header class="card">
      <h1>{h1}</h1>
      <p class="muted">{subtitle}</p>
      <p><a href="index.html">← к дневнику</a> · <a href="../index.html">← на главную</a></p>
    </header>

    {content}

    <footer class="footer muted">
      <p>quiet_logos · generated {generated}</p>
    </footer>
  </main>
</body>
</html>
"""

def slug_date(p: Path) -> str:
    # 2025-12-23.md -> 2025-12-23
    return p.stem

def esc(s: str) -> str:
    return html.escape(s, quote=True)

def md_to_blocks(md: str) -> list[tuple[str, str]]:
    """
    Очень простой парсер:
    - # title
    - ## section_title
    - далее абзацы, списки "- "
    """
    lines = md.splitlines()
    title = ""
    sections: list[tuple[str, list[str]]] = []
    current_h2 = ""
    buf: list[str] = []

    def flush():
        nonlocal buf, current_h2
        if current_h2 and buf:
            sections.append((current_h2, buf))
        buf = []

    for raw in lines:
        line = raw.rstrip()

        if line.startswith("# "):
            title = line[2:].strip()
            continue

        if line.startswith("## "):
            flush()
            current_h2 = line[3:].strip()
            continue

        # пропускаем пустые строки как разделители абзацев, но сохраняем структуру
        buf.append(line)

    flush()

    blocks: list[tuple[str, str]] = []
    blocks.append(("__title__", title))
    for h2, body_lines in sections:
        blocks.append((h2, "\n".join(body_lines).strip()))
    return blocks

def body_to_html(text: str) -> str:
    """
    Поддержка:
    - абзацы
    - списки '- item'
    - пустые строки
    """
    if not text:
        return ""

    out: list[str] = []
    lines = text.splitlines()

    in_ul = False
    para: list[str] = []

    def flush_para():
        nonlocal para
        if para:
            out.append(f"<p>{esc(' '.join(para).strip())}</p>")
            para = []

    def ul_open():
        nonlocal in_ul
        if not in_ul:
            flush_para()
            out.append("<ul>")
            in_ul = True

    def ul_close():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for raw in lines:
        line = raw.strip()

        if not line:
            ul_close()
            flush_para()
            continue

        if line.startswith("- "):
            ul_open()
            out.append(f"<li>{esc(line[2:].strip())}</li>")
            continue

        # обычная строка -> часть абзаца
        ul_close()
        para.append(line)

    ul_close()
    flush_para()
    return "\n".join(out)

def md_file_to_html(md_path: Path) -> tuple[str, str]:
    md = md_path.read_text(encoding="utf-8")
    blocks = md_to_blocks(md)

    title = next((v for k, v in blocks if k == "__title__"), "").strip()
    if not title:
        title = f"quiet_logos — {slug_date(md_path)}"

    # пытаемся вытащить дату из имени файла
    date_str = slug_date(md_path)
    subtitle = date_str
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        subtitle = dt.strftime("%d.%m.%Y")
    except Exception:
        pass

    content_parts: list[str] = []
    for h2, body in blocks:
        if h2 == "__title__":
            continue
        section_html = body_to_html(body)
        if not section_html:
            continue
        content_parts.append(
            f"""<section class="card">
  <h2>{esc(h2)}</h2>
  {section_html}
</section>"""
        )

    if not content_parts:
        content_parts.append('<section class="card"><p class="muted">Пусто.</p></section>')

    html_out = TEMPLATE.format(
        title=esc(title),
        css=CSS_REL,
        h1=esc(title),
        subtitle=esc(subtitle),
        content="\n\n".join(content_parts),
        generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    return title, html_out

def update_index(entries: list[tuple[str, str]]):
    """
    entries: [(date, title), ...] — по убыванию даты
    Пишем docs/log/index.html (простая лента).
    """
    items = []
    for date, title in entries:
        items.append(
            f'<li><a href="{esc(date)}.html">{esc(date)} — {esc(title)}</a></li>'
        )

    page = f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>quiet_logos — дневник</title>
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>
  <main class="wrap">
    <header class="card">
      <h1>quiet_logos — дневник</h1>
      <p class="muted">Лента практики: языки, среды, агентное мышление.</p>
      <p><a href="../index.html">← на главную</a></p>
    </header>

    <section class="card">
      <h2>Записи</h2>
      <ul>
        {''.join(items)}
      </ul>
    </section>

    <footer class="footer muted">
      <p>generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    </footer>
  </main>
</body>
</html>
"""
    (LOG / "index.html").write_text(page, encoding="utf-8")

def main():
    if not DOCS.exists():
        raise SystemExit("Нет папки docs/. Запусти из репозитория ~/relearning.")

    LOG.mkdir(parents=True, exist_ok=True)

    md_files = sorted(LOG.glob("*.md"))
    if not md_files:
        print("Нет .md файлов в docs/log/")
        return

    entries: list[tuple[str, str]] = []
    for md_path in md_files:
        # пропускаем служебные файлы
        if md_path.name.startswith("_"):
            continue

        date = slug_date(md_path)
        title, html_out = md_file_to_html(md_path)
        out_path = LOG / f"{date}.html"
        out_path.write_text(html_out, encoding="utf-8")
        entries.append((date, title))

    # сортировка по дате (строка YYYY-MM-DD сортируется корректно)
    entries.sort(key=lambda x: x[0], reverse=True)
    update_index(entries)

    print(f"OK: built {len(entries)} pages + index.html")

if __name__ == "__main__":
    main()
