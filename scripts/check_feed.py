"""Find Substack posts that haven't been shared yet.

Usage:
    python scripts/check_feed.py              # new posts since config start_date, not yet in data/posted.json
    python scripts/check_feed.py --post URL   # (re)load one specific post, even if already shared

For each new post it writes posts/<slug>/source.json (title, subtitle, url, date,
header image, full text) and prints a JSON list of the new slugs.
"""
import argparse, email.utils, html, json, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from common import config, log, post_dir, save_json, slug_from_url

UA = {"User-Agent": "Mozilla/5.0 (not-plain-social; +https://substack.com)"}
NS = {"content": "http://purl.org/rss/1.0/modules/content/"}


def get(url, tries=4):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:      # Substack rate limit: back off and retry
                time.sleep(5 * (i + 1)); continue
            raise


class _Text(HTMLParser):
    """HTML -> plain text, one paragraph per line. Skips buttons/subscribe widgets."""
    BLOCK = {"p", "h1", "h2", "h3", "h4", "li", "blockquote", "br", "div"}
    SKIP = {"script", "style", "button", "form", "figcaption"}

    def __init__(self):
        super().__init__(); self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP: self.skip += 1
        if tag in self.BLOCK: self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip: self.skip -= 1
        if tag in self.BLOCK: self.out.append("\n")

    def handle_data(self, d):
        if not self.skip: self.out.append(d)


def to_text(body_html):
    p = _Text(); p.feed(body_html or "")
    text = html.unescape("".join(p.out))
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def from_rss(base):
    root = ET.fromstring(get(f"{base}/feed"))
    for it in root.iter("item"):
        enc = it.find("enclosure")
        yield {
            "title": (it.findtext("title") or "").strip(),
            "subtitle": (it.findtext("description") or "").strip(),
            "url": (it.findtext("link") or "").strip(),
            "published": email.utils.parsedate_to_datetime(it.findtext("pubDate")).astimezone(timezone.utc).isoformat(),
            "header_image": enc.get("url") if enc is not None and (enc.get("type") or "").startswith("image") else None,
            "text": to_text(it.findtext("content:encoded", namespaces=NS)),
        }


def from_api(base, slug):
    """Fallback for one post via Substack's (unofficial) public JSON endpoint."""
    d = json.loads(get(f"{base}/api/v1/posts/{slug}"))
    return {
        "title": d.get("title", ""), "subtitle": d.get("subtitle", "") or "",
        "url": d.get("canonical_url") or f"{base}/p/{slug}",
        "published": d.get("post_date"), "header_image": d.get("cover_image"),
        "text": to_text(d.get("body_html")),
    }


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--post")
    args = ap.parse_args()
    cfg = config()
    base = cfg["substack_url"].rstrip("/")
    shared = {p["slug"] for p in log()["posts"]}
    start = datetime.fromisoformat(cfg.get("start_date", "2000-01-01")).replace(tzinfo=timezone.utc)

    if args.post:
        slug = slug_from_url(args.post)
        items = [i for i in from_rss(base) if slug_from_url(i["url"]) == slug] or [from_api(base, slug)]
    else:
        items = [i for i in from_rss(base)
                 if slug_from_url(i["url"]) not in shared
                 and datetime.fromisoformat(i["published"]) >= start]

    new = []
    for item in sorted(items, key=lambda i: i["published"] or ""):
        slug = slug_from_url(item["url"])
        item["slug"] = slug
        item["word_count"] = len(item["text"].split())
        # Substack falls back to the publication logo when a post has no cover photo; that isn't a post photo.
        if cfg.get("logo_image_id") and cfg["logo_image_id"] in (item.get("header_image") or ""):
            item["header_image"] = None
        item["looks_paywalled"] = item["word_count"] < 150   # RSS only carries a preview of paid posts
        save_json(post_dir(slug) / "source.json", item)
        new.append({"slug": slug, "title": item["title"], "published": item["published"],
                    "has_header_image": bool(item["header_image"]), "looks_paywalled": item["looks_paywalled"]})

    print(json.dumps(new, indent=2, ensure_ascii=False))
    if not new:
        print("No new posts.", file=sys.stderr)


if __name__ == "__main__":
    main()
