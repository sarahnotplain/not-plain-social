"""Check a post package before anything goes to Buffer.

Usage:
    python scripts/validate_post.py posts/<slug>/post.json [--images]

Fails (exit 1) if: the quote isn't word-for-word in the post, captions break
platform limits or house rules, or (with --images) the images are missing.
"""
import pathlib, re, sys, unicodedata
from common import LAYOUTS, PHOTO_LAYOUTS, QUOTE_LAYOUTS, image_name, load_json, slide_names

LIMITS = {"instagram": 2200, "facebook": 5000, "pin_title": 100, "pin_desc": 500}
MAX_HASHTAGS = 5


def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = s.translate(str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "—": "-", "–": "-", "…": "..."}))
    return re.sub(r"\s+", " ", s).strip().lower()


def main(path, check_images=False):
    path = pathlib.Path(path)
    post = load_json(path)
    source = load_json(path.parent / "source.json", {})
    errors, warnings = [], []

    for key in ("slug", "url", "title", "layout", "alt_text", "captions"):
        if not post.get(key):
            errors.append(f"missing '{key}'")
    layout = post.get("layout")
    if layout not in LAYOUTS:
        errors.append(f"layout must be one of {LAYOUTS}")

    # Quotes must be Sarah's exact words.
    quote = post.get("quote", "")
    if layout in QUOTE_LAYOUTS:
        if not quote:
            errors.append(f"layout '{layout}' needs a quote")
        elif norm(quote) not in norm(source.get("text", "")):
            errors.append("quote is not word-for-word in the post text (source.json). Copy it exactly.")
        if layout == "print" and len(quote.split()) > 18:
            warnings.append("print layout works best under ~15 words")
        if layout in ("artline", "manuscript") and len(quote.split()) > 30:
            warnings.append(f"{layout} works best under ~30 words")
        if layout == "quote" and len(quote.split()) > 35:
            warnings.append("quote is long; it will shrink to fit but may read small")
    if layout in PHOTO_LAYOUTS and not post.get("header_image"):
        errors.append(f"{layout} layout needs header_image")


    # Instagram carousel: every slide's text is her exact words (a leading/trailing "…" marks a fragment).
    car = post.get("carousel")
    if car:
        slides = car.get("slides", [])
        kinds = [s.get("kind", "line") for s in slides]
        if not 3 <= len(slides) <= 10:
            errors.append("carousel needs 3 to 10 slides")
        if kinds[:1] != ["hook"] or kinds[-1:] != ["end"]:
            errors.append("carousel must start with a 'hook' slide and finish with an 'end' slide")
        if any(k not in ("hook", "line", "print", "end") for k in kinds):
            errors.append("carousel slide kinds are hook, line, print, end")
        text_src = norm(source.get("text", ""))
        for n, s in enumerate(slides, 1):
            t = (s.get("text") or "").strip()
            core = norm(t.strip("…").rstrip(".") if t.startswith("…") or t.endswith("…") else t)
            if not t:
                errors.append(f"carousel slide {n}: needs text")
            elif core not in text_src:
                errors.append(f"carousel slide {n}: text is not word-for-word in the post: {t[:60]!r}")
            elif t[0].isupper() and not t.startswith("…") and text_src.find(norm(t)) > 0 \
                    and text_src[text_src.find(norm(t)) - 2] not in ".?!\"":
                warnings.append(f"carousel slide {n}: starts mid-sentence; begin it with '…' and her original lowercase")
            for extra in [s.get("label", ""), s.get("eyebrow", "")] + s.get("list", []):
                if extra and norm(extra) not in text_src and norm(extra) not in norm(post.get("title", "")):
                    warnings.append(f"carousel slide {n}: label {extra!r} isn't wording from the post; keep labels to her words")
            if s.get("bg", "cream") not in ("cream", "lavender", "black"):
                errors.append(f"carousel slide {n}: bg must be cream, lavender or black")
        if car.get("panorama") and not post.get("header_image"):
            errors.append("panorama carousel needs header_image")

    caps = post.get("captions", {})
    ig, fb, pin = caps.get("instagram", ""), caps.get("facebook", ""), caps.get("pinterest", {})
    if not ig or not fb or not pin.get("title") or not pin.get("description"):
        errors.append("captions need instagram, facebook, pinterest.title and pinterest.description")
    if len(ig) > LIMITS["instagram"]: errors.append("instagram caption over 2,200 characters")
    if len(fb) > LIMITS["facebook"]: errors.append("facebook caption is too long")
    if len(pin.get("title", "")) > LIMITS["pin_title"]: errors.append("pinterest title over 100 characters")
    if len(pin.get("description", "")) > LIMITS["pin_desc"]: errors.append("pinterest description over 500 characters")
    for name, text in (("instagram", ig), ("facebook", fb)):
        if len(re.findall(r"#\w+", text)) > MAX_HASHTAGS:
            errors.append(f"{name}: more than {MAX_HASHTAGS} hashtags")
    if post.get("url") and post["url"] not in fb:
        errors.append("facebook caption must include the post link")
    if "http" in ig:
        warnings.append("instagram links aren't clickable; say 'link in bio' instead")
    if re.search(r"[\U0001F300-\U0001FAFF☀-➿]", ig + fb + pin.get("description", "")):
        errors.append("no emoji (house rule, see CLAUDE.md)")

    # House style for the caption wording itself (her quoted words are left as she wrote them).
    for name, text in (("instagram", ig), ("facebook", fb), ("pinterest", pin.get("description", ""))):
        own = text.replace(quote, "") if quote else text
        if "—" in own:
            errors.append(f"{name}: no em dashes in caption wording (use a period or comma)")
        if "!" in own:
            errors.append(f"{name}: no exclamation points")

    if check_images:
        for f in [image_name(path, "instagram"), image_name(path, "pinterest")] + slide_names(path, post):
            if not (path.parent / f).exists():
                errors.append(f"missing {f}; run render_images.py")

    for w in warnings: print("warning:", w)
    for e in errors: print("ERROR:", e)
    if errors:
        sys.exit(1)
    print("ok")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    main(args[0], "--images" in sys.argv)
