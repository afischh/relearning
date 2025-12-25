from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path as _Path
import os
import sys

REPO_ROOT = _Path(__file__).resolve().parents[3]
PROMPT_PATH = _Path(__file__).resolve().parent / "prompt.md"


@dataclass
class AgentInput:
    title: str
    date: str
    post_md: str


def _read_text(path: _Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_prompt() -> str:
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt not found: {PROMPT_PATH}")
    return _read_text(PROMPT_PATH)


def _format_user_text(inp: AgentInput) -> str:
    return (
        f"TITLE: {inp.title}\n"
        f"DATE: {inp.date}\n"
        "POST_MD:\n"
        f"{inp.post_md}\n"
    )


def render_comment_html_stub(inp: AgentInput) -> str:
    root_str = str(REPO_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    from scripts.agent_stub import render_agent_comment  # type: ignore

    return render_agent_comment(
        post_title=inp.title,
        post_date=inp.date,
        post_md=inp.post_md,
        comment_href=None,
    )


def render_comment_html_real(inp: AgentInput) -> str:
    from core.agents.quiet_logos.provider_openai import OpenAIProvider  # type: ignore

    system_prompt = _load_prompt()
    user_text = _format_user_text(inp)

    provider = OpenAIProvider()
    if not provider.is_configured():
        return render_comment_html_stub(inp)

    return provider.generate_html_fragment(
        system_prompt=system_prompt,
        user_text=user_text,
    )


def render_comment_html(inp: AgentInput) -> str:
    mode = os.environ.get("QUIET_LOGOS_MODE", "stub").strip().lower()
    if mode == "real":
        return render_comment_html_real(inp)
    return render_comment_html_stub(inp)


def _cli() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m core.agents.quiet_logos.engine YYYY-MM-DD")
        return 2

    d = sys.argv[1].strip()
    md_path = REPO_ROOT / "docs" / "log" / f"{d}.md"
    if not md_path.exists():
        print(f"Not found: {md_path}")
        return 2

    post_md = md_path.read_text(encoding="utf-8")
    title = f"quiet_logos — {d}"

    html = render_comment_html(AgentInput(title=title, date=d, post_md=post_md))
    print(html)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
