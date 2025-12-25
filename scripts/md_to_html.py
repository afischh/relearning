#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys
import html

import markdown as mdlib


# --- Paths (repo-root relative) ---
REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = REPO_ROOT / "docs" / "log"
COMMENTS_DIR = LOG_DIR / "comments"
TEMPLATE_PATH = LOG_DIR / "_template.html"
INDEX_PATH = LOG_DIR / "index.html"

# Template placeholders:
# {{TITLE}}, {{CSS_HREF}}, {{CONTENT}}
# Agent placeholder:
# <!--AGENT_COMMENT-->

DATE_MD_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")


@dataclass
class Post:
    md_path: Path
    html_path: Path
    post_date: str   # YYYY-MM-DD
    title: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _extract_title(markdown_text: str, fallback: str) -> str:
    """
    If the first non-empty line is '# Title', use it.
    Otherwise fallback.
    """
    for line in markdown_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            return line[2:].strip() or fallback
        return fallback
    return fallback


def _load_template() -> str:
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")
    return _read_text(TEMPLATE_PATH)


def _render_markdown(markdown_text: str) -> str:
    return mdlib.markdown(
        markdown_text,
        extensions=[
            "fenced_code",
            "tables",
            "toc",
        ],
        output_format="html5",
    )


def _ensure_dirs() -> None:
    if not LOG_DIR.exists():
        raise FileNotFoundError(f"log dir not found: {LOG_DIR}")
    COMMENTS_DIR.mkdir(parents=True, exist_ok=True)


def _agent_comment_fragment(*, post_title: str, post_date: str, post_md: str) -> str:
    """
    Use new agent engine (stub by default; real if env enabled).
    Falls back to minimal safe HTML if engine raises.
    """
    root_str = str(REPO_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    try:
        from core.agents.quiet_logos.engine import AgentInput, render_comment_html  # type: ignore
        return render_comment_html(AgentInput(title=post_title, date=post_date, post_md=post_md))
    except Exception as e:
        esc = html.escape(str(e))
        return (
            '<div class="card agent">'
            "<p><strong>quiet_logos</strong></p>"
            f"<p><em>(агент недоступен: {esc})</em></p>"
            "</div>"
        )


def _wrap_comment_page(*, inner_html: str, post: Post) -> str:
    """
    Wraps comment fragment into a full HTML page.
    For docs/log/comments/*.html, css path is: ../../css/style.css
    """
    css_href = "../../css/style.css"
    title = f"quiet_logos — комментарий — {post.post_date}"

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="{css_href}" />
</head>
<body>
  <main class="container">
    <div class="card">
      <h1>Комментарий Аристарха</h1>
      <p><strong>{html.escape(post.post_date)}</strong></p>
      <p>
        <a href="../{post.post_date}.html">← К записи</a>
        &nbsp;·&nbsp;
        <a href="../index.html">Лента</a>
      </p>
    </div>

    {inner_html}

    <div class="card">
      <p><a href="../{post.post_date}.html">← К записи</a></p>
    </div>
  </main>
</body>
</html>
"""


def _write_comment_page(*, post: Post, comment_fragment_html: str) -> Path:
    """
    Writes docs/log/comments/YYYY-MM-DD_aristarkh.html
    """
    out_path = COMMENTS_DIR / f"{post.post_date}_aristarkh.html"
    page = _wrap_comment_page(inner_html=comment_fragment_html, post=post)
    _write_text(out_path, page)
    return out_path


def _build_posts() -> list[Post]:
    posts: list[Post] = []

    for md_path in sorted(LOG_DIR.glob("*.md")):
        if not DATE_MD_RE.match(md_path.name):
            continue

        post_date = md_path.stem  # YYYY-MM-DD
        html_path = LOG_DIR / f"{post_date}.html"

        md_text = _read_text(md_path)
        title = _extract_title(md_text, fallback=f"quiet_logos — {post_date}")

        posts.append(Post(md_path=md_path, html_path=html_path, post_date=post_date, title=title))

    posts.sort(key=lambda p: p.post_date, reverse=True)
    return posts


def _render_post_html(template: str, post: Post, css_href: str) -> str:
    md_text = _read_text(post.md_path)
    content_html = _render_markdown(md_text)

    # 1) Generate comment fragment (stub by default; real if enabled via env)
    comment_fragment_html = _agent_comment_fragment(
        post_title=post.title,
        post_date=post.post_date,
        post_md=md_text,
    )

    # 2) Write separate comment page (artifact)
    comment_page_path = _write_comment_page(post=post, comment_fragment_html=comment_fragment_html)

    # 3) Embed agent fragment and a link to the separate file
    comment_href = f"comments/{comment_page_path.name}"
    agent_block = (
        f"{comment_fragment_html}\n"
        f'<div class="card"><p><a href="{comment_href}">Комментарий Аристарха (файл)</a></p></div>'
    )

    # 4) Render full page using template
    page_html = template
    page_html = page_html.replace("{{TITLE}}", post.title)
    page_html = page_html.replace("{{CSS_HREF}}", css_href)
    page_html = page_html.replace("{{CONTENT}}", content_html)
    page_html = page_html.replace("<!--AGENT_COMMENT-->", agent_block)

    return page_html


def _render_log_index(posts: list[Post], css_href: str) -> str:
    items = []
    for p in posts:
        items.append(f'<li><a href="{p.post_date}.html">{p.post_date} — {html.escape(p.title)}</a></li>')

    items_html = "\n      ".join(items) if items else "<li><em>Пока нет записей.</em></li>"

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>quiet_logos — дневник</title>
  <link rel="stylesheet" href="{css_href}" />
</head>
<body>
  <main class="container">
    <div class="card">
      <h1>quiet_logos — дневник</h1>
      <p><a href="../index.html">← На главную</a></p>
    </div>

    <div class="card">
      <h2>Лента</h2>
      <ul>
      {items_html}
      </ul>
    </div>
  </main>
</body>
</html>
"""


def main() -> int:
    try:
        _ensure_dirs()
    except Exception as e:
        print(f"ERROR: {e}")
        return 2

    template = _load_template()
    posts = _build_posts()

    # From docs/log/*.html to css: "../css/style.css"
    css_href_posts = "../css/style.css"

    for p in posts:
        html_page = _render_post_html(template=template, post=p, css_href=css_href_posts)
        _write_text(p.html_path, html_page)
        print(f"OK: {p.md_path.name} -> {p.html_path.name} (+ comment: {p.post_date}_aristarkh.html)")

    log_index_html = _render_log_index(posts=posts, css_href=css_href_posts)
    _write_text(INDEX_PATH, log_index_html)
    print("Updated: docs/log/index.html")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
