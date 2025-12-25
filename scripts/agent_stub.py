#!/usr/bin/env python3
from __future__ import annotations

import re
from collections import Counter


def _extract_sections(md_text: str) -> dict[str, str]:
    """
    Выделяет разделы вида:
    ## quiet
    ## tech

    Если таких блоков несколько (несколько записей за день),
    будет взят ПОСЛЕДНИЙ — это соответствует режиму "последнее состояние".
    """
    text = md_text.replace("\r\n", "\n").replace("\r", "\n")
    parts = re.split(r"\n##\s+", "\n" + text)

    sections: dict[str, str] = {}
    for part in parts:
        part = part.strip()
        if not part:
            continue

        lines = part.split("\n", 1)
        name = lines[0].strip().lower()
        body = lines[1].strip() if len(lines) > 1 else ""

        if name in ("quiet", "tech"):
            sections[name] = body

    return sections


def _keywords(md_text: str, limit: int = 5) -> list[str]:
    words = re.findall(r"[A-Za-zА-Яа-яЁё]{4,}", md_text.lower())
    counter = Counter(words)
    return [w for w, _ in counter.most_common(limit)]


def render_agent_comment(
    *,
    post_title: str,
    post_date: str,
    post_md: str,
    comment_href: str | None = None,
) -> str:
    """
    quiet_logos v1: агент-наблюдатель.

    На статическом сайте:
    - без "вопросов, требующих ответа"
    - без навязывания действий
    - только наблюдение формы + фиксация нитей
    """
    sections = _extract_sections(post_md)
    keys = _keywords(post_md)

    quiet_len = len(sections.get("quiet", "").strip())
    tech_len = len(sections.get("tech", "").strip())

    observations: list[str] = []

    if quiet_len and tech_len:
        observations.append("В записи присутствуют и тишина, и техническая часть.")
        if quiet_len > tech_len * 2:
            observations.append("Тишина сегодня заметно преобладает.")
        elif tech_len > quiet_len * 2:
            observations.append("Техническая часть сегодня доминирует.")
    elif quiet_len:
        observations.append("Запись почти целиком состоит из тишины.")
    elif tech_len:
        observations.append("Запись почти целиком техническая.")
    else:
        observations.append("Форма записи минимальна.")

    if keys:
        observations.append("Повторяющиеся нити: " + ", ".join(keys) + ".")

    obs_html = "".join(f"<p>{o}</p>" for o in observations)

    # Ссылка на отдельную страницу комментария уместна только на странице записи.
    link_html = ""
    if comment_href:
        link_html = f'<p><a href="{comment_href}">Комментарий Аристарха</a></p>'

    return f"""
<div class="card agent">
  <p><strong>quiet_logos</strong></p>
  <p>Я прочитал запись «{post_title}» от {post_date}.</p>
  {obs_html}
  {link_html}
</div>
"""
