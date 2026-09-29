"""Record a post as shared so it's never picked up again.

Usage:
    python scripts/log_post.py posts/<slug>/post.json     # after drafts are in Buffer
    python scripts/log_post.py --skip <slug> "reason"      # mark a post as intentionally not shared
    python scripts/log_post.py --recent                    # show the last few layouts used (for rotation)
"""
import sys
from datetime import datetime, timezone
from common import LOG, load_json, log, save_json


def main(a):
    data = log()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if a[:1] == ["--recent"]:
        for p in data["posts"][-5:]:
            print(f"{p.get('logged_at','')[:10]}  {p.get('layout','-'):<6} {p['slug']}")
        return
    if a[:1] == ["--skip"] and len(a) >= 2:
        entry = {"slug": a[1], "status": "skipped", "reason": " ".join(a[2:]), "logged_at": now}
    elif len(a) == 1:
        post = load_json(a[0])
        entry = {"slug": post["slug"], "title": post["title"], "url": post["url"], "layout": post["layout"],
                 "status": "drafted", "buffer": post.get("buffer", {}), "logged_at": now}
    else:
        sys.exit(__doc__)
    data["posts"] = [p for p in data["posts"] if p["slug"] != entry["slug"]] + [entry]
    save_json(LOG, data)
    print(f"logged {entry['slug']} ({entry['status']})")


if __name__ == "__main__":
    main(sys.argv[1:])
