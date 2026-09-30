"""Render the social images for one post.

Usage:
    python scripts/render_images.py posts/<slug>/post.json      (or post-2.json, post-3.json)

An optional "theme" in post.json ({"logo": file next to post.json, "site": label,
"css": ":root{--cream:...}"}) restyles the images, e.g. for client mockups.

Reads the post package, fills the chosen layout in templates/, and writes
instagram.png (4:5, also used for Facebook) and pinterest.png (2:3) next to post.json.
Variants (post-2.json) get matching names (instagram-2.png).

If post.json has a "carousel", its slides are also rendered (instagram-s1.png, -s2.png ...)
from templates/carousel/. Instagram gets the carousel; Facebook and Pinterest keep the single image.
"""
import base64, hashlib, html, mimetypes, pathlib, sys, urllib.request
from playwright.sync_api import sync_playwright
from common import ROOT, SIZES, LAYOUTS, config, image_name, load_json, slide_names

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
        sys.exit("This layout needs a header_image in post.json.")
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
        "site": (post.get("theme") or {}).get("site") or cfg.get("site_label", ""),
    }
    out = template
    for k, v in values.items():
        # Keep dashes on the line with the word before them, never starting a new line.
        v = html.escape(v).replace(" —", "&nbsp;—").replace(" –", "&nbsp;–")
        out = out.replace("{{" + k + "}}", v)
    if "{{logo_src}}" in out:
        logo = (post.get("theme") or {}).get("logo")
        out = out.replace("{{logo_src}}", data_uri(folder / logo if logo else ROOT / "assets" / "logo.png"))
    if "{{image_src}}" in out:
        out = out.replace("{{image_src}}", header_image(post, folder))
    return out


def sub(template, values):
    """Fill {{key}}. Keys ending in _html, _css or _only are inserted as-is; everything else is escaped."""
    for k, v in values.items():
        v = str(v)
        if not k.endswith(("_html", "_css", "_only")):
            v = html.escape(v).replace(" —", "&nbsp;—").replace(" –", "&nbsp;–")
        template = template.replace("{{" + k + "}}", v)
    return template


BG = {  # slide background -> (background, text, small labels)
    "cream": ("var(--cream)", "var(--ink)", "var(--accent)"),
    "lavender": ("var(--lavender)", "var(--cream)", "#ECE7F2"),
    "black": ("var(--black)", "var(--cream)", "#A9A29A"),
}


def carousel_bodies(post, cfg, folder, reel=False):
    """One HTML body per carousel slide (see the carousel section of the share-new-posts skill).
    reel=True drops "Swipe" and the slide counters, for the video version (render_reel.py)."""
    c = post["carousel"]
    slides = c["slides"]
    art = header_image(post, folder) if post.get("header_image") else None
    lines = [s for s in slides if s.get("kind", "line") == "line"]
    site = (post.get("theme") or {}).get("site") or cfg.get("site_label", "")
    logo = data_uri(ROOT / "assets" / "logo.png")
    out = []
    for i, s in enumerate(slides, 1):
        kind = s.get("kind", "line")
        has_art = bool(art) and s.get("art", True)
        if not has_art:
            art_css = "display: none"
        elif c.get("panorama") and kind == "line":
            # One painting panning across the middle slides.
            k = lines.index(s)
            x = 0 if len(lines) == 1 else round(100 * k / (len(lines) - 1))
            art_css = f"background: url('{art}') {x}% {s.get('y', '50%')}/{len(lines) * 100}% auto no-repeat; filter: saturate(.9)"
        else:
            # zoom: the hook's tall strip scales by height (so wide paintings still fill it); the others by width.
            zoom = s.get("zoom", {"hook": 125, "line": 250, "end": 150}.get(kind, 200))
            size = f"auto {zoom}%" if kind == "hook" else f"{zoom}% auto"
            art_css = f"background: url('{art}') {s.get('crop', '50% 30%')}/{size} no-repeat; filter: saturate(.9)"
        bg, fg, soft = BG[s.get("bg", "cream")]
        v = {"text": s.get("text", ""), "label": s.get("label", ""), "number": s.get("number", f"{i - 1:02d}"),
             "eyebrow": s.get("eyebrow", ""), "counter": "" if reel else f"{i} / {len(slides)}",
             "swipe_css": "display: none" if reel else "", "site": site, "title": post.get("title", ""),
             "logo_src": logo, "art_css": art_css, "art_only": "" if has_art else "display: none",
             "bg": bg, "fg": fg, "soft": soft, "tilt": ["-2deg", "1.6deg", "-1deg", "2.2deg"][i % 4]}
        if kind == "hook":
            items = s.get("list", [])
            v["list_html"] = "".join(
                f'<div class="mono" style="font-size: calc(var(--u)*2.6); color: var(--cream)">'
                f'<span style="color: var(--lavender)">{n:02d}</span>&nbsp;&nbsp;{html.escape(t)}</div>'
                for n, t in enumerate(items, 1))
            v["text_width"] = "60%" if has_art else "84%"
            v["text_bottom"] = 22 + 5 * len(items) if items else 22
        elif kind == "line":
            v["text_top"] = "47%" if has_art else "calc(var(--u)*30)"
            v["number_top"] = "calc(47% - var(--u)*19)" if has_art else "calc(var(--u)*9)"
            v["number_color"] = "var(--cream)" if has_art else soft
            v["number_shadow"] = "0 2px 18px rgba(0,0,0,.35)" if has_art else "none"
        elif kind == "end":
            v["end_top"] = "40%" if has_art else "30%"
            default = ("Subscribe to read the rest of " if post.get("looks_paywalled") else "Read the rest in ")
            v["cta_html"] = html.escape(s.get("cta") or default) + f'<span style="color: var(--cream)">{html.escape(post.get("title", ""))}</span>. Link in bio.'
        out.append(sub((TEMPLATES / "carousel" / f"{kind}.html").read_text(), v))
    return out


