#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import re
import sys

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
AGENT_BLOCK_RE = re.compile(r'(<div class="card agent">.*?</div>)', re.DOTALL)


@dataclass
class Post:
    md_path: Path
    html_path: Path
    post_date: str   # YYYY-MM-DD
    title: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _extract_title(markdown_text: str, fallback: str) -> str:
    """
    If the first non-empty line is '# Title', use it. Otherwise fallback.
    """
    for line in markdown_text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("# "):
            return s[2:].strip() or fallback
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


def _wrap_comment_page(*, inner_html: str, post_date: str) -> str:
    """
    Делает из HTML-фрагмента (карточка агента) полноценную страницу комментария.
    Из docs/log/comments/*.html CSS путь: ../../css/style.css
    """
    css_href = "../../css/style.css"
    title = f"Aristarkh — comment — {post_date}"

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
    <div class="card">
      <h1>Комментарий Аристарха</h1>
      <p>
        <a href="../{post_date}.html">К записи</a>
        &nbsp;·&nbsp;
        <a href="../index.html">Лента</a>
      </p>
    </div>

    {inner_html}

  </main>
</body>
</html>
"""


def _render_agent_block(*, post_title: str, post_date: str, post_md: str) -> str:
    """
    Вызывает scripts/agent_stub.py -> render_agent_comment().
    Работает даже если scripts не пакет.
    """
    root_str = str(REPO_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    try:
        from scripts.agent_stub import render_agent_comment  # type: ignore
        return render_agent_comment(
            post_title=post_title,
            post_date=post_date,
            post_md=post_md,
        )
    except Exception as e:
        return (
            '<div class="card agent">'
            "<p><strong>Аристарх</strong></p>"
            f"<p><em>(агент недоступен: {e})</em></p>"
            "</div>"
        )


def _extract_agent_block_from_comment_page(comment_page_html: str) -> str | None:
    """
    Достаём из полной HTML-страницы комментария только карточку агента.
    """
    m = AGENT_BLOCK_RE.search(comment_page_html)
    return m.group(1) if m else None


def _agent_block_from_existing_comment(post_date: str) -> str | None:
    """
    Если комментарий уже существует (docs/log/comments/YYYY-MM-DD_aristarkh.html),
    возвращаем карточку агента, чтобы не дергать API заново.
    """
    comment_path = COMMENTS_DIR / f"{post_date}_aristarkh.html"
    if not comment_path.exists():
        return None
    html = _read_text(comment_path)
    return _extract_agent_block_from_comment_page(html)


def _build_posts() -> list[Post]:
    posts: list[Post] = []

    for md_path in sorted(LOG_DIR.glob("*.md")):
        if not DATE_MD_RE.match(md_path.name):
            continue

        post_date = md_path.stem
        html_path = LOG_DIR / f"{post_date}.html"

        md_text = _read_text(md_path)
        title = _extract_title(md_text, fallback=f"quiet_logos — {post_date}")
        posts.append(Post(md_path=md_path, html_path=html_path, post_date=post_date, title=title))

    posts.sort(key=lambda p: p.post_date, reverse=True)  # newest first
    return posts


def _render_post_html(*, template: str, post: Post, css_href: str, agent_html_inline: str) -> str:
    md_text = _read_text(post.md_path)
    content_html = _render_markdown(md_text)

    page_html = template
    page_html = page_html.replace("{{TITLE}}", post.title)
    page_html = page_html.replace("{{CSS_HREF}}", css_href)
    page_html = page_html.replace("{{CONTENT}}", content_html)
    page_html = page_html.replace("<!--AGENT_COMMENT-->", agent_html_inline)

    return page_html


def _render_log_index(posts: list[Post], css_href: str) -> str:
    items = []
    for p in posts:
        items.append(f'<li><a href="{p.post_date}.html">{p.post_date} — {p.title}</a></li>')
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
      <p><a href="../index.html">На главную</a></p>
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
    parser = argparse.ArgumentParser(description="Build quiet_logos site from markdown.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--agent-latest-only", action="store_true", help="Regenerate agent comment only for the newest post.")
    mode.add_argument("--agent-all", action="store_true", help="Regenerate agent comments for ALL posts.")
    args = parser.parse_args()

    if not LOG_DIR.exists():
        print(f"ERROR: log dir not found: {LOG_DIR}")
        return 2

    template = _load_template()
    posts = _build_posts()
    if not posts:
        print("No posts found in docs/log/*.md")
        _write_text(INDEX_PATH, _render_log_index(posts=[], css_href="../css/style.css"))
        return 0

    # default: in GitHub Actions => latest only; locally => all (меньше сюрпризов)
    if args.agent_latest_only:
        agent_latest_only = True
    elif args.agent_all:
        agent_latest_only = False
    else:
        agent_latest_only = (str(Path.cwd()) != "" and (("GITHUB_ACTIONS" in dict(**{}) ) ))  # dummy line, replaced below

    # правильное определение без "магии"
    if not (args.agent_latest_only or args.agent_all):
        agent_latest_only = (("GITHUB_ACTIONS" in __import__("os").environ) and (__import__("os").environ.get("GITHUB_ACTIONS") == "true"))

    COMMENTS_DIR.mkdir(parents=True, exist_ok=True)

    css_href_posts = "../css/style.css"
    newest_date = posts[0].post_date

    for p in posts:
        md_text = _read_text(p.md_path)

        regen_this = (not agent_latest_only) or (p.post_date == newest_date)

        if regen_this:
            # генерируем свежий агентский блок
            agent_block = _render_agent_block(post_title=p.title, post_date=p.post_date, post_md=md_text)
            # пишем отдельную страницу комментария (на будущее/архив)
            comment_page = _wrap_comment_page(inner_html=agent_block, post_date=p.post_date)
            comment_path = COMMENTS_DIR / f"{p.post_date}_aristarkh.html"
            _write_text(comment_path, comment_page)
            print(f"OK: comment regenerated: {comment_path.relative_to(REPO_ROOT)}")
        else:
            # не дергаем API — берём существующий блок
            agent_block = _agent_block_from_existing_comment(p.post_date) or (
                '<div class="card agent">'
                "<p><strong>Аристарх</strong></p>"
                "<p><em>(Комментарий сохранён ранее; пересборка только для последней записи.)</em></p>"
                "</div>"
            )

        # Встраиваем в пост только карточку (без ссылки “файл”)
        html = _render_post_html(template=template, post=p, css_href=css_href_posts, agent_html_inline=agent_block)
        _write_text(p.html_path, html)
        print(f"OK: {p.md_path.name} -> {p.html_path.name}")

    # индекс дневника
    _write_text(INDEX_PATH, _render_log_index(posts=posts, css_href=css_href_posts))
    print("Updated: docs/log/index.html")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
