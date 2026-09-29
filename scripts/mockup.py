"""Set up a sales mockup for another Substack writer.

ONLY run this after the writer has said yes to a mockup. Mockups stay private to that
writer, are never posted or reused without written permission, and get deleted if they
decline. Don't use their cover photo unless they confirm it's theirs to use.

Usage:
    python scripts/mockup.py https://substack.com/@handle      (or a publication URL, or @handle)

Writes to private/mockups/<subdomain>/ (never committed):
    brand.json            name, colors, logo, fonts
    logo.png              their publication logo
    <slug>/source.json    full text of each of their 3 most recent free posts
    <slug>/theme.json     the "theme" block to paste into a post.json

Then Claude writes <slug>/post.json (layout, exact quote, captions, "theme"), and
render_images.py renders it in their colors.
"""
import json, pathlib, re, sys, urllib.request
from check_feed import get, to_text
from common import ROOT, save_json

OUT = ROOT / "private" / "mockups"


def preloads(url):
    page = get(url).decode("utf-8", "ignore")
    m = re.search(r'window\._preloads\s*=\s*JSON\.parse\((".*?")\)', page, re.S)
    return json.loads(json.loads(m.group(1))) if m else {}


def mix(a, b, t):
    """Blend two #rrggbb colors; t=0 gives a, t=1 gives b."""
    a, b = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def resolve(arg):
    handle = re.search(r"@([\w.-]+)", arg)
    if handle:
        prof = json.loads(get(f"https://substack.com/api/v1/user/{handle.group(1)}/public_profile"))
        pub = prof["primaryPublication"]
        return pub.get("custom_domain") and f"https://{pub['custom_domain']}" or f"https://{pub['subdomain']}.substack.com"
    return arg.rstrip("/")


def main(arg):
    base = resolve(arg)
    pub = preloads(base + "/").get("pub", {})
    theme = pub.get("theme") or {}
    bg = theme.get("web_bg_color") or "#ffffff"
    accent = theme.get("background_pop_color") or pub.get("theme_var_background_pop") or "#222222"
    sub = pub.get("subdomain") or re.sub(r"\W+", "-", base)
    folder = OUT / sub
    folder.mkdir(parents=True, exist_ok=True)

    brand = {"name": pub.get("name"), "base": base, "bg": bg, "accent": accent,
             "heading_font": theme.get("font_preset_heading"), "body_font": theme.get("font_preset_body"),
             "logo_url": pub.get("logo_url"), "hero": pub.get("hero_text")}
    save_json(folder / "brand.json", brand)
    if brand["logo_url"]:
        (folder / "logo.png").write_bytes(get(brand["logo_url"]))

    css = (":root{" + f"--cream:{bg};--accent:{accent};--lavender:{accent};--black:{accent};"
           + f"--kraft:{mix(bg, accent, .25)};--ink:{mix('#111111', accent, .35)};"
           + f"--muted:{mix(accent, bg, .45)};--rule:{mix(bg, accent, .15)}" + "}")
    site = base.replace("https://", "")

    posts = [p for p in json.loads(get(base + "/api/v1/archive?sort=new&limit=12")) if p.get("audience") == "everyone"][:3]
    listing = []
    for p in posts:
        full = json.loads(get(f"{base}/api/v1/posts/{p['slug']}"))
        d = folder / p["slug"]
        save_json(d / "source.json", {"title": full.get("title"), "subtitle": full.get("subtitle"),
                                      "url": full.get("canonical_url"), "published": full.get("post_date"),
                                      "header_image": full.get("cover_image"), "text": to_text(full.get("body_html"))})
        save_json(d / "theme.json", {"logo": "../logo.png", "site": site, "css": css})
        listing.append({"slug": p["slug"], "title": full.get("title"), "has_cover": bool(full.get("cover_image"))})
    print(json.dumps({"folder": str(folder.relative_to(ROOT)), "brand": brand, "posts": listing}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
