"""Find Substack Notes that haven't been shared or skipped yet.

Usage:
    python scripts/check_notes.py

Reads Sarah's public Notes feed and keeps her own original notes (not replies or restacks),
published since config notes.start_date and within notes.lookback_days, that aren't
in data/posted.json. For each it writes posts/note-<id>/source.json and prints a JSON list.

Choosing which note (at most notes.per_day) becomes a draft is a judgment call made
by Claude in the share-new-posts workflow; the rest are logged as skipped.
"""
import json, sys
from datetime import datetime, timedelta, timezone
from check_feed import get
from common import config, log, post_dir, save_json


def main():
    cfg = config()
    n = cfg["notes"]
    handled = {p["slug"] for p in log()["posts"]}
    now = datetime.now(timezone.utc)
    since = max(datetime.fromisoformat(n["start_date"]).replace(tzinfo=timezone.utc),
                now - timedelta(days=n.get("lookback_days", 14)))

    feed = json.loads(get(f"https://substack.com/api/v1/reader/feed/profile/{n['user_id']}?types%5B%5D=note"))
    found = []
    for item in feed.get("items", []):
        c = item.get("comment") or {}
        if item.get("context", {}).get("type") != "note" or c.get("user_id") != n["user_id"]:
            continue                                  # restacks, other people's notes
        if c.get("ancestor_path"):
            continue                                  # replies
        published = datetime.fromisoformat(c["date"].replace("Z", "+00:00"))
        slug = f"note-{c['id']}"
        if published < since or slug in handled or not (c.get("body") or "").strip():
            continue
        source = {"kind": "note", "slug": slug, "id": c["id"], "published": c["date"],
                  "url": f"https://substack.com/@{n['handle']}/note/c-{c['id']}",
                  "text": c["body"].strip(), "word_count": len(c["body"].split())}
        # A note that shares one of her essays should link to that essay.
        shared = [a["post"] for a in c.get("attachments") or [] if a.get("type") == "post" and a.get("post")]
        if shared:
            source["shares_post"] = {"title": shared[0].get("title"), "url": shared[0].get("canonical_url")}
        save_json(post_dir(slug) / "source.json", source)
        found.append({k: source[k] for k in ("slug", "published", "word_count", "text", "shares_post") if k in source})

    found.sort(key=lambda s: s["published"])
    print(json.dumps(found, indent=2, ensure_ascii=False))
    if not found:
        print("No new notes.", file=sys.stderr)


if __name__ == "__main__":
    main()
