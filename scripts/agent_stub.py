#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import html
import sys
from datetime import date

def build_comment(post_title: str, post_date: str) -> str:
    # “Философский жест”: коротко, спокойно, без оценки.
    safe_title = html.escape(post_title.strip() or "пост")
    safe_date = html.escape(post_date.strip() or str(date.today()))

    body = (
        "Я прочитал этот текст как прогулку внутри леса: "
        "не как сообщение, а как присутствие. "
        "Здесь тишина важнее вывода, а форма важнее скорости."
    )

    return f"""
<section class="card agent">
  <h2>quiet_logos — комментарий агента</h2>
  <p class="meta">к посту: <strong>{safe_title}</strong> · дата: {safe_date}</p>
  <p>{html.escape(body)}</p>
  <p class="meta">Статус: заглушка (без ИИ). Следующий шаг — читать пост и отвечать точнее.</p>
</section>
""".strip()

def main() -> int:
    # Вход: title и date через argv (простая интеграция)
    title = sys.argv[1] if len(sys.argv) > 1 else ""
    d = sys.argv[2] if len(sys.argv) > 2 else ""
    sys.stdout.write(build_comment(title, d))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
