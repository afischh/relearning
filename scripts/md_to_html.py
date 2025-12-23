#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import date
import re
import sys

import markdown


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_LOG_DIR = REPO_ROOT / "docs" / "log"
TEMPLATE_PATH = DOCS_LOG_DIR / "_template.html"
INDEX_PATH = DOCS_LOG_DIR / "index.html"


def slug_title_from_md(text: str) -> str:
    """
    Берём самый верхний H1 вида:
      # quiet_logos — 2025-12-23
    и превращаем в аккуратный title для html.
    """
    m = re.search(r"^#\s+(.+)\s*$", text, flags=re.MULTILINE)
    return m.group(1).strip() if m else "quiet_logos"


def md_to_html_body(md_text: str) -> str:
    return markdown.markdown(
        md_text,
        extensions=[
            "fenced_code",
            "tables",
            "toc",
            "smarty",
        ],
        output_format="html5",
    )


def render_page(title: str, body_html: str, css_href: str = "../css/style.css") -> str:
    if not TEMPLATE_PATH.exists():
        # запасной минимальный шаблон, если _template.html вдруг не найден
        return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="stylesheet" href="{css_href}" />
</head>
<body>
  <main class="container">
    <div class="card">{body_html}</div>
  </main>
</body>
</html>
"""

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Ожидаем, что в шаблоне есть маркеры:
    # {{TITLE}} и {{CONTENT}}
    return (
        template.replace("{{TITLE}}", title)
                .replace("{{CONTENT}}", body_html)
                .replace("{{CSS_HREF}}", css_href)
    )


def update_log_index(link_text: str, html_filename: str) -> None:
    """
    Обновляем docs/log/index.html так, чтобы в ленте была только последняя запись.
    (как ты и решил)
    """
    li = f'    <li><a href="{html_filename}">{link_text}</a></li>\n'

    if not INDEX_PATH.exists():
        INDEX_PATH.write_text(
            "<!doctype html>\n<html lang=\"ru\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>quiet_logos — дневник</title>"
            "<link rel=\"stylesheet\" href=\"../css/style.css\"></head><body>"
            "<main class=\"container\"><h1>quiet_logos — дневник</h1><ul>\n"
            f"{li}"
            "</ul></main></body></html>\n",
            encoding="utf-8",
        )
        return

    text = INDEX_PATH.read_text(encoding="utf-8")

    # Находим первый <ul> ... </ul> и заменяем содержимое на один элемент.
    m = re.search(r"(<ul[^>]*>\s*)(.*?)(\s*</ul>)", text, flags=re.DOTALL | re.IGNORECASE)
    if not m:
        # если структура неожиданная — просто допишем в конец body
        new_text = text + "\n<ul>\n" + li + "</ul>\n"
    else:
        new_text = text[: m.start(2)] + li + text[m.end(2) :]

    INDEX_PATH.write_text(new_text, encoding="utf-8")


def main() -> int:
    DOCS_LOG_DIR.mkdir(parents=True, exist_ok=True)

    md_path = DOCS_LOG_DIR / f"{date.today().isoformat()}.md"
    if len(sys.argv) >= 2:
        md_path = Path(sys.argv[1]).expanduser().resolve()

    if not md_path.exists():
        print(f"MD file not found: {md_path}")
        return 2

    md_text = md_path.read_text(encoding="utf-8")
    title = slug_title_from_md(md_text)
    body_html = md_to_html_body(md_text)

    # Пишем рядом html с тем же именем даты
    html_path = md_path.with_suffix(".html")
    html_text = render_page(title=title, body_html=body_html, css_href="../css/style.css")
    html_path.write_text(html_text, encoding="utf-8")

    # Обновляем ленту (только последняя запись)
    # В ссылке оставим твой стиль заголовка H1, но без '#'
    update_log_index(link_text=title, html_filename=html_path.name)

    print(f"OK: {md_path.name} -> {html_path.name}")
    print(f"Updated: {INDEX_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