def main(post_path):
    post_path = pathlib.Path(post_path).resolve()
    folder = post_path.parent
    post, cfg = load_json(post_path), config()
    layout = post.get("layout")
    if layout not in LAYOUTS:
        sys.exit(f"post.json 'layout' must be one of {LAYOUTS}, got {layout!r}")

    body = fill((TEMPLATES / f"{layout}.html").read_text(), post, cfg, folder)
    base_css = page_css(post, post_path)

    jobs = [(body, SIZES[name], image_name(post_path, name)) for name in SIZES]
    if post.get("carousel"):
        jobs += list(zip(carousel_bodies(post, cfg, folder), [SIZES["instagram"]] * 99, slide_names(post_path, post)))

    shoot(jobs, base_css, folder)


def page_css(post, post_path):
    """base.css plus the per-post print tilt and any per-package theme."""
    # Optional per-package theme (used for client mockups): extra CSS that overrides the color tokens.
    # The print tilt varies per post (stable, so re-renders match).
    tilt = [-2.2, 1.8, -1.3, 2.5][int(hashlib.md5(post_path.name.encode() + post.get("slug", "").encode()).hexdigest(), 16) % 4]
    return ((TEMPLATES / "base.css").read_text()
            + f"\n:root{{--tilt:{tilt}deg}}\n" + (post.get("theme") or {}).get("css", ""))


def reel_slides(post_path, out_dir):
    """Render the carousel slides without "Swipe" or counters into out_dir; returns the paths."""
    post_path = pathlib.Path(post_path).resolve()
    post, cfg = load_json(post_path), config()
    bodies = carousel_bodies(post, cfg, post_path.parent, reel=True)
    names = [f"s{i}.png" for i in range(1, len(bodies) + 1)]
    shoot(list(zip(bodies, [SIZES["instagram"]] * 99, names)), page_css(post, post_path), out_dir)
    return [out_dir / n for n in names]


def shoot(jobs, base_css, folder):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for body_html, (w, h), filename in jobs:
            page = browser.new_page(viewport={"width": w, "height": h})
            css = f"{font_css()}\n{base_css}\n:root{{--w:{w}px;--h:{h}px;--u:{w/100}px}}"
            page.set_content(f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head>{body_html}</html>")
            page.evaluate("document.fonts.ready")
            page.evaluate(FIT_JS)
            out = folder / filename
            page.screenshot(path=str(out))
            page.close()
            print(f"wrote {out.relative_to(ROOT)}")
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
