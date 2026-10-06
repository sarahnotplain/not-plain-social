"""Render standalone Pinterest pins (not tied to an essay): the free case-files guide and the
Bookshop lists. Pins and their captions live in posts/pinterest-extras/pins.json.

Usage: .venv/bin/python scripts/render_pins.py
"""
import html
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import ROOT  # noqa: E402
from render_images import FIT_JS, data_uri, font_css  # noqa: E402

FOLDER = ROOT / "posts" / "pinterest-extras"
W, H = 1000, 1500

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
{fonts}
{base}
:root {{ --w: {w}px; --h: {h}px; --u: {u}px; }}
body {{ background: var(--cream); }}
.label {{ color: var(--accent); font-size: calc(var(--u)*2.4); }}
.title {{ font-size: calc(var(--u)*10.5); line-height: 1.05; font-weight: 500; color: var(--ink); }}
.sub {{ font-style: italic; font-size: calc(var(--u)*4.4); line-height: 1.3; color: var(--muted); margin-top: calc(var(--u)*3); }}
.rule {{ width: calc(var(--u)*12); height: 3px; background: var(--lavender); margin: calc(var(--u)*5) 0; }}
.items {{ list-style: none; font-size: calc(var(--u)*5.2); line-height: 1.35; }}
.items li {{ padding: calc(var(--u)*1.6) 0; border-bottom: 1px solid var(--rule); display: flex; align-items: baseline; }}
.items li span {{ font-family: "Plex Mono", monospace; font-size: calc(var(--u)*2.6); color: var(--accent); margin-right: calc(var(--u)*2.4); letter-spacing: .1em; flex-shrink: 0; }}
.quote {{ font-style: italic; font-size: calc(var(--u)*5.6); line-height: 1.35; color: var(--ink); background: #fbf8f2; border-left: 4px solid var(--lavender); padding: calc(var(--u)*4); }}
</style></head><body>
<div class="abs fitbox" style="left: calc(var(--u)*9); right: calc(var(--u)*9); top: calc(var(--u)*9); bottom: calc(var(--u)*22); justify-content: center">
  <div class="fit">
    <div class="mono label">{label}</div>
    <div class="title" style="margin-top: calc(var(--u)*3.5)">{title}</div>
    {sub}
    <div class="rule"></div>
    {body}
  </div>
</div>
<div class="abs" style="left: calc(var(--u)*9); right: calc(var(--u)*9); bottom: calc(var(--u)*8); display: flex; align-items: center; gap: calc(var(--u)*3)">
  <img class="logo" src="{logo}" alt="">
  <div>
    <div class="brand">Not Plain</div>
    <div class="mono" style="color: var(--muted); margin-top: calc(var(--u)*1)">{footer}</div>
  </div>
</div>
</body></html>"""


def body_html(pin):
    if pin.get("items"):
        lis = "".join(f"<li><span>{i:02d}</span>{html.escape(t)}</li>" for i, t in enumerate(pin["items"], 1))
        return f'<ul class="items">{lis}</ul>'
    return f'<div class="quote">{html.escape(pin["quote"])}</div>'


def main():
    spec = json.loads((FOLDER / "pins.json").read_text())
    base = (ROOT / "templates" / "base.css").read_text()
    logo = data_uri(ROOT / "assets" / "logo.png")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        for pin in spec["pins"]:
            sub = f'<div class="sub">{html.escape(pin["sub"])}</div>' if pin.get("sub") else ""
            page.set_content(PAGE.format(fonts=font_css(), base=base, w=W, h=H, u=W / 100,
                                         label=html.escape(pin["label"]), title=html.escape(pin["title_image"]),
                                         sub=sub, body=body_html(pin), logo=logo,
                                         footer=html.escape(pin["footer"])))
            page.wait_for_timeout(300)
            page.evaluate(FIT_JS)
            out = FOLDER / pin["file"]
            page.screenshot(path=str(out))
            print("wrote", out.relative_to(ROOT))
        browser.close()


if __name__ == "__main__":
    main()
