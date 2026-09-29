"""Render the social images for one post.

Usage:
    python scripts/render_images.py posts/<slug>/post.json

Reads the post package, fills the chosen layout in templates/, and writes
instagram.png (4:5, also used for Facebook) and pinterest.png (2:3) next to post.json.
"""
import base64, html, mimetypes, pathlib, sys, urllib.request
from playwright.sync_api import sync_playwright
from common import ROOT, SIZES, LAYOUTS, config, load_json

TEMPLATES = ROOT / "templates"
FONTS = ROOT / "assets" / "fonts"

FONT_FACES = [
    ("Garamond", "normal", 400, "eb-garamond-latin-400-normal.woff2"),
    ("Garamond", "normal", 500, "eb-garamond-latin-500-normal.woff2"),
    ("Garamond", "italic", 400, "eb-garamond-latin-400-italic.woff2"),
    ("Garamond", "italic", 500, "eb-garamond-latin-500-italic.woff2"),
    ("Plex Mono", "normal", 400, "ibm-plex-mono-latin-400-normal.woff2"),
]

# Shrinks any .fit element until its .fitbox stops overflowing (long quotes/titles).
FIT_JS = """
() => {
  for (const box of document.querySelectorAll('.fitbox')) {
    const el = box.querySelector('.fit'); if (!el) continue;
    let size = parseFloat(getComputedStyle(el).fontSize), min = size * 0.5;
    while (box.scrollHeight > box.clientHeight + 1 && size > min) {
      size *= 0.95; el.style.fontSize = size + 'px';
    }
  }
}
"""


def data_uri(path):
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(pathlib.Path(path).read_bytes()).decode()}"


def font_css():
    return "\n".join(
        f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{w};src:url({data_uri(FONTS / f)}) format('woff2')}}"
        for fam, style, w, f in FONT_FACES)


def header_image(post, folder):
    """Download the post's header image once and return it as a data URI."""
    url = post.get("header_image")
    if not url:
        sys.exit("Layout 'photo' needs a header_image in post.json.")
    local = folder / "header.jpg"
    if not local.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        local.write_bytes(urllib.request.urlopen(req, timeout=30).read())
    return data_uri(local)


def fill(template, post, cfg, folder):
    values = {
        "title": post.get("title", ""),
        "subtitle": post.get("subtitle", ""),
        "quote": post.get("quote", ""),
        "label": post.get("label") or "New essay",
        "date_label": post.get("date_label", ""),
        "site": cfg.get("site_label", ""),
    }
    out = template
    for k, v in values.items():
        out = out.replace("{{" + k + "}}", html.escape(v))
    if "{{image_src}}" in out:
        out = out.replace("{{image_src}}", header_image(post, folder))
    return out


def main(post_path):
    post_path = pathlib.Path(post_path).resolve()
    folder = post_path.parent
    post, cfg = load_json(post_path), config()
    layout = post.get("layout")
    if layout not in LAYOUTS:
        sys.exit(f"post.json 'layout' must be one of {LAYOUTS}, got {layout!r}")

    body = fill((TEMPLATES / f"{layout}.html").read_text(), post, cfg, folder)
    base_css = (TEMPLATES / "base.css").read_text()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name, (w, h) in SIZES.items():
            page = browser.new_page(viewport={"width": w, "height": h})
            css = f"{font_css()}\n{base_css}\n:root{{--w:{w}px;--h:{h}px;--u:{w/100}px}}"
            page.set_content(f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head>{body}</html>")
            page.evaluate("document.fonts.ready")
            page.evaluate(FIT_JS)
            out = folder / f"{name}.png"
            page.screenshot(path=str(out))
            page.close()
            print(f"wrote {out.relative_to(ROOT)}")
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
