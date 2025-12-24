#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import re


def _extract_threads(md_text: str) -> list[str]:
    words = re.findall(r"[A-Za-zА-Яа-яЁё]{4,}", md_text)
    return [w.lower() for w in words]


def render_agent_comment(*, post_title: str, post_date: str, post_md: str) -> str:
    threads = _extract_threads(post_md)
    cnt = Counter(threads)
    top = cnt.most_common(3)

    if top:
        threads_line = ", ".join([f"{w}×{n}" for w, n in top])
        threads_html = f"<p>Я вижу повторяющиеся нити: {threads_line}.</p>"
    else:
        threads_html = "<p>Я читаю запись внимательно. Нити пока не выделены.</p>"

    return f"""
<div class="card agent">
  <p><strong>quiet_logos</strong></p>
  <p>Я прочитал запись «{post_title}» от {post_date}.</p>
  {threads_html}
  <p><em>Вопрос:</em> Какой минимальный следующий шаг ты выбираешь сегодня: запись, сборка или маленькая правка кода?</p>
  <p><code>Следующий шаг:</code> python scripts/md_to_html.py</p>
</div>
"""
