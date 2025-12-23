#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS = os.path.join(ROOT, "docs")
LOG_DIR = os.path.join(DOCS, "log")
MD_TO_HTML = os.path.join(ROOT, "scripts", "md_to_html.py")

HTML_FORM = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>quiet_logos — новая запись</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 24px; max-width: 900px; margin: 0 auto; }
    .card { border: 2px solid #6b0f1a; padding: 16px; border-radius: 12px; }
    label { display:block; margin: 12px 0 6px; font-weight: 600; }
    input[type="text"], textarea { width: 100%; padding: 10px; border: 1px solid #111; border-radius: 8px; }
    textarea { min-height: 220px; }
    .row { display:flex; gap:12px; }
    .row > div { flex:1; }
    button { margin-top: 14px; padding: 10px 14px; border: 1px solid #111; border-radius: 10px; cursor: pointer; }
    small { opacity: .75; }
    code { background:#f3f3f3; padding:2px 6px; border-radius:6px; }
  </style>
</head>
<body>
  <h1>quiet_logos — __TODAY__</h1>
  <p><small>Локальная форма. Сохраняет <code>docs/log/YYYY-MM-DD.md</code>, затем запускает конвертацию и обновляет ленту.</small></p>

  <div class="card">
    <form method="post" action="/submit">
      <div class="row">
        <div>
          <label>Дата (YYYY-MM-DD)</label>
          <input name="d" type="text" value="{today}" />
        </div>
        <div>
          <label>Заголовок (кратко)</label>
          <input name="title" type="text" placeholder="например: Prolog, тишина и уважение к логике" />
        </div>
      </div>

      <label>quiet</label>
      <textarea name="quiet" placeholder="Тишина, наблюдение, поэтика, воздух..."></textarea>

      <label>tech</label>
      <textarea name="tech" placeholder="Что сделал руками: команды, мысли, планы..."></textarea>

      <button type="submit">Сохранить → конвертировать → обновить ленту</button>
    </form>
  </div>

  <p style="margin-top:16px;">
    <small>После сохранения откроешь: <code>docs/log/index.html</code> и новую страницу записи.</small>
  </p>
</body>
</html>
"""

def ensure_dirs() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)

def write_md(d: str, title: str, quiet: str, tech: str) -> str:
    ensure_dirs()
    md_path = os.path.join(LOG_DIR, f"{d}.md")
    header = f"# quiet_logos — {d}\n\n"
    if title.strip():
        header += f"**{title.strip()}**\n\n"
    body = (
        "## quiet\n\n" + (quiet.strip() + "\n\n" if quiet.strip() else "_..._\n\n") +
        "## tech\n\n"  + (tech.strip()  + "\n\n" if tech.strip()  else "_..._\n\n")
    )
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(header + body)
    return md_path

def run_md_to_html() -> None:
    # Запускаем тем же интерпретатором, что и сервер (важно для venv)
    subprocess.check_call([os.environ.get("PYTHON", "python"), MD_TO_HTML], cwd=ROOT)

class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, content: str, ctype: str = "text/html; charset=utf-8") -> None:
        data = content.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/write"):
            self._send(200, HTML_FORM.replace("__TODAY__", str(date.today())))
            return
        self._send(404, "<h1>404</h1>")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/submit":
            self._send(404, "<h1>404</h1>")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        form = parse_qs(raw)

        d = (form.get("d", [""])[0] or str(date.today())).strip()
        title = (form.get("title", [""])[0]).strip()
        quiet = (form.get("quiet", [""])[0])
        tech = (form.get("tech", [""])[0])

        md_path = write_md(d, title, quiet, tech)
        try:
            run_md_to_html()
        except Exception as e:
            self._send(500, f"<h1>Ошибка конвертации</h1><pre>{e}</pre>")
            return

        html_path = f"/relearning/docs/log/{d}.html"
        index_path = "/relearning/docs/log/index.html"

        msg = f"""
        <h1>Готово</h1>
        <p>Создано: <code>{md_path}</code></p>
        <ul>
          <li>Открой ленту: <code>{LOG_DIR}/index.html</code></li>
          <li>Открой запись: <code>{LOG_DIR}/{d}.html</code></li>
        </ul>
        <p><a href="/write">написать ещё</a></p>
        """
        self._send(200, msg)

def main() -> None:
    host = "127.0.0.1"
    port = 8008
    httpd = HTTPServer((host, port), Handler)
    print(f"quiet_logos form: http://{host}:{port}/write")
    httpd.serve_forever()

if __name__ == "__main__":
    main()
