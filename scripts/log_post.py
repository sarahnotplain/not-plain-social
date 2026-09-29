"""Record a post as shared so it's never picked up again.

Usage:
    python scripts/log_post.py posts/<slug>/post.json [posts/<slug>/post-2.json ...]   # after drafts are in Buffer
    python scripts/log_post.py --skip <slug> "reason"      # mark a post as intentionally not shared
    python scripts/log_post.py --recent                    # show the last few layouts used (for rotation)

Pass every variant of one article together; they're logged as a single entry.
"""
import sys
from datetime import datetime, timezone
from common import LOG, load_json, log, save_json, variant_suffix


def main(a):
    data = log()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if a[:1] == ["--recent"]:
        for p in data["posts"][-5:]:
            layouts = ",".join(v["layout"] for v in p.get("variants", [])) or p.get("layout", "-")
            print(f"{p.get('logged_at','')[:10]}  {layouts:<18} {p['slug']}")
        return
    if a[:1] == ["--skip"] and len(a) >= 2:
        entry = {"slug": a[1], "status": "skipped", "reason": " ".join(a[2:]), "logged_at": now}
    elif a and not a[0].startswith("--"):
        posts = [(path, load_json(path)) for path in a]
        slugs = {p["slug"] for _, p in posts}
        if len(slugs) != 1:
            sys.exit(f"All files must be variants of one article, got {sorted(slugs)}")
        first = posts[0][1]
        entry = {"slug": first["slug"], "title": first["title"], "url": first["url"], "status": "drafted",
                 "variants": [{"file": f"post{variant_suffix(path)}.json", "layout": p["layout"],
                               "quote": p.get("quote", ""), "buffer": p.get("buffer", {})} for path, p in posts],
                 "logged_at": now}
    else:
        sys.exit(__doc__)
    data["posts"] = [p for p in data["posts"] if p["slug"] != entry["slug"]] + [entry]
    save_json(LOG, data)
    print(f"logged {entry['slug']} ({entry['status']})")


if __name__ == "__main__":
    main(sys.argv[1:])
