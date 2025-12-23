#!/usr/bin/env python3
"""
md_to_html.py
Конвертирует markdown-дневник в HTML для сайта quiet_logos.
"""

from pathlib import Path
import markdown
from datetime import date

# Пути
ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "docs" / "log"
TEMPLATE_FILE = LOG_DIR / "_template.html"
INDEX_FILE = LOG_DIR / "index.html"

def render_md(md_path: Path, template: str) -> str:
    html_body = markdown.markdown(
        md_path.read_text(encoding="utf-8"),
        extensions=["fenced_code", "tables"]
    )
    return template.replace("{{ content }}", html_body).replace(
        "{{ title }}", md_path.stem
    )

def main():
    today = date.today().isoformat()
    md_file = LOG_DIR / f"{today}.md"
    html_file = LOG_DIR / f"{today}.html"

    if not md_file.exists():
        print(f"Нет файла: {md_file.name}")
        return

    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    html = render_md(md_file, template)

    html_file.write_text(html, encoding="utf-8")
    print(f"OK: {md_file.name} -> {html_file.name}")

    # обновляем index.html
    entries = sorted(
        p for p in LOG_DIR.glob("*.html") if p.name != "index.html"
    )
    items = "\n".join(
        f'<li><a href="{p.name}">{p.stem}</a></li>' for p in reversed(entries)
    )

    index_html = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>quiet_logos — дневник</title>
<link rel="stylesheet" href="../css/style.css">
</head>
<body>
<main class="card">
<h1>quiet_logos</h1>
<ul>
{items}
</ul>
</main>
</body>
</html>
"""

    INDEX_FILE.write_text(index_html, encoding="utf-8")
    print("Updated: docs/log/index.html")

if __name__ == "__main__":
    main()
