from pathlib import Path
import markdown

SRC = Path("docs/log")
TEMPLATE = SRC / "_template.html"

def render(md_path):
    html_body = markdown.markdown(md_path.read_text(encoding="utf-8"))
    template = TEMPLATE.read_text(encoding="utf-8")
    return template.replace("{{ content }}", html_body)

def main():
    for md in SRC.glob("*.md"):
        html = render(md)
        out = md.with_suffix(".html")
        out.write_text(html, encoding="utf-8")
        print(f"built: {out}")

if __name__ == "__main__":
    main()
